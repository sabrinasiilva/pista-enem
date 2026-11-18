"""Mede a busca de habilidades (Recall@5) e mostra exemplos de questões parecidas.

Uso: python evals/busca.py [--questoes data/questoes-mvp.json]

Gabarito da busca: a habilidade oficial de cada questão, dos microdados do Inep. Cada questão é
classificada sem ver a própria resposta (deixa uma de fora): os votos vêm só das outras questões.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "api"))

from app.tutor.busca import IndiceTfIdf, cosseno, habilidades_provaveis, texto_da_questao  # noqa: E402
from app.tutor.questoes import BancoDeQuestoes  # noqa: E402

VIZINHAS = 7
METODOS = ("só a matriz", "só as vizinhas", "matriz + vizinhas")


def main() -> None:
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--questoes", type=Path, default=RAIZ / "data" / "questoes-mvp.json")
    caminho = argumentos.parse_args().questoes

    banco = BancoDeQuestoes.de_arquivo(caminho)
    questoes = sorted(banco.listar(), key=lambda q: q.id)
    indice = IndiceTfIdf([texto_da_questao(q) for q in questoes])
    matrizes = {}
    for area in {q.area for q in questoes}:
        dados = json.loads((caminho.parent / f"matriz_{area}.json").read_text(encoding="utf-8"))
        matrizes[area] = {h["codigo"]: h["descricao"] for h in dados["habilidades"]}

    acertos = {m: defaultdict(int) for m in METODOS}
    total = defaultdict(int)
    for i, questao in enumerate(questoes):
        vizinhas = sorted(
            (
                (cosseno(indice.vetores[i], indice.vetores[j]), outra.habilidade)
                for j, outra in enumerate(questoes)
                if j != i and outra.area == questao.area
            ),
            reverse=True,
        )[:VIZINHAS]
        texto = texto_da_questao(questao)
        matriz = matrizes[questao.area]
        resultados = {
            "só a matriz": habilidades_provaveis(texto, matriz),
            "só as vizinhas": habilidades_provaveis("", matriz, vizinhas),
            "matriz + vizinhas": habilidades_provaveis(texto, matriz, vizinhas),
        }
        total[questao.area] += 1
        for metodo, top5 in resultados.items():
            acertos[metodo][questao.area] += questao.habilidade in top5

    areas = sorted(total)
    print(f"Recall@5 com {len(questoes)} questões ({', '.join(f'{a}: {total[a]}' for a in areas)})\n")
    print("| Método | " + " | ".join(areas) + " | Geral |")
    print("|---|" + "---|" * (len(areas) + 1))
    for metodo in METODOS:
        celulas = [f"{acertos[metodo][a] / total[a]:.0%}" for a in areas]
        geral = sum(acertos[metodo].values()) / sum(total.values())
        print(f"| {metodo} | " + " | ".join(celulas) + f" | {geral:.0%} |")


if __name__ == "__main__":
    main()
