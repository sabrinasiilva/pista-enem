from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from .. import dependencias
from ..esquemas import (
    Erro,
    ExplicacaoEntrada,
    ExplicacaoSaida,
    MensagemEntrada,
    MensagemSaida,
    NovaSessao,
    RespostaEntrada,
    RespostaSaida,
    SessaoSaida,
)
from ..sessoes import RepositorioDeSessoes
from ..tutor.motor import Tutor

rotas = APIRouter(prefix="/sessoes", tags=["Sessões"])

TutorDep = Annotated[Tutor, Depends(dependencias.tutor)]
SessoesDep = Annotated[RepositorioDeSessoes, Depends(dependencias.sessoes)]

NAO_ENCONTRADA = {404: {"model": Erro, "description": "Sessão não encontrada ou expirada"}}
CONFLITO = {409: {"model": Erro, "description": "Ação não permitida no estado atual da sessão"}}


@rotas.post(
    "",
    status_code=201,
    summary="Abre uma sessão anônima para uma questão",
    response_model=SessaoSaida,
    responses={404: {"model": Erro, "description": "Questão não encontrada"}},
)
def criar(dados: NovaSessao, tutor: TutorDep, sessoes: SessoesDep) -> SessaoSaida:
    sessao = tutor.nova_sessao(dados.questao_id)
    sessoes.guardar(sessao)
    return SessaoSaida.de(sessao, tutor.banco.obter(sessao.questao_id).gabarito)


@rotas.get(
    "/{sessao_id}",
    summary="Mostra o estado e as mensagens da sessão",
    response_model=SessaoSaida,
    responses=NAO_ENCONTRADA,
)
def obter(sessao_id: str, tutor: TutorDep, sessoes: SessoesDep) -> SessaoSaida:
    sessao, _ = sessoes.obter(sessao_id)
    return SessaoSaida.de(sessao, tutor.banco.obter(sessao.questao_id).gabarito)


@rotas.post(
    "/{sessao_id}/respostas",
    summary="Envia a alternativa marcada",
    description=(
        "O código compara com o gabarito e decide o próximo estado: `concluida` se acertou, "
        "senão `pista_1`, `pista_2` e, no terceiro erro, `explicacao`. "
        "O gabarito só volta quando a resposta é revelada."
    ),
    response_model=RespostaSaida,
    responses={**NAO_ENCONTRADA, **CONFLITO},
)
async def responder(sessao_id: str, dados: RespostaEntrada, tutor: TutorDep, sessoes: SessoesDep) -> RespostaSaida:
    sessao, trava = sessoes.obter(sessao_id)
    async with trava:
        resultado = await tutor.responder(sessao, dados.alternativa)
    gabarito = tutor.banco.obter(sessao.questao_id).gabarito
    return RespostaSaida(
        acertou=resultado.acertou,
        estado=resultado.estado,
        tentativas=sessao.tentativas,
        gabarito=gabarito if sessao.resposta_revelada else None,
        mensagem=MensagemSaida.de(resultado.mensagem),
    )


@rotas.post(
    "/{sessao_id}/mensagens",
    summary="Conversa com o tutor (streaming)",
    description=(
        'Resposta em Server-Sent Events. Cada evento `trecho` traz `{"texto": ...}`; '
        'o evento final `fim` traz `{"estado": ...}`. Enquanto a resposta está protegida, '
        "a mensagem é verificada inteira antes do primeiro trecho."
    ),
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}, **NAO_ENCONTRADA},
)
async def conversar(sessao_id: str, dados: MensagemEntrada, tutor: TutorDep, sessoes: SessoesDep) -> StreamingResponse:
    sessao, trava = sessoes.obter(sessao_id)  # 404 antes de abrir o streaming

    async def eventos() -> AsyncIterator[str]:
        async with trava:
            async for trecho in tutor.conversar_em_trechos(sessao, dados.texto):
                yield _evento("trecho", {"texto": trecho})
            yield _evento("fim", {"estado": sessao.estado.value})

    return StreamingResponse(
        eventos(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@rotas.post(
    "/{sessao_id}/explicacao",
    summary="Pede a explicação completa",
    description="Só depois de pelo menos uma tentativa, e com `confirmar: true`. Revela o gabarito.",
    response_model=ExplicacaoSaida,
    responses={**NAO_ENCONTRADA, **CONFLITO},
)
async def explicar(sessao_id: str, dados: ExplicacaoEntrada, tutor: TutorDep, sessoes: SessoesDep) -> ExplicacaoSaida:
    sessao, trava = sessoes.obter(sessao_id)
    async with trava:
        mensagem = await tutor.explicar(sessao, dados.confirmar)
    return ExplicacaoSaida(
        estado=sessao.estado,
        gabarito=tutor.banco.obter(sessao.questao_id).gabarito,
        mensagem=MensagemSaida.de(mensagem),
    )


def _evento(nome: str, dados: dict) -> str:
    return f"event: {nome}\ndata: {json.dumps(dados, ensure_ascii=False)}\n\n"
