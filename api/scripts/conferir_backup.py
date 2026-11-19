"""Confere se uma cópia restaurada do banco bate com o original.

Uso (PowerShell, colando as conexões no próprio terminal, nunca no código nem no chat):
    $env:BANCO_ORIGEM = "postgresql://..."      # branch principal do Neon
    $env:BANCO_RESTAURADO = "postgresql://..."  # branch restaurada
    python scripts/conferir_backup.py

Mostra só a contagem de linhas de cada tabela e a versão das migrações, nunca dados das contas.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, inspect, text

TABELAS = ["usuarios", "acessos", "resultados", "alembic_version"]


def motor(variavel: str):
    url = os.environ.get(variavel, "").strip()
    if not url:
        sys.exit(f"Defina {variavel} no terminal antes de rodar.")
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return create_engine(url)


def retrato(variavel: str) -> dict[str, object]:
    with motor(variavel).connect() as conexao:
        existentes = set(inspect(conexao).get_table_names())
        dados: dict[str, object] = {}
        for tabela in TABELAS:
            if tabela not in existentes:
                dados[tabela] = "não existe"
            elif tabela == "alembic_version":
                dados[tabela] = conexao.execute(text("select version_num from alembic_version")).scalar()
            else:
                dados[tabela] = conexao.execute(text(f"select count(*) from {tabela}")).scalar()  # noqa: S608 - nome fixo
        ultimo = conexao.execute(text("select max(concluido_em) from resultados")).scalar()
        dados["último resultado"] = str(ultimo)[:16] if ultimo else "nenhum"
        return dados


def main() -> None:
    origem, restaurado = retrato("BANCO_ORIGEM"), retrato("BANCO_RESTAURADO")
    print(f"{'':18}{'original':>18}{'restaurado':>18}")
    for chave in origem:
        marca = "" if origem[chave] == restaurado[chave] else "  <- diferente"
        print(f"{chave:18}{origem[chave]!s:>18}{restaurado[chave]!s:>18}{marca}")
    print("\nDiferença pequena é normal se alguém usou o Pista depois do horário escolhido na restauração.")


if __name__ == "__main__":
    main()
