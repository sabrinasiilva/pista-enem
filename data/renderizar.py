"""Gera imagens das páginas oficiais de cada questão, para revisão humana.

Uso: python data/renderizar.py

Salva em data/brutos/paginas/ (não versionado) e cria data/brutos/paginas/indice.json,
que diz em quais imagens está cada questão.
"""

import json
import re

import pymupdf

import fontes

RESOLUCAO = 150


def main() -> None:
    pasta = fontes.PASTA_BRUTOS / "paginas"
    pasta.mkdir(parents=True, exist_ok=True)
    indice = {}
    for ano in fontes.TODOS_OS_ANOS:
        with pymupdf.open(fontes.caminho_prova(ano)) as documento:
            pagina_da_questao = {}
            for numero_pagina, pagina in enumerate(documento):
                # "QUESTÃO 141" até 2024 e "Questão 141" em 2025 (search_for não iguala Ã e ã)
                for achado in re.finditer(r"QUESTÃO\s*(\d{2,3})\b", pagina.get_text(), re.IGNORECASE):
                    pagina_da_questao.setdefault(int(achado.group(1)), numero_pagina)
            ultima = len(documento) - 1
            for numero, inicio in pagina_da_questao.items():
                # a questão vai até a página onde começa a próxima
                fim = pagina_da_questao.get(numero + 1, min(inicio + 1, ultima))
                arquivos = []
                for numero_pagina in range(inicio, fim + 1):
                    destino = pasta / f"{ano}_pagina_{numero_pagina + 1:02d}.png"
                    if not destino.exists():
                        documento[numero_pagina].get_pixmap(dpi=RESOLUCAO).save(destino)
                    arquivos.append(str(destino))
                indice[f"{ano}-{numero}"] = arquivos
    (pasta / "indice.json").write_text(json.dumps(indice, indent=2), encoding="utf-8")
    print(f"{len(indice)} questões indexadas em {pasta}")


if __name__ == "__main__":
    main()
