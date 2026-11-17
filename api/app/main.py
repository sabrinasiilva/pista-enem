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

from . import __version__
from .config import Configuracoes, configuracoes
from .erros import registrar_tratadores
from .esquemas import Saude
from .rotas import questoes, sessoes
from .sessoes import RepositorioDeSessoes
from .tutor.fabrica import criar_tutor
from .tutor.motor import Tutor

DESCRICAO = """
Tutor socrático com IA para o ENEM: dá pistas, não respostas.

**Fluxo de uma questão**
1. `GET /questoes` e `GET /questoes/{id}` para escolher e mostrar a questão (sem o gabarito).
2. `POST /sessoes` abre uma sessão anônima.
3. `POST /sessoes/{id}/respostas` envia a alternativa marcada. Errou: vem uma pista. Acertou: a sessão termina.
4. `POST /sessoes/{id}/mensagens` conversa com o tutor (streaming).
5. `POST /sessoes/{id}/explicacao` mostra a resolução, se o aluno confirmar.

Erros sempre vêm como `{"erro": {"codigo": ..., "mensagem": ...}}`.

Código: [github.com/sabrinasiilva/pista-enem](https://github.com/sabrinasiilva/pista-enem)
"""


def criar_app(config: Configuracoes | None = None, tutor: Tutor | None = None) -> FastAPI:
    config = config or configuracoes()

    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI):
        app.state.tutor = tutor or criar_tutor(config)
        app.state.sessoes = RepositorioDeSessoes()
        yield

    app = FastAPI(
        title="Pista API",
        version=__version__,
        description=DESCRICAO,
        lifespan=ciclo_de_vida,
        openapi_tags=[
            {"name": "Questões", "description": "Questões oficiais do ENEM, sem o gabarito"},
            {"name": "Sessões", "description": "Resolução de uma questão com o tutor"},
            {"name": "Sistema", "description": "Estado da API"},
        ],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.lista_de_origens,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    registrar_tratadores(app)
    app.include_router(questoes.rotas)
    app.include_router(sessoes.rotas)

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
