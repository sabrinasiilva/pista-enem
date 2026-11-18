"""Monta data/questoes.json e as matrizes (data/matriz_<area>.json) a partir das fontes em data/brutos/.

Uso: python data/extrair.py

Para cada questão de Matemática e de Ciências da Natureza de 2022 a 2024:
- o texto vem do conjunto da Maritaca;
- o gabarito, a habilidade e a dificuldade (TRI) vêm dos microdados do Inep;
- enunciado e alternativas são comparados com o PDF oficial do caderno.

O texto da Maritaca vem em parte da versão para leitor de tela (fórmulas por extenso,
números romanos trocados por algarismos). Por isso as questões do MVP são transcritas
de novo a partir da prova oficial (data/anotacoes/revisao/) e montadas em selecionar.py.

Para 2025 (Matemática), não há conjunto aberto: o texto bruto vem do PDF do caderno azul, só
como referência, e a revisão transcreve tudo a partir da imagem da página oficial.
"""

from __future__ import annotations

import csv
import difflib
import json
import re
import unicodedata
from collections import defaultdict

import fontes

LETRAS = "ABCDE"
LIMITE_ENUNCIADO = 0.90
LIMITE_ALTERNATIVA = 0.80
CORES_ADAPTADAS = {"LARANJA", "LEITOR TELA"}
MAXIMO_DE_DIFERENCAS = 3
NOMES_CORES = {"CINZA": "cinza", "ROSA": "rosa", "VERDE": "verde", "AZUL": "azul"}



# ---------------------------------------------------------------- texto

