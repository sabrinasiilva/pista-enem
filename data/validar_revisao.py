"""Valida um arquivo de revisão manual (data/anotacoes/revisao/*.json).

Uso: python data/validar_revisao.py data/anotacoes/revisao/lote_1.json
"""

import json
import re
import sys

LETRAS = "ABCDE"
CAMPOS = {"id", "enunciado", "alternativas", "depende_de_figura", "observacao_transcricao",
          "gabarito_calculado", "resolucao", "enganos", "conceitos"}
# \t, \f, \b, \r: viram caracteres de controle quando \times, \frac, \beta... ficam sem escape
CONTROLE = re.compile(r"[\x00-\x09\x0b-\x1f]")
# Cifrão literal (dinheiro, senha) é escrito \$, como no remark-math; $ sem barra abre e fecha fórmula.
DELIMITADOR = re.compile(r"(?<!\\)\$")
CIFRAO_SEM_ESCAPE = re.compile(r"(?<!\$)R\$\s*\d")  # "R$ 2,00"; não confunde com a variável "$R$"
FORMULA = re.compile(r"(?<!\\)\$\$?(.+?)(?<!\\)\$\$?", re.S)


def problemas_da_revisao(revisao: dict) -> list[str]:
    erros = []
    faltando = CAMPOS - revisao.keys()
    if faltando:
        return [f"campos faltando: {sorted(faltando)}"]
    if not re.fullmatch(r"20\d\d-1[3-8]\d", revisao["id"]):
        erros.append("id inválido")
    if sorted(revisao["alternativas"]) != list(LETRAS):
        erros.append("alternativas precisam ser exatamente A, B, C, D e E")
    if revisao["gabarito_calculado"] not in LETRAS:
        erros.append("gabarito_calculado precisa ser uma letra de A a E")
    erradas = sorted(set(LETRAS) - {revisao["gabarito_calculado"]})
    if sorted(revisao["enganos"]) != erradas:
        erros.append(f"enganos precisam ter exatamente as letras {erradas}")
    if not isinstance(revisao["depende_de_figura"], bool):
        erros.append("depende_de_figura precisa ser true ou false")
    if not (isinstance(revisao["conceitos"], list) and 1 <= len(revisao["conceitos"]) <= 4):
        erros.append("conceitos precisa ser uma lista com 1 a 4 itens")

    textos = [revisao["enunciado"], revisao["resolucao"], *revisao["alternativas"].values(), *revisao["enganos"].values()]
    for texto in textos:
        if not isinstance(texto, str) or not texto.strip():
            erros.append("há texto vazio")
            break
        if CONTROLE.search(texto):
            erros.append("caractere de controle encontrado: barra invertida sem escape no JSON (use \\\\frac, \\\\times...)")
            break
        if CIFRAO_SEM_ESCAPE.search(texto):
            erros.append(f"cifrão de dinheiro sem escape (escreva R\\$) em: {texto[:60]!r}")
            break
        if len(DELIMITADOR.findall(texto)) % 2:
            erros.append(f"número ímpar de $ em: {texto[:60]!r}")
            break
        if any("\n" in formula for formula in FORMULA.findall(texto)):
            # \neq, \nu sem escape viram quebra de linha dentro da fórmula
            erros.append(f"quebra de linha dentro de fórmula (\\n sem escape?) em: {texto[:60]!r}")
            break
    return erros


def main(caminho: str) -> int:
    revisoes = json.loads(open(caminho, encoding="utf-8").read())
    total = 0
    for revisao in revisoes:
        erros = problemas_da_revisao(revisao)
        for erro in erros:
            print(f"{revisao.get('id', '?')}: {erro}")
        total += len(erros)
    print(f"{len(revisoes)} revisões, {total} problemas")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
