"""Erros padronizados: toda falha volta como {"erro": {"codigo", "mensagem"}}."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .contas import ErroDeConta
from .dependencias import LimiteAtingido
from .sessoes import SessaoNaoEncontrada
from .tutor.estados import TransicaoInvalida
from .tutor.questoes import QuestaoNaoEncontrada

logger = logging.getLogger(__name__)


def resposta_de_erro(status: int, codigo: str, mensagem: str, detalhes: list | None = None) -> JSONResponse:
    corpo: dict = {"codigo": codigo, "mensagem": mensagem}
    if detalhes is not None:
        corpo["detalhes"] = detalhes
    return JSONResponse(status_code=status, content={"erro": corpo})


def registrar_tratadores(app: FastAPI) -> None:
    @app.exception_handler(QuestaoNaoEncontrada)
    async def questao_nao_encontrada(_: Request, erro: QuestaoNaoEncontrada) -> JSONResponse:
        return resposta_de_erro(404, "questao_nao_encontrada", f"Questão {erro} não encontrada.")

    @app.exception_handler(SessaoNaoEncontrada)
    async def sessao_nao_encontrada(_: Request, __: SessaoNaoEncontrada) -> JSONResponse:
        return resposta_de_erro(404, "sessao_nao_encontrada", "Sessão não encontrada ou expirada.")

    @app.exception_handler(ErroDeConta)
    async def erro_de_conta(_: Request, erro: ErroDeConta) -> JSONResponse:
        resposta = resposta_de_erro(erro.status, erro.codigo, erro.mensagem)
        if erro.status == 401:
            resposta.headers["WWW-Authenticate"] = "Bearer"
        return resposta

    @app.exception_handler(LimiteAtingido)
    async def limite_atingido(_: Request, erro: LimiteAtingido) -> JSONResponse:
        resposta = resposta_de_erro(429, "muitas_requisicoes", erro.mensagem)
        resposta.headers["Retry-After"] = "600"
        return resposta

    @app.exception_handler(TransicaoInvalida)
    async def transicao_invalida(_: Request, erro: TransicaoInvalida) -> JSONResponse:
        return resposta_de_erro(409, erro.codigo, erro.mensagem)

    @app.exception_handler(RequestValidationError)
    async def entrada_invalida(_: Request, erro: RequestValidationError) -> JSONResponse:
        detalhes = [{"campo": ".".join(str(p) for p in e["loc"]), "problema": e["msg"]} for e in erro.errors()]
        return resposta_de_erro(422, "entrada_invalida", "Os dados enviados são inválidos.", detalhes)

    @app.exception_handler(StarletteHTTPException)
    async def erro_http(_: Request, erro: StarletteHTTPException) -> JSONResponse:
        conhecidos = {
            400: ("corpo_invalido", "O corpo da requisição não é um JSON válido (em UTF-8)."),
            404: ("rota_nao_encontrada", "Rota não encontrada."),
            405: ("metodo_nao_permitido", "Método não permitido nesta rota."),
        }
        codigo, mensagem = conhecidos.get(erro.status_code, ("erro_http", str(erro.detail)))
        return resposta_de_erro(erro.status_code, codigo, mensagem)

    @app.exception_handler(Exception)
    async def erro_inesperado(_: Request, erro: Exception) -> JSONResponse:
        logger.exception("erro inesperado", exc_info=erro)
        return resposta_de_erro(500, "erro_interno", "Algo deu errado do nosso lado. Tente de novo.")
