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
