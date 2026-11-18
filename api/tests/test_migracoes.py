import json

from sqlalchemy import create_engine, inspect, text

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


def test_migracao_0002_poe_a_area_nos_codigos_antigos(tmp_path):
    url = f"sqlite:///{(tmp_path / 'teste.db').as_posix()}"
    migrar(url, "0001")
    motor = create_engine(url)
    with motor.begin() as conexao:
        conexao.execute(
            text(
                "INSERT INTO usuarios (id, apelido, senha_hash, codigo_recuperacao_hash, meta_semanal, "
                "habilidades_foco, tema, criado_em) "
                "VALUES ('u1', 'ana', 'x', 'y', 10, :foco, 'auto', '2026-11-18 10:00:00')"
            ),
            {"foco": json.dumps(["H16", "H3"])},
        )
        conexao.execute(
            text(
                "INSERT INTO resultados (usuario_id, questao_id, habilidade, acertou, acertou_de_primeira, tentativas, "
                "pediu_explicacao, concluido_em) VALUES ('u1', '2022-141', 'H16', 1, 1, 1, 0, '2026-11-18 10:00:00')"
            )
        )
    motor.dispose()

    migrar(url)
    motor = create_engine(url)
    with motor.connect() as conexao:
        assert json.loads(conexao.execute(text("SELECT habilidades_foco FROM usuarios")).scalar()) == [
            "MT-H16",
            "MT-H3",
        ]
        assert conexao.execute(text("SELECT habilidade FROM resultados")).scalar() == "MT-H16"
    motor.dispose()
