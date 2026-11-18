"""Monta data/questoes-mvp.json com as 60 questões do MVP e o relatório data/RELATORIO.md.

Uso: python data/selecionar.py

Junta três coisas:
- data/questoes.json: gabarito, habilidade e dificuldade oficiais (microdados do Inep);
- data/anotacoes/revisao/*.json: transcrição revisada a partir da prova oficial,
  resolução e engano provável de cada alternativa errada;
- data/matriz_matematica.json: descrição das habilidades e competências.

Uma questão só entra no MVP se:
1. não é anulada, não depende de figura e é igual em todos os cadernos regulares;
2. a resolução da revisão chegou ao mesmo gabarito oficial do Inep;
3. a transcrição revisada é parecida com o texto extraído do PDF oficial.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from itertools import zip_longest

import extrair
import fontes

TAMANHO_MVP = 60
LIMITE_TRANSCRICAO = 0.80


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
    for ano in fontes.ANOS:
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


def escolher(elegiveis: list[dict], tamanho: int) -> list[dict]:
    """Escolhe as questões alternando entre habilidades, para cobrir o máximo da matriz.

    Dentro de cada habilidade, alterna os anos. O resultado é determinístico.
    """
    por_habilidade = defaultdict(list)
    for questao in sorted(elegiveis, key=lambda q: (q["ano"], q["numero"])):
        por_habilidade[questao["habilidade"]["codigo"]].append(questao)
    for habilidade, questoes in por_habilidade.items():
        por_ano = defaultdict(list)
        for questao in questoes:
            por_ano[questao["ano"]].append(questao)
        intercaladas = zip_longest(*(por_ano[a] for a in sorted(por_ano)))
        por_habilidade[habilidade] = [q for grupo in intercaladas for q in grupo if q]

    ordem = sorted(por_habilidade, key=lambda h: int(h[1:]))
    escolhidas = []
    for rodada in zip_longest(*(por_habilidade[h] for h in ordem)):
        for questao in rodada:
            if questao and len(escolhidas) < tamanho:
                escolhidas.append(questao)
    return sorted(escolhidas, key=lambda q: (q["ano"], q["numero"]))


def montar(questao: dict, revisao: dict, matriz: dict) -> dict:
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


def relatorio(questoes: dict, revisoes: dict, escolhidas: list, excluidas: dict, elegiveis: list,
              similaridades: dict) -> str:
    linhas = [
        "# Relatório dos dados do MVP",
        "",
        "Gerado por `data/selecionar.py`. Não edite à mão.",
        "",
        "## Resumo",
        "",
        f"- Questões de Matemática extraídas (2022 a 2024): {len(questoes)}",
        f"- Sem imagem, não anuladas e iguais à prova regular: {len(revisoes)} (todas revisadas a partir da prova oficial)",
        f"- Elegíveis depois da revisão: {len(elegiveis)}",
        f"- Escolhidas para o MVP: {len(escolhidas)}",
        f"- Gabaritos conferidos com os microdados do Inep: {len(escolhidas)} de {len(escolhidas)}",
        "",
        "## Questões escolhidas",
        "",
        "| Questão | Habilidade | Dificuldade (TRI) | Transcrição × PDF |",
        "|---|---|---|---|",
    ]
    for questao in escolhidas:
        tri = f"{questao['dificuldade_tri']:.2f}" if questao["dificuldade_tri"] is not None else "—"
        linhas.append(f"| {questao['id']} | {questao['habilidade']['codigo']} | {tri} | {similaridades[questao['id']]:.0%} |")

    contagem = defaultdict(int)
    for questao in escolhidas:
        contagem[questao["habilidade"]["codigo"]] += 1
    linhas += ["", "## Cobertura da matriz", "",
               f"{len(contagem)} das 30 habilidades aparecem no MVP.", "",
               "| Habilidade | Questões |", "|---|---|"]
    for codigo in sorted(contagem, key=lambda c: int(c[1:])):
        linhas.append(f"| {codigo} | {contagem[codigo]} |")

    linhas += ["", "## Revisadas e excluídas", "", "| Questão | Motivo |", "|---|---|"]
    for id_questao, motivos in sorted(excluidas.items()):
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
            agrupadas["dependem de figura (MVP é só texto)"].append(questao["id"])
        elif similaridade is None or similaridade < 0.5:
            agrupadas["o conjunto da Maritaca traz a questão substituta do caderno adaptado, não a da prova regular"].append(questao["id"])
        else:
            agrupadas["item diferente entre cadernos regulares"].append(questao["id"])
    for motivo, ids in agrupadas.items():
        linhas.append(f"- **{motivo}** ({len(ids)}): {', '.join(sorted(ids))}")
    return "\n".join(linhas) + "\n"


def main() -> None:
    questoes = {q["id"]: q for q in json.loads((fontes.PASTA_DADOS / "questoes.json").read_text(encoding="utf-8"))}
    matriz = json.loads((fontes.PASTA_DADOS / "matriz_matematica.json").read_text(encoding="utf-8"))
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
            elegiveis.append(montar(questao, revisao, matriz))

    assert len(elegiveis) >= TAMANHO_MVP, f"só {len(elegiveis)} questões elegíveis"
    escolhidas = escolher(elegiveis, TAMANHO_MVP)

    extrair.salvar(fontes.PASTA_DADOS / "questoes-mvp.json", escolhidas)
    (fontes.PASTA_DADOS / "RELATORIO.md").write_text(
        relatorio(questoes, revisoes, escolhidas, excluidas, elegiveis, similaridades), encoding="utf-8")
    print(f"{len(elegiveis)} elegíveis, {len(escolhidas)} escolhidas, {len(excluidas)} excluídas na revisão")


if __name__ == "__main__":
    main()
