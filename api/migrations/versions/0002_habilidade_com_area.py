"""habilidade com a área ("MT-H16"), para caber Ciências da Natureza

Revisão: 0002
Anterior: 0001
Criada em: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# até aqui só havia Matemática: todo código antigo ("H16") é de Matemática
usuarios = sa.table("usuarios", sa.column("id", sa.String), sa.column("habilidades_foco", sa.JSON))


def upgrade() -> None:
    with op.batch_alter_table("resultados") as tabela:
        tabela.alter_column("habilidade", type_=sa.String(length=8), existing_type=sa.String(length=5))
    op.execute("UPDATE resultados SET habilidade = 'MT-' || habilidade WHERE habilidade NOT LIKE '%-%'")

    conexao = op.get_bind()
    for id_usuario, foco in conexao.execute(sa.select(usuarios.c.id, usuarios.c.habilidades_foco)).all():
        novo = [h if "-" in h else f"MT-{h}" for h in foco or []]
        if novo != (foco or []):
            conexao.execute(usuarios.update().where(usuarios.c.id == id_usuario).values(habilidades_foco=novo))


def downgrade() -> None:
    conexao = op.get_bind()
    for id_usuario, foco in conexao.execute(sa.select(usuarios.c.id, usuarios.c.habilidades_foco)).all():
        antigos = [h.removeprefix("MT-") for h in foco or [] if not h.startswith("CN-")]
        conexao.execute(usuarios.update().where(usuarios.c.id == id_usuario).values(habilidades_foco=antigos))
    op.execute("DELETE FROM resultados WHERE habilidade LIKE 'CN-%'")
    op.execute("UPDATE resultados SET habilidade = substr(habilidade, 4) WHERE habilidade LIKE 'MT-%'")
    with op.batch_alter_table("resultados") as tabela:
        tabela.alter_column("habilidade", type_=sa.String(length=5), existing_type=sa.String(length=8))
