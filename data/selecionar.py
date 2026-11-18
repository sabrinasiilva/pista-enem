"""Monta data/questoes-mvp.json com as questões do tutor e o relatório data/RELATORIO.md.

Uso: python data/selecionar.py

Junta três coisas:
- data/questoes.json: gabarito, habilidade e dificuldade oficiais (microdados do Inep);
- data/anotacoes/revisao/*.json: transcrição revisada a partir da prova oficial,
  resolução e engano provável de cada alternativa errada;
- data/matriz_<area>.json: descrição das habilidades e competências de cada área.

Entram todas as questões que passam nos critérios (a v0.1.0 tinha 60 de Matemática; a v0.2.0
junta Matemática de 2025 e Ciências da Natureza). Uma questão só entra se:
1. não é anulada, não depende de figura e é igual em todos os cadernos regulares;
2. a resolução da revisão chegou ao mesmo gabarito oficial do Inep;
3. a transcrição revisada é parecida com o texto extraído do PDF oficial.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict

import extrair
import fontes

MINIMO_POR_AREA = 60
LIMITE_TRANSCRICAO = 0.80
NOMES_DAS_AREAS = {"matematica": "Matemática", "natureza": "Ciências da Natureza"}


def ler_revisoes() -> dict[str, dict]:
    revisoes = {}
    for caminho in sorted((fontes.PASTA_DADOS / "anotacoes" / "revisao").glob("*.json")):
        for revisao in json.loads(caminho.read_text(encoding="utf-8")):
            assert revisao["id"] not in revisoes, f"{revisao['id']} revisada duas vezes"
            revisoes[revisao["id"]] = revisao
    return revisoes


def sem_latex(texto: str) -> str:
    """Remove comandos LaTeX e marcação Markdown para comparar com o texto do PDF."""
    texto = re.sub(r"\\[a-zA-Z]+", " ", texto)
    return re.sub(r"[$|{}^_*:-]", " ", texto)


def similaridade_com_pdf(revisao: dict, enunciado_pdf: str | None) -> float | None:
    if enunciado_pdf is None:
        return None
    return extrair.similaridade(sem_latex(revisao["enunciado"]), enunciado_pdf)


def enunciados_do_pdf() -> dict[str, str]:
    enunciados = {}
    for ano in fontes.TODOS_OS_ANOS:
        blocos = extrair.blocos_por_questao(extrair.texto_da_prova(fontes.caminho_prova(ano)))
        for numero, bloco in blocos.items():
            separado = extrair.separar_alternativas(bloco)
            if separado:
                enunciados[f"{ano}-{numero}"] = separado[0]
    return enunciados


def motivos_de_exclusao(questao: dict, revisao: dict, similaridade: float | None) -> list[str]:
    motivos = []
    if questao["anulada"]:
        motivos.append("anulada pelo Inep")
    if questao["tem_imagem"] or revisao["depende_de_figura"]:
        motivos.append("depende de figura")
    if not questao["conferencia"]["item_igual_nos_cadernos_regulares"]:
        motivos.append("item diferente entre cadernos regulares")
    if revisao["gabarito_calculado"] != questao["gabarito"]:
        motivos.append(f"resolução chegou em {revisao['gabarito_calculado']}, gabarito oficial é {questao['gabarito']}")
    if similaridade is None:
        motivos.append("questão não encontrada no PDF")
    elif similaridade < LIMITE_TRANSCRICAO:
        motivos.append(f"transcrição só {similaridade:.0%} parecida com o PDF")
    return motivos


def montar(questao: dict, revisao: dict, matriz: dict) -> dict:
    """Junta a questão oficial, a revisão e a matriz da área no formato que a API lê."""
    habilidades = {h["codigo"]: h for h in matriz["habilidades"]}
    competencias = {c["codigo"]: c for c in matriz["competencias"]}
    habilidade = habilidades[questao["habilidade"]]
    competencia = competencias[habilidade["competencia"]]
    return {
        "id": questao["id"],
        "ano": questao["ano"],
        "numero": questao["numero"],
        "area": questao["area"],
        "enunciado": revisao["enunciado"],
        "alternativas": [
            {
                "letra": letra,
                "texto": revisao["alternativas"][letra],
                "engano_provavel": revisao["enganos"].get(letra),
            }
            for letra in extrair.LETRAS
        ],
        "gabarito": questao["gabarito"],
        "resolucao": revisao["resolucao"],
        "habilidade": {"codigo": habilidade["codigo"], "descricao": habilidade["descricao"]},
        "competencia": {"codigo": competencia["codigo"], "descricao": competencia["descricao"]},
        "conceitos": revisao["conceitos"],
        "dificuldade_tri": questao["dificuldade_tri"],
        "fonte": questao["fonte"],
    }


def relatorio(questoes: dict, revisoes: dict, escolhidas: list, excluidas: dict, similaridades: dict,
              matrizes: dict) -> str:
    linhas = [
        "# Relatório dos dados",
        "",
        "Gerado por `data/selecionar.py`. Não edite à mão.",
        "",
        "## Resumo",
        "",
        "| Área | Extraídas | Revisadas | No tutor |",
        "|---|---|---|---|",
    ]
    for area, nome in NOMES_DAS_AREAS.items():
        extraidas = [q for q in questoes.values() if q["area"] == area]
        revisadas = [i for i in revisoes if questoes[i]["area"] == area]
        no_tutor = [q for q in escolhidas if q["area"] == area]
        anos = sorted({q["ano"] for q in extraidas})
        linhas.append(f"| {nome} ({anos[0]} a {anos[-1]}) | {len(extraidas)} | {len(revisadas)} | {len(no_tutor)} |")
    linhas += [
        "",
        f"Gabaritos conferidos com os microdados do Inep: {len(escolhidas)} de {len(escolhidas)}.",
        "Revisadas são as que não são anuladas, não têm figura conhecida e são iguais em todos os cadernos regulares; "
        "todas foram transcritas de novo a partir da prova oficial e resolvidas sem ver o gabarito.",
    ]

    for area, nome in NOMES_DAS_AREAS.items():
        da_area = [q for q in escolhidas if q["area"] == area]
        linhas += ["", f"## {nome}", "", "| Questão | Habilidade | Dificuldade (TRI) | Transcrição × PDF |", "|---|---|---|---|"]
        for questao in da_area:
            tri = f"{questao['dificuldade_tri']:.2f}" if questao["dificuldade_tri"] is not None else "—"
            linhas.append(f"| {questao['id']} | {questao['habilidade']['codigo']} | {tri} | {similaridades[questao['id']]:.0%} |")
        contagem = defaultdict(int)
        for questao in da_area:
            contagem[questao["habilidade"]["codigo"]] += 1
        total = len(matrizes[area]["habilidades"])
        linhas += ["", f"{len(contagem)} das {total} habilidades da matriz aparecem.", "",
                   "| Habilidade | Questões |", "|---|---|"]
        for codigo in sorted(contagem, key=lambda c: int(c[1:])):
            linhas.append(f"| {codigo} | {contagem[codigo]} |")

    linhas += ["", "## Revisadas e excluídas", "", "| Questão | Motivo |", "|---|---|"]
    for id_questao, motivos in sorted(excluidas.items(), key=lambda par: tuple(map(int, par[0].split("-")))):
        linhas.append(f"| {id_questao} | {'; '.join(motivos)} |")
    if not excluidas:
        linhas.append("| — | — |")

    nao_revisadas = [q for q in questoes.values() if q["id"] not in revisoes]
    linhas += ["", "## Não revisadas", "",
               f"{len(nao_revisadas)} questões ficaram de fora antes da revisão:", ""]
    agrupadas = defaultdict(list)
    for questao in nao_revisadas:
        similaridade = questao["conferencia"]["similaridade_enunciado_pdf"]
        if questao["anulada"]:
            agrupadas["anuladas pelo Inep"].append(questao["id"])
        elif questao["tem_imagem"]:
            agrupadas["dependem de figura (o tutor é só texto)"].append(questao["id"])
        elif similaridade is None or similaridade < 0.5:
            agrupadas["o conjunto da Maritaca traz a questão substituta do caderno adaptado, não a da prova regular"].append(questao["id"])
        else:
            agrupadas["item diferente entre cadernos regulares"].append(questao["id"])
    for motivo, ids in agrupadas.items():
        ids = sorted(ids, key=lambda i: tuple(map(int, i.split("-"))))
        linhas.append(f"- **{motivo}** ({len(ids)}): {', '.join(ids)}")
    return "\n".join(linhas) + "\n"


def main() -> None:
    questoes = {q["id"]: q for q in json.loads((fontes.PASTA_DADOS / "questoes.json").read_text(encoding="utf-8"))}
    matrizes = {area: json.loads((fontes.PASTA_DADOS / f"matriz_{area}.json").read_text(encoding="utf-8"))
                for area in fontes.AREAS}
    revisoes = ler_revisoes()
    pdf = enunciados_do_pdf()

    elegiveis, excluidas, similaridades = [], {}, {}
    for id_questao, revisao in revisoes.items():
        questao = questoes[id_questao]
        similaridades[id_questao] = similaridade_com_pdf(revisao, pdf.get(id_questao))
        motivos = motivos_de_exclusao(questao, revisao, similaridades[id_questao])
        if motivos:
            excluidas[id_questao] = motivos
        else:
            elegiveis.append(montar(questao, revisao, matrizes[questao["area"]]))

    for area in fontes.AREAS:
        quantas = sum(q["area"] == area for q in elegiveis)
        assert quantas >= MINIMO_POR_AREA, f"só {quantas} questões elegíveis em {area}"
    escolhidas = sorted(elegiveis, key=lambda q: (q["area"] != "matematica", q["ano"], q["numero"]))

    extrair.salvar(fontes.PASTA_DADOS / "questoes-mvp.json", escolhidas)
    (fontes.PASTA_DADOS / "RELATORIO.md").write_text(
        relatorio(questoes, revisoes, escolhidas, excluidas, similaridades, matrizes), encoding="utf-8")
    for area in fontes.AREAS:
        print(f"{area}: {sum(q['area'] == area for q in escolhidas)} no tutor")
    print(f"{len(escolhidas)} no total, {len(excluidas)} excluídas na revisão")


if __name__ == "__main__":
    main()
