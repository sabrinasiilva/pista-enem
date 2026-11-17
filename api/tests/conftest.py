from __future__ import annotations

import pytest

from app.config import RAIZ_DO_REPOSITORIO
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
