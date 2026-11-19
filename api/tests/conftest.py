from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.banco import Base
from app.config import RAIZ_DO_REPOSITORIO, Configuracoes
from app.main import criar_app
from app.tutor.motor import Tutor
from app.tutor.prompts import Prompts
from app.tutor.questoes import BancoDeQuestoes, Questao
from tests.auxiliares import IAFalsa, questao_exemplo


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def banco_real() -> BancoDeQuestoes:
    return BancoDeQuestoes.de_arquivo(RAIZ_DO_REPOSITORIO / "data" / "questoes-mvp.json")


@pytest.fixture(scope="session")
def prompts() -> Prompts:
    return Prompts.carregar(RAIZ_DO_REPOSITORIO / "prompts", "tutor_v1")


@pytest.fixture
def questao() -> Questao:
    return questao_exemplo()


@pytest.fixture
def criar(prompts, questao):
    """Cria um tutor com a questão de exemplo e a IA simulada."""

    def _criar(*respostas: str | Exception, sem_ia: bool = False) -> tuple[Tutor, IAFalsa]:
        ia = IAFalsa(*respostas)
        tutor = Tutor(BancoDeQuestoes([questao]), prompts, None if sem_ia else ia)
        return tutor, ia

    return _criar


@pytest.fixture
def motor():
    """Banco SQLite em memória, novo a cada teste."""
    motor = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(motor)
    yield motor
    motor.dispose()


@pytest.fixture
def montar(prompts, motor):
    """Cria um cliente HTTP com a questão de exemplo e as respostas simuladas da IA."""

    abertos: list[TestClient] = []

    def _montar(*respostas, banco=None) -> tuple[TestClient, IAFalsa]:
        ia = IAFalsa(*respostas)
        tutor = Tutor(banco or BancoDeQuestoes([questao_exemplo()]), prompts, ia)
        cliente = TestClient(criar_app(Configuracoes(), tutor, motor), raise_server_exceptions=False)
        cliente.__enter__()  # roda o ciclo de vida (lifespan)
        abertos.append(cliente)
        return cliente, ia

    yield _montar
    for cliente in abertos:
        cliente.__exit__(None, None, None)
