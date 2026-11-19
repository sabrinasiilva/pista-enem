"""Compara dois juízes nas mesmas mensagens: quanto o juiz barato concorda com o mais forte.

Uso: python evals/concordancia.py <relatorio>-juiz.json <relatorio>-juiz-flash.json

O primeiro arquivo é o juiz que julgou tudo; o segundo, o que julgou uma amostra. Se os dois concordam
na grande maioria, as métricas do primeiro valem para a rodada inteira. Gera <segundo>-concordancia.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CRITERIOS = {"revela": "Revela a resposta", "socratica": "Aderência socrática", "diagnostico": "Diagnóstico do engano"}


def comparar(base: list[dict], referencia: list[dict]) -> dict:
    """Para cada critério, quantas mensagens os dois julgaram e em quantas concordaram."""
    validos = {(j["caso"], j["fala"]): j for j in base if "erro" not in j}
    pares = [
        (validos[(r["caso"], r["fala"])], r)
        for r in referencia
        if "erro" not in r and (r["caso"], r["fala"]) in validos
    ]
    resultado = {"mensagens": len(pares), "criterios": {}, "divergencias": []}
    for chave in CRITERIOS:
        comparaveis = [(a, b) for a, b in pares if a.get(chave) is not None and b.get(chave) is not None]
        iguais = sum(a[chave] == b[chave] for a, b in comparaveis)
        resultado["criterios"][chave] = {"comparadas": len(comparaveis), "iguais": iguais}
        for a, b in comparaveis:
            if a[chave] != b[chave]:
                resultado["divergencias"].append(
                    {"caso": a["caso"], "fala": a["fala"], "criterio": chave, "base": a[chave], "referencia": b[chave]}
                )
    return resultado


def relatorio(resultado: dict, modelo_base: str, modelo_referencia: str) -> str:
    linhas = [
        "# Concordância entre os juízes",
        "",
        f"`{modelo_base}` (julgou tudo) comparado com `{modelo_referencia}` (amostra) "
        f"em {resultado['mensagens']} mensagens julgadas pelos dois.",
        "",
        "| Critério | Comparadas | Concordância |",
        "|---|---|---|",
    ]
    for chave, nome in CRITERIOS.items():
        c = resultado["criterios"][chave]
        taxa = f"{100 * c['iguais'] / c['comparadas']:.0f}%" if c["comparadas"] else "—"
        linhas.append(f"| {nome} | {c['comparadas']} | {taxa} |")
    if resultado["divergencias"]:
        linhas += ["", "## Onde discordaram", ""]
        for d in resultado["divergencias"]:
            linhas.append(
                f"- `{d['caso']}` fala {d['fala']}, {CRITERIOS[d['criterio']].lower()}: "
                f"{modelo_base} disse {d['base']}, {modelo_referencia} disse {d['referencia']}"
            )
    return "\n".join(linhas) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("base", type=Path)
    parser.add_argument("referencia", type=Path)
    argumentos = parser.parse_args()
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    base = json.loads(argumentos.base.read_text(encoding="utf-8"))
    referencia = json.loads(argumentos.referencia.read_text(encoding="utf-8"))
    resultado = comparar(base["julgados"], referencia["julgados"])
    texto = relatorio(resultado, base["resumo"].get("modelo", "juiz"), referencia["resumo"].get("modelo", "referência"))
    destino = argumentos.referencia.with_name(argumentos.referencia.stem + "-concordancia.md")
    destino.write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
