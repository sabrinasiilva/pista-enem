from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import dependencias
from ..banco import Usuario
from ..dependencias import BancoDep, LimiteAtingido, UsuarioOpcional, limite_de_ia, limite_de_sessoes
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
from ..progresso import registrar_resultado
from ..sessoes import RepositorioDeSessoes, SessaoNaoEncontrada
from ..tutor.motor import Tutor
from ..tutor.sessao import Sessao

rotas = APIRouter(prefix="/sessoes", tags=["Sessões"])

TutorDep = Annotated[Tutor, Depends(dependencias.tutor)]
SessoesDep = Annotated[RepositorioDeSessoes, Depends(dependencias.sessoes)]

NAO_ENCONTRADA = {404: {"model": Erro, "description": "Sessão não encontrada ou expirada"}}
CONFLITO = {409: {"model": Erro, "description": "Ação não permitida no estado atual da sessão"}}


def _obter(sessoes: RepositorioDeSessoes, sessao_id: str, usuario: Usuario | None):
    """A sessão de uma conta só é acessível pela própria conta; para os outros, ela não existe."""
    sessao, trava = sessoes.obter(sessao_id)
    if sessao.usuario_id is not None and (usuario is None or usuario.id != sessao.usuario_id):
        raise SessaoNaoEncontrada(sessao_id)
    return sessao, trava


def _contar_acao(sessao: Sessao, request: Request) -> None:
    sessao.acoes_com_ia += 1
    if sessao.acoes_com_ia > request.app.state.config.limite_ia_por_sessao:
        raise LimiteAtingido("Esta questão chegou ao limite de mensagens. Abra a questão de novo para continuar.")


def _gravar_se_terminou(sessao: Sessao, tutor: Tutor, banco: Session) -> None:
    """Quando a resposta é revelada, grava o resultado no histórico da conta (uma única vez)."""
    if sessao.usuario_id is None or sessao.resultado_gravado or not sessao.resposta_revelada:
        return
    registrar_resultado(banco, sessao, tutor.banco.obter(sessao.questao_id))
    sessao.resultado_gravado = True


@rotas.post(
    "",
    status_code=201,
    dependencies=[Depends(limite_de_sessoes)],
    summary="Abre uma sessão para uma questão",
    description="Com o token de uma conta, o resultado entra no histórico do aluno. Sem token, a sessão é anônima.",
    response_model=SessaoSaida,
    responses={404: {"model": Erro, "description": "Questão não encontrada"}},
)
def criar(dados: NovaSessao, tutor: TutorDep, sessoes: SessoesDep, usuario: UsuarioOpcional) -> SessaoSaida:
    sessao = tutor.nova_sessao(dados.questao_id)
    sessao.usuario_id = usuario.id if usuario else None
    sessoes.guardar(sessao)
    return SessaoSaida.de(sessao, tutor.banco.obter(sessao.questao_id).gabarito)


@rotas.get(
    "/{sessao_id}",
    summary="Mostra o estado e as mensagens da sessão",
    response_model=SessaoSaida,
    responses=NAO_ENCONTRADA,
)
def obter(sessao_id: str, tutor: TutorDep, sessoes: SessoesDep, usuario: UsuarioOpcional) -> SessaoSaida:
    sessao, _ = _obter(sessoes, sessao_id, usuario)
    return SessaoSaida.de(sessao, tutor.banco.obter(sessao.questao_id).gabarito)


@rotas.post(
    "/{sessao_id}/respostas",
    dependencies=[Depends(limite_de_ia)],
    summary="Envia a alternativa marcada",
    description=(
        "O código compara com o gabarito e decide o próximo estado: `concluida` se acertou, "
        "senão `pista_1`, `pista_2` e, no terceiro erro, `explicacao`. "
        "O gabarito só volta quando a resposta é revelada."
    ),
    response_model=RespostaSaida,
    responses={**NAO_ENCONTRADA, **CONFLITO},
)
async def responder(
    request: Request,
    sessao_id: str,
    dados: RespostaEntrada,
    tutor: TutorDep,
    sessoes: SessoesDep,
    usuario: UsuarioOpcional,
    banco: BancoDep,
) -> RespostaSaida:
    sessao, trava = _obter(sessoes, sessao_id, usuario)
    _contar_acao(sessao, request)
    async with trava:
        resultado = await tutor.responder(sessao, dados.alternativa)
        await run_in_threadpool(_gravar_se_terminou, sessao, tutor, banco)
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
    dependencies=[Depends(limite_de_ia)],
    summary="Conversa com o tutor (streaming)",
    description=(
        'Resposta em Server-Sent Events. Cada evento `trecho` traz `{"texto": ...}`; '
        'o evento final `fim` traz `{"estado": ...}`. Enquanto a resposta está protegida, '
        "a mensagem é verificada inteira antes do primeiro trecho."
    ),
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}, **NAO_ENCONTRADA},
)
async def conversar(
    request: Request,
    sessao_id: str,
    dados: MensagemEntrada,
    tutor: TutorDep,
    sessoes: SessoesDep,
    usuario: UsuarioOpcional,
) -> StreamingResponse:
    sessao, trava = _obter(sessoes, sessao_id, usuario)  # 404 antes de abrir o streaming
    _contar_acao(sessao, request)

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
    dependencies=[Depends(limite_de_ia)],
    summary="Pede a explicação completa",
    description="Só depois de pelo menos uma tentativa, e com `confirmar: true`. Revela o gabarito.",
    response_model=ExplicacaoSaida,
    responses={**NAO_ENCONTRADA, **CONFLITO},
)
async def explicar(
    request: Request,
    sessao_id: str,
    dados: ExplicacaoEntrada,
    tutor: TutorDep,
    sessoes: SessoesDep,
    usuario: UsuarioOpcional,
    banco: BancoDep,
) -> ExplicacaoSaida:
    sessao, trava = _obter(sessoes, sessao_id, usuario)
    _contar_acao(sessao, request)
    async with trava:
        mensagem = await tutor.explicar(sessao, dados.confirmar)
        await run_in_threadpool(_gravar_se_terminou, sessao, tutor, banco)
    return ExplicacaoSaida(
        estado=sessao.estado,
        gabarito=tutor.banco.obter(sessao.questao_id).gabarito,
        mensagem=MensagemSaida.de(mensagem),
    )


def _evento(nome: str, dados: dict) -> str:
    return f"event: {nome}\ndata: {json.dumps(dados, ensure_ascii=False)}\n\n"
