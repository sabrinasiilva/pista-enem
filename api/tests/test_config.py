import pytest

from app.config import Configuracoes


@pytest.mark.parametrize(
    ("recebida", "esperada"),
    [
        (
            "postgresql://u:s@ep-x.neon.tech/pista?sslmode=require",
            "postgresql+psycopg://u:s@ep-x.neon.tech/pista?sslmode=require",
        ),
        ("postgres://u:s@host/pista", "postgresql+psycopg://u:s@host/pista"),
        ("postgresql+psycopg://u:s@host/pista", "postgresql+psycopg://u:s@host/pista"),
        ("sqlite:///pista.db", "sqlite:///pista.db"),
    ],
)
def test_url_do_banco_usa_o_driver_psycopg(recebida, esperada):
    assert Configuracoes(database_url=recebida).database_url == esperada


def test_origens_do_cors():
    config = Configuracoes(cors_origens="https://sabrinasiilva.github.io, http://localhost:5173")
    assert config.lista_de_origens == ["https://sabrinasiilva.github.io", "http://localhost:5173"]


def test_migracoes_usam_o_usuario_dono_quando_informado():
    config = Configuracoes(
        database_url="postgresql://pista_app:x@host/neondb",
        migracoes_database_url="postgresql://neondb_owner:y@host/neondb",
    )
    assert config.database_url.startswith("postgresql+psycopg://pista_app")
    assert config.url_das_migracoes.startswith("postgresql+psycopg://neondb_owner")


def test_sem_url_das_migracoes_usa_a_mesma_do_dia_a_dia():
    config = Configuracoes(database_url="postgresql://u:s@host/neondb", migracoes_database_url="")
    assert config.url_das_migracoes == config.database_url
