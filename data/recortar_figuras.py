"""Recorta as figuras de questões da prova oficial (PDF do Inep).

Uso: python data/recortar_figuras.py 2022-136 2022-137 ...

Para cada questão, acha o cabeçalho "QUESTÃO N", pega o trecho da coluna até a próxima questão
(seguindo para a próxima coluna ou página, se a questão continuar) e junta as imagens e os
desenhos vetoriais desse trecho em grupos. Cada grupo vira data/imagens/<id>-<n>.png.
O recorte é conferido por uma pessoa antes de entrar no banco (ver anotacoes/revisao/).
"""

from __future__ import annotations

import re
import sys

import fontes
import pymupdf

PASTA = fontes.PASTA_DADOS / "imagens"
RESOLUCAO = 200
MARGEM = 6  # pontos em volta do recorte
DISTANCIA_PARA_JUNTAR = 18  # caixas mais próximas que isso são a mesma figura
AREA_MINIMA = 2500  # pontos²: abaixo disso é enfeite (traço, marcador)
LADO_MINIMO = 40  # pontos: recorte mais fino que isso é borda da página
RODAPE = 40  # pontos no fim da página com número e código da prova
CABECALHO = 60  # pontos no começo da página com o nome da prova

CABECALHO_DA_QUESTAO = re.compile(r"QUESTÃO\s*(\d{2,3})\b", re.IGNORECASE)


def cabecalhos(pagina: pymupdf.Page) -> list[tuple[int, pymupdf.Rect]]:
    achados = []
    for bloco in pagina.get_text("dict")["blocks"]:
        for linha in bloco.get("lines", []):
            texto = "".join(span["text"] for span in linha["spans"])
            achado = CABECALHO_DA_QUESTAO.search(texto)
            if achado:
                achados.append((int(achado.group(1)), pymupdf.Rect(linha["bbox"])))
    return achados


def coluna(pagina: pymupdf.Page, retangulo: pymupdf.Rect) -> pymupdf.Rect:
    meio = pagina.rect.width / 2
    x0, x1 = (0, meio) if retangulo.x0 < meio else (meio, pagina.rect.width)
    return pymupdf.Rect(x0, CABECALHO, x1, pagina.rect.height - RODAPE)


def trechos_da_questao(documento: pymupdf.Document, numero: int) -> list[tuple[int, pymupdf.Rect]]:
    """Retângulos (página, área) ocupados pela questão, na ordem de leitura."""
    ordem = []  # (página, coluna 0/1)
    for indice, pagina in enumerate(documento):
        for lado in (0, 1):
            ordem.append((indice, lado))
    inicio = None
    for indice, pagina in enumerate(documento):
        for n, retangulo in cabecalhos(pagina):
            if n == numero:
                lado = 0 if retangulo.x0 < pagina.rect.width / 2 else 1
                inicio = (indice, lado, retangulo.y1)
    if inicio is None:
        raise LookupError(f"questão {numero} não encontrada")
    trechos = []
    posicao = ordem.index((inicio[0], inicio[1]))
    topo = inicio[2]
    for indice, lado in ordem[posicao : posicao + 3]:  # no máximo a coluna seguinte e mais uma
        pagina = documento[indice]
        area = coluna(pagina, pymupdf.Rect(0 if lado == 0 else pagina.rect.width, 0, 0, 0))
        area.y0 = max(area.y0, topo)
        proximos = [r.y0 for n, r in cabecalhos(pagina) if n != numero and area.x0 <= r.x0 < area.x1 and r.y0 > area.y0]
        if proximos:
            area.y1 = min(proximos)
            trechos.append((indice, area))
            break
        trechos.append((indice, area))
        topo = 0
    return trechos


def caixas(pagina: pymupdf.Page, area: pymupdf.Rect) -> list[pymupdf.Rect]:
    resultado = []
    for bloco in pagina.get_text("dict")["blocks"]:
        r = pymupdf.Rect(bloco["bbox"])
        # imagem estreita e alta é a faixa de segurança entre as colunas
        if bloco["type"] == 1 and not (r.width < 15 and r.height > 100):
            resultado.append(r)
    for desenho in pagina.get_drawings():
        r = desenho["rect"]
        largura_da_coluna = area.width
        if r.width < 15 and r.height > 0.5 * area.height:  # linha ou faixa vertical entre as colunas
            continue
        if r.width < 3 and r.height < 3:
            continue
        if r.height < 2 and r.width > 0.9 * largura_da_coluna:  # linha que separa questões
            continue
        resultado.append(pymupdf.Rect(r))
    return [r & area for r in resultado if r.intersects(area)]


def agrupar(retangulos: list[pymupdf.Rect]) -> list[pymupdf.Rect]:
    grupos: list[pymupdf.Rect] = []
    for r in sorted(retangulos, key=lambda r: r.y0):
        perto = pymupdf.Rect(r.x0 - DISTANCIA_PARA_JUNTAR, r.y0 - DISTANCIA_PARA_JUNTAR,
                             r.x1 + DISTANCIA_PARA_JUNTAR, r.y1 + DISTANCIA_PARA_JUNTAR)
        for i, g in enumerate(grupos):
            if g.intersects(perto):
                grupos[i] = g | r
                break
        else:
            grupos.append(pymupdf.Rect(r))
    # junções podem aproximar grupos que antes estavam separados
    mudou = True
    while mudou:
        mudou = False
        for i in range(len(grupos)):
            for j in range(i + 1, len(grupos)):
                a, b = grupos[i], grupos[j]
                perto = pymupdf.Rect(a.x0 - DISTANCIA_PARA_JUNTAR, a.y0 - DISTANCIA_PARA_JUNTAR,
                                     a.x1 + DISTANCIA_PARA_JUNTAR, a.y1 + DISTANCIA_PARA_JUNTAR)
                if perto.intersects(b):
                    grupos[i] = a | b
                    del grupos[j]
                    mudou = True
                    break
            if mudou:
                break
    return [g for g in grupos if g.width * g.height >= AREA_MINIMA]


