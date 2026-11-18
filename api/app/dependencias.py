"""Dependências das rotas: tutor, sessões, banco de dados e conta do aluno."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from .banco import Usuario
from .contas import ErroDeConta, usuario_do_token
from .limites import LimiteDeRequisicoes, LimiteDeTentativas
from .sessoes import RepositorioDeSessoes
from .tutor.motor import Tutor


def tutor(request: Request) -> Tutor:
    return request.app.state.tutor


def sessoes(request: Request) -> RepositorioDeSessoes:
    return request.app.state.sessoes


def limite_de_login(request: Request) -> LimiteDeTentativas:
    return request.app.state.limite_de_login


class LimiteAtingido(Exception):
    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


def ip_do_cliente(request: Request) -> str:
    """IP real do aluno. Atrás do Render, vem do cabeçalho que a Cloudflare define."""
    cabecalho = request.app.state.config.cabecalho_ip_do_cliente
    if cabecalho and (valor := request.headers.get(cabecalho)):
        return valor.strip()
    return request.client.host if request.client else "desconhecido"


def exigir(limite: LimiteDeRequisicoes, chave: str, mensagem: str) -> None:
    if not limite.permitir(chave):
        raise LimiteAtingido(mensagem)


def limite_de_ia(request: Request) -> None:
    """Limite por IP das ações que chamam a IA (responder, conversar, explicar)."""
    exigir(
        request.app.state.limite_ia_por_ip,
        ip_do_cliente(request),
        "Muitas mensagens em pouco tempo. Espere alguns minutos e tente de novo.",
    )


def limite_de_sessoes(request: Request) -> None:
    exigir(
        request.app.state.limite_sessoes_por_ip,
        ip_do_cliente(request),
        "Muitas questões abertas em pouco tempo. Espere alguns minutos e tente de novo.",
    )


def banco(request: Request) -> Iterator[Session]:
    with request.app.state.fabrica_de_sessoes() as sessao:
        yield sessao


def token(authorization: Annotated[str | None, Header(include_in_schema=False)] = None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return None


BancoDep = Annotated[Session, Depends(banco)]
TokenDep = Annotated[str | None, Depends(token)]


def usuario_opcional(sessao_do_banco: BancoDep, token_recebido: TokenDep) -> Usuario | None:
    """Conta do aluno, se ele mandou um token válido. Sem token, segue anônimo."""
    if not token_recebido:
        return None
    usuario = usuario_do_token(sessao_do_banco, token_recebido)
    if usuario is None:
        raise ErroDeConta(401, "sessao_expirada", "Sua sessão expirou. Entre de novo.")
    return usuario


def usuario_obrigatorio(usuario: Annotated[Usuario | None, Depends(usuario_opcional)]) -> Usuario:
    if usuario is None:
        raise ErroDeConta(401, "login_necessario", "Entre na sua conta para continuar.")
    return usuario


UsuarioOpcional = Annotated[Usuario | None, Depends(usuario_opcional)]
UsuarioObrigatorio = Annotated[Usuario, Depends(usuario_obrigatorio)]
