from sqlalchemy import create_engine, inspect

from app.banco import Base
from app.main import migrar


def test_migracoes_criam_as_mesmas_tabelas_do_modelo(tmp_path):
    url = f"sqlite:///{(tmp_path / 'teste.db').as_posix()}"
    migrar(url)
    inspetor = inspect(create_engine(url))
    tabelas = set(inspetor.get_table_names()) - {"alembic_version"}
    assert tabelas == set(Base.metadata.tables)
    for nome, tabela in Base.metadata.tables.items():
        colunas = {coluna["name"] for coluna in inspetor.get_columns(nome)}
        assert colunas == set(tabela.columns.keys()), nome


def test_migrar_duas_vezes_nao_quebra(tmp_path):
    url = f"sqlite:///{(tmp_path / 'teste.db').as_posix()}"
    migrar(url)
    migrar(url)