def linhas_de_texto(pagina: pymupdf.Page, area: pymupdf.Rect) -> list[tuple[pymupdf.Rect, bool]]:
    """Cada linha de texto da área e se ela é texto corrido (enunciado, alternativas).
    Rótulos de gráfico, títulos curtos e a linha da fonte (letra pequena) não são texto corrido.
    É por linha, e não por bloco, porque o PDF às vezes junta um rótulo ao parágrafo vizinho."""
    brutas = []
    for bloco in pagina.get_text("dict")["blocks"]:
        for linha in bloco.get("lines", []):
            r = pymupdf.Rect(linha["bbox"])
            # texto girado é a faixa de segurança impressa entre as colunas, não parte da figura
            if not r.intersects(area) or abs(linha["dir"][1]) > 0.5:
                continue
            texto = "".join(s["text"] for s in linha["spans"]).strip()
            tamanho = max((s["size"] for s in linha["spans"]), default=0)
            brutas.append((r, len(texto) >= 40 and tamanho >= 8.5, tamanho))
    # na ordem em que se lê: o PDF nem sempre guarda as linhas assim
    brutas.sort(key=lambda linha: (round(linha[0].y0), linha[0].x0))
    margem_direita = max((r.x1 for r, corrido, _ in brutas if corrido), default=area.x1)
    resultado: list[tuple[pymupdf.Rect, bool, float]] = []
    for r, corrido, tamanho in brutas:
        # a última linha curta de um parágrafo ("mostra o gráfico.") continua sendo texto corrido:
        # logo abaixo de uma linha cheia (que vai até a margem direita), na mesma margem e com a
        # mesma letra. Um rótulo logo depois do fim de um parágrafo não é continuação.
        continua = any(
            c and a.x1 >= margem_direita - 3 and -4 <= r.y0 - a.y1 < 6
            and abs(r.x0 - a.x0) < 3 and abs(tamanho - t) < 0.3
            for a, c, t in resultado
        )
        resultado.append((r, corrido or continua, tamanho))
    return [(r, corrido) for r, corrido, _ in resultado]


def faixa_da_figura(pagina: pymupdf.Page, area: pymupdf.Rect, grupo: pymupdf.Rect) -> pymupdf.Rect:
    """Do fim do texto de cima ao começo do texto de baixo: assim entram o título, os rótulos e a fonte."""
    linhas = linhas_de_texto(pagina, area)
    corridas = [r for r, corrido in linhas if corrido]
    cima = max((r.y1 for r in corridas if r.y1 <= grupo.y0 + 2), default=area.y0)
    baixo = min((r.y0 for r in corridas if r.y0 >= grupo.y1 - 2), default=area.y1)
    faixa = pymupdf.Rect(area.x0, cima, area.x1, baixo)
    conteudo = pymupdf.Rect(grupo)
    for r, corrido in linhas:
        if not corrido and r.intersects(faixa):
            conteudo |= r & faixa
    # nada acima do fim do texto de cima nem abaixo do começo do texto de baixo (as pontas das letras)
    conteudo.y0 = max(conteudo.y0, cima + 2)
    conteudo.y1 = min(conteudo.y1, baixo - 1)
    return conteudo


def recortar(id_questao: str) -> list[str]:
    ano, numero = id_questao.split("-")
    PASTA.mkdir(exist_ok=True)
    salvos = []
    with pymupdf.open(fontes.caminho_prova(int(ano))) as documento:
        for pagina_indice, area in trechos_da_questao(documento, int(numero)):
            pagina = documento[pagina_indice]
            recortes: list[pymupdf.Rect] = []
            for grupo in agrupar(caixas(pagina, area)):
                faixa = faixa_da_figura(pagina, area, grupo)
                if min(faixa.width, faixa.height) < LADO_MINIMO:
                    continue  # traço na borda da página, não figura
                # partes da mesma figura (as três grades de um quadro) caem na mesma faixa
                iguais = [r for r in recortes if r.intersects(faixa)]
                for r in iguais:
                    recortes.remove(r)
                    faixa |= r
                recortes.append(faixa)
            for grupo in sorted(recortes, key=lambda r: r.y0):
                # margem só dos lados: em cima e embaixo já começa o texto do enunciado
                # sem passar da coluna: na divisa fica a faixa de segurança da prova
                recorte = (grupo + (-MARGEM, 0, MARGEM, 0)) & (area + (2, -500, -4, 500)) & pagina.rect
                destino = PASTA / f"{id_questao}-{len(salvos) + 1}.png"
                pagina.get_pixmap(dpi=RESOLUCAO, clip=recorte).save(destino)
                salvos.append(destino.name)
    return salvos


def main() -> None:
    for id_questao in sys.argv[1:]:
        print(id_questao, recortar(id_questao))


if __name__ == "__main__":
    main()