def normalizar(texto: str) -> str:
    """Deixa só letras e números minúsculos, sem acento, para comparar textos."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def similaridade(a: str, b: str) -> float:
    a, b = normalizar(a), normalizar(b)
    if not a and not b:
        return 1.0
    return round(difflib.SequenceMatcher(None, a, b, autojunk=False).ratio(), 3)


# ---------------------------------------------------------------- Maritaca

def ler_maritaca(caminho, area: str = "matematica") -> dict[int, dict]:
    questoes = {}
    with open(caminho, encoding="utf-8") as arquivo:
        for linha in arquivo:
            registro = json.loads(linha)
            numero = int(registro["id"].split("_")[1])
            if fontes.AREAS[area]["primeira"] <= numero <= fontes.AREAS[area]["ultima"]:
                questoes[numero] = registro
    return questoes


# ---------------------------------------------------------------- microdados

def ler_itens(caminho, sigla: str = "MT") -> list[dict]:
    with open(caminho, encoding="latin-1", newline="") as arquivo:
        return [linha for linha in csv.DictReader(arquivo, delimiter=";") if linha["SG_AREA"] == sigla]


def itens_da_prova(itens: list[dict], prova: str) -> dict[int, list[dict]]:
    """Itens de uma prova já identificada (usado em 2025, sem o conjunto da Maritaca)."""
    return {int(i["CO_POSICAO"]): [i] for i in itens if i["CO_PROVA"] == prova}


def itens_por_posicao(itens: list[dict], gabaritos: dict[int, str]) -> dict[int, list[dict]]:
    """Agrupa por posição os itens dos cadernos regulares que seguem a mesma ordem do conjunto.

    Usa os cadernos regulares cujo gabarito mais bate com o do conjunto. Até MAXIMO_DE_DIFERENCAS
    posições podem divergir: são as em que o conjunto traz a questão substituta do caderno
    adaptado, com outro gabarito. Essas posições saem depois, na conferência do gabarito.
    """
    por_prova = defaultdict(list)
    for item in itens:
        por_prova[item["CO_PROVA"]].append(item)

    validas = {numero: letra for numero, letra in gabaritos.items() if letra in LETRAS}
    regulares = {}
    for codigo, prova in por_prova.items():
        if prova[0]["TX_COR"] in CORES_ADAPTADAS or any(i["IN_ITEM_ADAPTADO"] == "1" for i in prova):
            continue
        posicoes = {int(i["CO_POSICAO"]): i for i in prova}
        acertos = sum(posicoes.get(n, {}).get("TX_GABARITO") == letra for n, letra in validas.items())
        regulares[codigo] = (acertos, posicoes)

    resultado = defaultdict(list)
    if not regulares:
        return resultado
    melhor = max(acertos for acertos, _ in regulares.values())
    if melhor < len(validas) - MAXIMO_DE_DIFERENCAS:
        return resultado
    for acertos, posicoes in regulares.values():
        if acertos == melhor:
            for numero, item in posicoes.items():
                resultado[numero].append(item)
    return resultado


def dados_oficiais(itens: list[dict]) -> dict:
    """Resume os itens de uma posição. Se os cadernos regulares divergirem, marca conflito."""
    chaves = {(i["CO_ITEM"], i["CO_HABILIDADE"], i["TX_GABARITO"]) for i in itens}
    item = itens[0]
    parametro_b = item["NU_PARAM_B"].strip()
    # IN_ITEM_ABAN marca itens fora do cálculo da nota. Só os com gabarito "X" foram anulados;
    # os outros saíram da calibração da TRI por motivo estatístico ("Convergência", "Bis<0,01")
    # e continuam com gabarito válido.
    abandonado = item["IN_ITEM_ABAN"] == "1"
    anulada = item["TX_GABARITO"] == "X"
    habilidade = int(item["CO_HABILIDADE"]) if item["CO_HABILIDADE"].strip() else None
    return {
        "item_inep": item["CO_ITEM"],
        "gabarito": None if anulada else item["TX_GABARITO"],
        "habilidade": habilidade,
        "dificuldade_tri": float(parametro_b) if parametro_b else None,
        "anulada": anulada,
        "fora_da_tri": abandonado and not anulada,
        "motivo_abandono": item["TX_MOTIVO_ABAN"].strip() or None,
        "conflito_entre_cadernos": len(chaves) > 1,
    }


# ---------------------------------------------------------------- PDF

MARCA_DAGUA = re.compile(r"(ENEM\s*20\d\d\s*){3,}")
CABECALHO = re.compile(
    r"•|^\*\w+\*$|^Questões de \d+ a \d+$|^MATEMÁTICA E SUAS TECNOLOGIAS$"
    r"|^[A-Z]{2} - \d° dia \| Caderno"  # rodapé de 2022: "MT - 2° dia | Caderno 6 - CINZA - 1ª Aplicação"
    r"|\| CADERNO \d+ \|"  # cabeçalho de 2025: "MATEMÁTICA E SUAS TECNOLOGIAS | 2º DIA | CADERNO 7 | AZUL"
)


def limpar_pagina(texto: str) -> str:
    linhas = [l for l in texto.splitlines() if not MARCA_DAGUA.search(l) and not CABECALHO.search(l.strip())]
    return "\n".join(linhas)


def texto_da_prova(caminho) -> str:
    import pymupdf

    with pymupdf.open(caminho) as documento:
        return "\n".join(limpar_pagina(pagina.get_text()) for pagina in documento)


def blocos_por_questao(texto: str) -> dict[int, str]:
    # até 2024 o PDF escreve "QUESTÃO 141"; em 2025, "Questão 141"
    marcas = list(re.finditer(r"QUESTÃO\s*(\d{1,3})\b", texto, re.IGNORECASE))
    blocos = {}
    for indice, marca in enumerate(marcas):
        fim = marcas[indice + 1].start() if indice + 1 < len(marcas) else len(texto)
        blocos[int(marca.group(1))] = texto[marca.end():fim]
    return blocos


def separar_alternativas(bloco: str) -> tuple[str, list[str]] | None:
    """Separa enunciado e alternativas de um bloco de questão extraído do PDF.

    Procura, de trás para frente, linhas que começam com A, B, C, D e E, nessa ordem.
    Cobre os dois formatos usados pelo Inep: "A\\t\\nA\\t texto" e "A texto".
    """
    linhas = bloco.splitlines()
    # a letra pode vir sozinha na linha quando a alternativa é uma fórmula
    marcador = re.compile(r"^([A-E])(?:[\t ]+(.*))?$")
    inicio = {}
    procurando = 4
    for indice in range(len(linhas) - 1, -1, -1):
        achado = marcador.match(linhas[indice])
        if achado and achado.group(1) == LETRAS[procurando]:
            # o formato antigo repete a letra: a linha de cima é o "círculo" vazio
            inicio[procurando] = indice
            procurando -= 1
            if procurando < 0:
                break
    if procurando >= 0:
        return None

    # descarta a linha do "círculo" vazio, quando existe
    def eh_circulo(indice: int, letra: str) -> bool:
        return indice >= 0 and linhas[indice].strip() == letra

    primeira = inicio[0]
    if eh_circulo(primeira - 1, "A"):
        primeira -= 1
    enunciado = "\n".join(linhas[:primeira]).strip()

    alternativas = []
    for posicao in range(5):
        comeco = inicio[posicao]
        fim = inicio[posicao + 1] if posicao < 4 else len(linhas)
        if posicao < 4 and eh_circulo(fim - 1, LETRAS[posicao + 1]):
            fim -= 1
        trecho = [marcador.match(linhas[comeco]).group(2) or ""] + linhas[comeco + 1:fim]
        if posicao == 4:
            # números soltos no fim da página são rodapé (número da página, códigos)
            while len(trecho) > 1 and re.fullmatch(r"\s*\d{0,2}\s*", trecho[-1]):
                trecho.pop()
        alternativas.append(" ".join(t.strip() for t in trecho if t.strip()))
    return enunciado, alternativas


# ---------------------------------------------------------------- matriz

def extrair_matriz(texto: str, area: str = "matematica") -> dict:
    """Extrai competências e habilidades de uma área da matriz de referência do Enem.

    A competência de cada habilidade é a do bloco "Competência de área N" em que ela aparece.
    """
    inicio = texto.find(fontes.AREAS[area]["marca_na_matriz"])
    inicio = texto.rfind("Competência de área 1", 0, inicio)
    fim = texto.find("Competência de área 1", inicio + 10)
    trecho = texto[inicio:fim]
    ruido = r"^(MATRIZES DE REFERÊNCIA|ENEM|VOLTAR PARA|O SUMÁRIO|\d+|MATEMÁTICA E SUAS|CIÊNCIAS DA NATUREZA E SUAS|TECNOLOGIAS)\s*$"
    trecho = "\n".join(l for l in trecho.splitlines() if l.strip() and not re.match(ruido, l.strip()))
    # "H28 –" às vezes sai quebrado no PDF como "H\n28 –"
    trecho = re.sub(r"\nH\n(\d+\s*–)", r"\nH\1", trecho)

    def limpar(t: str) -> str:
        return re.sub(r"\s+", " ", t).strip()

    competencias = []
    for achado in re.finditer(r"Competência de área (\d)\n(.+?)(?=\nH\d+\s*–)", trecho, re.S):
        competencias.append({"codigo": f"C{achado.group(1)}", "descricao": limpar(achado.group(2))})

    habilidades = []
    blocos = re.split(r"\nCompetência de área (\d)\n", "\n" + trecho)
    for numero_da_competencia, bloco in zip(blocos[1::2], blocos[2::2]):
        for achado in re.finditer(r"H(\d+)\s*–\s*(.+?)(?=\nH\d+\s*–|\Z)", bloco, re.S):
            habilidades.append({
                "codigo": f"H{int(achado.group(1))}",
                "competencia": f"C{numero_da_competencia}",
                "descricao": limpar(achado.group(2)),
            })
    return {"area": area, "fonte": fontes.MATRIZ_URL, "competencias": competencias, "habilidades": habilidades}


# ---------------------------------------------------------------- montagem

def montar_questao(
    ano: int, numero: int, registro: dict, oficial: dict, bloco_pdf: str | None, area: str, competencias: dict[str, str]
) -> dict:
    """`registro` é a questão do conjunto da Maritaca, ou None em 2025 (texto bruto do PDF)."""
    caderno = fontes.CADERNOS[ano]
    separado = separar_alternativas(bloco_pdf) if bloco_pdf else None
    if registro is None:
        texto_pdf, alternativas_pdf = separado if separado else ("", [""] * 5)
        registro = {"question": texto_pdf, "alternatives": alternativas_pdf, "IU": None, "figures": None,
                    "label": oficial["gabarito"] or "Anulado"}
    enunciado = registro["question"].strip()
    alternativas = [{"letra": letra, "texto": texto.strip()} for letra, texto in zip(LETRAS, registro["alternatives"])]

    if separado:
        enunciado_pdf, alternativas_pdf = separado
        sim_enunciado = similaridade(enunciado, enunciado_pdf)
        sim_alternativas = [similaridade(a["texto"], b) for a, b in zip(alternativas, alternativas_pdf)]
    else:
        sim_enunciado, sim_alternativas = None, None

    habilidade = oficial["habilidade"]
    return {
        "id": f"{ano}-{numero}",
        "ano": ano,
        "numero": numero,
        "area": area,
        "enunciado": enunciado,
        "alternativas": alternativas,
        "gabarito": oficial["gabarito"],
        "anulada": oficial["anulada"],
        # em 2025 não se sabe pelo texto: quem decide é a revisão, olhando a página
        "tem_imagem": None if registro["IU"] is None else bool(registro["IU"] or registro["figures"]),
        "habilidade": f"H{habilidade}" if habilidade else None,
        "competencia": competencias.get(f"H{habilidade}") if habilidade else None,
        "dificuldade_tri": oficial["dificuldade_tri"],
        "fonte": {
            "orgao": "Inep",
            "prova": f"ENEM {ano}, 2º dia, caderno {caderno['codigo']} ({NOMES_CORES[caderno['cor']]}), questão {numero}",
            "url": fontes.url_prova(ano),
            "item_inep": oficial["item_inep"],
        },
        "conferencia": {
            "gabarito_confere_com_microdados": registro["label"] == (oficial["gabarito"] or "Anulado"),
            "item_igual_nos_cadernos_regulares": not oficial["conflito_entre_cadernos"],
            "similaridade_enunciado_pdf": sim_enunciado,
            "similaridade_alternativas_pdf": sim_alternativas,
            "fora_da_tri": oficial["fora_da_tri"],
            "motivo_abandono": oficial["motivo_abandono"],
        },
    }


def precisa_revisao(questao: dict) -> list[str]:
    """Motivos para uma questão ser revisada à mão antes de entrar no MVP."""
    conferencia = questao["conferencia"]
    motivos = []
    if not conferencia["gabarito_confere_com_microdados"]:
        motivos.append("gabarito diferente dos microdados")
    if not conferencia["item_igual_nos_cadernos_regulares"]:
        motivos.append("item diferente entre cadernos")
    if conferencia["similaridade_enunciado_pdf"] is None:
        motivos.append("questão não encontrada no PDF")
    else:
        if conferencia["similaridade_enunciado_pdf"] < LIMITE_ENUNCIADO:
            motivos.append(f"enunciado {conferencia['similaridade_enunciado_pdf']:.2f} parecido com o PDF")
        for letra, valor in zip(LETRAS, conferencia["similaridade_alternativas_pdf"]):
            if valor < LIMITE_ALTERNATIVA:
                motivos.append(f"alternativa {letra} {valor:.2f} parecida com o PDF")
    return motivos


def main() -> None:
    import pymupdf

    with pymupdf.open(fontes.caminho_matriz()) as documento:
        texto_da_matriz = "\n".join(p.get_text() for p in documento)
    matrizes = {area: extrair_matriz(texto_da_matriz, area) for area in fontes.AREAS}
    for area, matriz in matrizes.items():
        assert len(matriz["habilidades"]) == 30, f"matriz de {area} incompleta"
        salvar(fontes.PASTA_DADOS / f"matriz_{area}.json", matriz)
    competencias = {area: {h["codigo"]: h["competencia"] for h in m["habilidades"]} for area, m in matrizes.items()}

    questoes = {}
    for ano in fontes.TODOS_OS_ANOS:
        blocos = blocos_por_questao(texto_da_prova(fontes.caminho_prova(ano)))
        for area, configuracao in fontes.AREAS.items():
            itens = ler_itens(fontes.caminho_itens(ano), configuracao["sigla"])
            if ano in fontes.ANOS:
                registros = ler_maritaca(fontes.caminho_maritaca(ano), area)
                oficiais = itens_por_posicao(itens, {n: r["label"] for n, r in registros.items()})
            elif area == "matematica":
                oficiais = itens_da_prova(itens, fontes.CADERNOS[ano]["prova"])
                registros = dict.fromkeys(range(configuracao["primeira"], configuracao["ultima"] + 1))
            else:
                continue  # 2025: por enquanto, só Matemática
            for numero, registro in sorted(registros.items()):
                questao = montar_questao(
                    ano, numero, registro, dados_oficiais(oficiais[numero]), blocos.get(numero), area, competencias[area]
                )
                questoes[questao["id"]] = questao

    for questao in questoes.values():
        questao["conferencia"]["pendencias"] = precisa_revisao(questao)
    salvar(fontes.PASTA_DADOS / "questoes.json", list(questoes.values()))

    for area in fontes.AREAS:
        da_area = [q for q in questoes.values() if q["area"] == area]
        validas = [q for q in da_area if q["tem_imagem"] is not True and not q["anulada"]]
        print(f"{area}: {len(da_area)} questões, {len(validas)} sem imagem conhecida e não anuladas")


def salvar(caminho, dados) -> None:
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"salvo: {caminho.name}")


if __name__ == "__main__":
    main()
