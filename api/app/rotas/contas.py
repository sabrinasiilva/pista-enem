from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from .. import contas, dependencias
from ..dependencias import BancoDep, TokenDep, UsuarioObrigatorio
from ..esquemas import Erro
from ..esquemas_contas import AcessoSaida, Cadastro, Login, Recuperacao, UsuarioSaida
from ..limites import LimiteDeTentativas

rotas = APIRouter(prefix="/contas", tags=["Contas"])
LimiteDep = Annotated[LimiteDeTentativas, Depends(dependencias.limite_de_login)]

MUITAS_TENTATIVAS = {429: {"model": Erro, "description": "Tentativas demais; espere 15 minutos"}}


def _chaves(request: Request, apelido: str) -> tuple[str, str]:
    return f"apelido:{apelido.strip().lower()}", f"ip:{dependencias.ip_do_cliente(request)}"


def _saida(entrada: contas.Entrada) -> AcessoSaida:
    return AcessoSaida(
        token=entrada.token,
        usuario=UsuarioSaida.de(entrada.usuario),
        codigo_de_recuperacao=entrada.codigo_de_recuperacao,
    )


@rotas.post(
    "",
    status_code=201,
    summary="Cria uma conta (sem dados pessoais)",
    description=(
        "Só apelido e senha. A resposta traz um **código de recuperação**, que só aparece agora: "
        "é a única forma de recuperar a conta se a senha for esquecida."
    ),
    response_model=AcessoSaida,
    responses={409: {"model": Erro, "description": "Apelido em uso"}},
)
def cadastrar(dados: Cadastro, banco: BancoDep) -> AcessoSaida:
    return _saida(
        contas.criar_conta(banco, dados.apelido, dados.senha, dados.meta_semanal, sorted(set(dados.habilidades_foco)))
    )


@rotas.post(
    "/entrar",
    summary="Entra na conta",
    response_model=AcessoSaida,
    responses={401: {"model": Erro}, **MUITAS_TENTATIVAS},
)
def entrar(dados: Login, request: Request, banco: BancoDep, limite: LimiteDep) -> AcessoSaida:
    chaves = _chaves(request, dados.apelido)
    if limite.bloqueado(*chaves):
        raise contas.ErroDeConta(429, "tentativas_demais", "Muitas tentativas. Espere 15 minutos e tente de novo.")
    try:
        entrada = contas.entrar(banco, dados.apelido, dados.senha)
    except contas.ErroDeConta:
        limite.registrar_falha(*chaves)
        raise
    limite.zerar(chaves[0])
    return _saida(entrada)


@rotas.post(
    "/recuperar",
    summary="Troca a senha com o código de recuperação",
    description="O código usado deixa de valer e um novo é devolvido. Os outros aparelhos são desconectados.",
    response_model=AcessoSaida,
    responses={401: {"model": Erro}, **MUITAS_TENTATIVAS},
)
def recuperar(dados: Recuperacao, request: Request, banco: BancoDep, limite: LimiteDep) -> AcessoSaida:
    chaves = _chaves(request, dados.apelido)
    if limite.bloqueado(*chaves):
        raise contas.ErroDeConta(429, "tentativas_demais", "Muitas tentativas. Espere 15 minutos e tente de novo.")
    try:
        entrada = contas.recuperar(banco, dados.apelido, dados.codigo_de_recuperacao, dados.nova_senha)
    except contas.ErroDeConta as erro:
        if erro.status == 401:
            limite.registrar_falha(*chaves)
        raise
    return _saida(entrada)


@rotas.post("/sair", status_code=204, summary="Sai da conta neste aparelho", response_class=Response)
def sair(_: UsuarioObrigatorio, banco: BancoDep, token: TokenDep) -> Response:
    if token:
        contas.sair(banco, token)
    return Response(status_code=204)
