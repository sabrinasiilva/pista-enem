"""Monta data/questoes.json e data/matriz_matematica.json a partir das fontes em data/brutos/.

Uso: python data/extrair.py

Para cada questão de Matemática de 2022 a 2024:
- o texto vem do conjunto da Maritaca;
- o gabarito, a habilidade e a dificuldade (TRI) vêm dos microdados do Inep;
- enunciado e alternativas são comparados com o PDF oficial do caderno.

O texto da Maritaca vem em parte da versão para leitor de tela (fórmulas por extenso,
números romanos trocados por algarismos). Por isso as questões do MVP são transcritas
de novo a partir da prova oficial (data/anotacoes/revisao/) e montadas em selecionar.py.
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
NOMES_CORES = {"CINZA": "cinza", "ROSA": "rosa", "VERDE": "verde"}

COMPETENCIAS_POR_HABILIDADE = {
    **{h: 1 for h in range(1, 6)},
    **{h: 2 for h in range(6, 10)},
    **{h: 3 for h in range(10, 15)},
    **{h: 4 for h in range(15, 19)},
    **{h: 5 for h in range(19, 24)},
    **{h: 6 for h in range(24, 27)},
    **{h: 7 for h in range(27, 31)},
}


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

def ler_maritaca(caminho) -> dict[int, dict]:
    questoes = {}
    with open(caminho, encoding="utf-8") as arquivo:
        for linha in arquivo:
            registro = json.loads(linha)
            numero = int(registro["id"].split("_")[1])
            if fontes.PRIMEIRA_QUESTAO_MATEMATICA <= numero <= fontes.ULTIMA_QUESTAO_MATEMATICA:
                questoes[numero] = registro
    return questoes


# ---------------------------------------------------------------- microdados

def ler_itens(caminho) -> list[dict]:
    with open(caminho, encoding="latin-1", newline="") as arquivo:
        return [linha for linha in csv.DictReader(arquivo, delimiter=";") if linha["SG_AREA"] == "MT"]


def itens_por_posicao(itens: list[dict], gabaritos: dict[int, str]) -> dict[int, list[dict]]:
    """Agrupa por posição os itens dos cadernos regulares que seguem a mesma ordem do conjunto.

    Um caderno segue a mesma ordem quando o gabarito bate em todas as questões não anuladas.
    """
    por_prova = defaultdict(list)
    for item in itens:
        por_prova[item["CO_PROVA"]].append(item)

    validas = {numero: letra for numero, letra in gabaritos.items() if letra in LETRAS}
    resultado = defaultdict(list)
    for prova in por_prova.values():
        if prova[0]["TX_COR"] in CORES_ADAPTADAS or any(i["IN_ITEM_ADAPTADO"] == "1" for i in prova):
            continue
        posicoes = {int(i["CO_POSICAO"]): i for i in prova}
        if all(posicoes.get(n, {}).get("TX_GABARITO") == letra for n, letra in validas.items()):
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
)


def limpar_pagina(texto: str) -> str:
    linhas = [l for l in texto.splitlines() if not MARCA_DAGUA.search(l) and not CABECALHO.search(l.strip())]
    return "\n".join(linhas)


def texto_da_prova(caminho) -> str:
    import pymupdf

    with pymupdf.open(caminho) as documento:
        return "\n".join(limpar_pagina(pagina.get_text()) for pagina in documento)


def blocos_por_questao(texto: str) -> dict[int, str]:
    marcas = list(re.finditer(r"QUESTÃO\s*(\d{1,3})\b", texto))
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

def extrair_matriz(texto: str) -> dict:
    """Extrai competências e habilidades de Matemática da matriz de referência do Enem."""
    inicio = texto.find("Construir significados para os números")
    inicio = texto.rfind("Competência de área 1", 0, inicio)
    fim = texto.find("Competência de área 1", inicio + 10)
    trecho = texto[inicio:fim]
    trecho = "\n".join(l for l in trecho.splitlines()
                       if l.strip() and not re.match(r"^(MATRIZES DE REFERÊNCIA|ENEM|VOLTAR PARA|O SUMÁRIO|\d+|MATEMÁTICA E SUAS|TECNOLOGIAS)\s*$", l.strip()))

    def limpar(t: str) -> str:
        return re.sub(r"\s+", " ", t).strip()

    competencias = []
    for achado in re.finditer(r"Competência de área (\d)\n(.+?)(?=\nH\d+\s*–)", trecho, re.S):
        competencias.append({"codigo": f"C{achado.group(1)}", "descricao": limpar(achado.group(2))})

    habilidades = []
    for achado in re.finditer(r"H(\d+)\s*–\s*(.+?)(?=\nH\d+\s*–|\nCompetência de área|\Z)", trecho, re.S):
        numero = int(achado.group(1))
        habilidades.append({
            "codigo": f"H{numero}",
            "competencia": f"C{COMPETENCIAS_POR_HABILIDADE[numero]}",
            "descricao": limpar(achado.group(2)),
        })
    return {"area": "matematica", "fonte": fontes.MATRIZ_URL,
            "competencias": competencias, "habilidades": habilidades}


# ---------------------------------------------------------------- montagem

def montar_questao(ano: int, numero: int, registro: dict, oficial: dict, bloco_pdf: str | None) -> dict:
    caderno = fontes.CADERNOS[ano]
    enunciado = registro["question"].strip()
    alternativas = [{"letra": letra, "texto": texto.strip()} for letra, texto in zip(LETRAS, registro["alternatives"])]

    separado = separar_alternativas(bloco_pdf) if bloco_pdf else None
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
        "area": "matematica",
        "enunciado": enunciado,
        "alternativas": alternativas,
        "gabarito": oficial["gabarito"],
        "anulada": oficial["anulada"],
        "tem_imagem": bool(registro["IU"] or registro["figures"]),
        "habilidade": f"H{habilidade}" if habilidade else None,
        "competencia": f"C{COMPETENCIAS_POR_HABILIDADE[habilidade]}" if habilidade else None,
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
        matriz = extrair_matriz("\n".join(p.get_text() for p in documento))
    assert len(matriz["habilidades"]) == 30 and len(matriz["competencias"]) == 7, "matriz incompleta"

    questoes = {}
    for ano in fontes.ANOS:
        registros = ler_maritaca(fontes.caminho_maritaca(ano))
        gabaritos = {n: r["label"] for n, r in registros.items()}
        oficiais = itens_por_posicao(ler_itens(fontes.caminho_itens(ano)), gabaritos)
        blocos = blocos_por_questao(texto_da_prova(fontes.caminho_prova(ano)))
        for numero, registro in sorted(registros.items()):
            questao = montar_questao(ano, numero, registro, dados_oficiais(oficiais[numero]), blocos.get(numero))
            questoes[questao["id"]] = questao

    for questao in questoes.values():
        questao["conferencia"]["pendencias"] = precisa_revisao(questao)

    salvar(fontes.PASTA_DADOS / "matriz_matematica.json", matriz)
    salvar(fontes.PASTA_DADOS / "questoes.json", list(questoes.values()))

    sem_imagem = [q for q in questoes.values() if not q["tem_imagem"] and not q["anulada"]]
    pendentes = [q for q in sem_imagem if q["conferencia"]["pendencias"]]
    print(f"{len(questoes)} questões, {len(sem_imagem)} sem imagem e válidas, {len(pendentes)} com pendências")


def salvar(caminho, dados) -> None:
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"salvo: {caminho.name}")


if __name__ == "__main__":
    main()
