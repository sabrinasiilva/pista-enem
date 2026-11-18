"""Aplicação FastAPI do Pista.

Rodar localmente (dentro de api/):
    uvicorn app.main:app --reload
Documentação: http://localhost:8000/docs
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine

from . import __version__
from .banco import criar_motor, fabrica_de_sessoes
from .config import PASTA_API, Configuracoes, configuracoes
from .erros import registrar_tratadores
from .esquemas import Saude
from .limites import LimiteDeTentativas
from .rotas import contas, eu, questoes, sessoes
from .sessoes import RepositorioDeSessoes
from .tutor.fabrica import criar_tutor
from .tutor.motor import Tutor

DESCRICAO = """
Tutor socrático com IA para o ENEM: dá pistas, não respostas.

**Fluxo de uma questão**
1. `GET /questoes` e `GET /questoes/{id}` para escolher e mostrar a questão (sem o gabarito).
2. `POST /sessoes` abre uma sessão (anônima, ou da conta, se vier o token).
3. `POST /sessoes/{id}/respostas` envia a alternativa marcada. Errou: vem uma pista. Acertou: a sessão termina.
4. `POST /sessoes/{id}/mensagens` conversa com o tutor (streaming).
5. `POST /sessoes/{id}/explicacao` mostra a resolução, se o aluno confirmar.

**Contas (opcionais):** só apelido e senha, sem dados pessoais. `POST /contas` devolve um token;
envie-o como `Authorization: Bearer <token>` para gravar o progresso.

Erros sempre vêm como `{"erro": {"codigo": ..., "mensagem": ...}}`.

Código: [github.com/sabrinasiilva/pista-enem](https://github.com/sabrinasiilva/pista-enem)
"""


def migrar(url: str) -> None:
    """Aplica as migrações do Alembic até a última versão."""
    from alembic import command
    from alembic.config import Config

    alembic = Config(str(PASTA_API / "alembic.ini"), attributes={"configurar_logs": False})
    alembic.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(alembic, "head")


def criar_app(config: Configuracoes | None = None, tutor: Tutor | None = None, motor: Engine | None = None) -> FastAPI:
    config = config or configuracoes()

    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI):
        app.state.tutor = tutor or criar_tutor(config)
        app.state.sessoes = RepositorioDeSessoes()
        app.state.limite_de_login = LimiteDeTentativas()
        if motor is None and config.migrar_ao_iniciar:
            migrar(config.url_das_migracoes)
        motor_em_uso = motor or criar_motor(config.database_url)
        app.state.fabrica_de_sessoes = fabrica_de_sessoes(motor_em_uso)
        yield
        if motor is None:
            motor_em_uso.dispose()

    app = FastAPI(
        title="Pista API",
        version=__version__,
        description=DESCRICAO,
        lifespan=ciclo_de_vida,
        openapi_tags=[
            {"name": "Questões", "description": "Questões oficiais do ENEM, sem o gabarito"},
            {"name": "Sessões", "description": "Resolução de uma questão com o tutor"},
            {"name": "Contas", "description": "Conta opcional, só com apelido e senha"},
            {"name": "Perfil e progresso", "description": "Meta, habilidades em foco, tema e histórico"},
            {"name": "Sistema", "description": "Estado da API"},
        ],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.lista_de_origens,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )
    registrar_tratadores(app)
    app.include_router(questoes.rotas)
    app.include_router(sessoes.rotas)
    app.include_router(contas.rotas)
    app.include_router(eu.rotas)

    @app.get("/health", tags=["Sistema"], summary="Verifica se a API está de pé", response_model=Saude)
    def saude() -> Saude:
        estado_tutor: Tutor = app.state.tutor
        return Saude(
            status="ok",
            versao=__version__,
            questoes=len(estado_tutor.banco),
            ia="gemini" if estado_tutor.ia is not None else "desativada",
            prompt=estado_tutor.prompts.versao,
        )

    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
app = criar_app()
