from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select

from .. import contas, dependencias, progresso
from ..banco import Resultado
from ..dependencias import BancoDep, TokenDep, UsuarioObrigatorio, UsuarioOpcional
from ..esquemas import Erro, QuestaoResumo
from ..esquemas_contas import (
    AtualizacaoDoPerfil,
    ConfirmacaoDeSenha,
    HabilidadeSaida,
    ProgressoSaida,
    QuestaoParaRevisar,
    ResultadoSaida,
    TrocaDeSenha,
    UsuarioSaida,
)
from ..tutor.motor import Tutor
from ..tutor.sessao import agora

rotas = APIRouter(tags=["Perfil e progresso"])
TutorDep = Annotated[Tutor, Depends(dependencias.tutor)]
SEM_LOGIN = {401: {"model": Erro, "description": "Precisa entrar na conta"}}


def _resultados(banco, usuario) -> list[Resultado]:
    return list(banco.scalars(select(Resultado).where(Resultado.usuario_id == usuario.id)))


def _resultado_saida(resultado: Resultado) -> ResultadoSaida:
    return ResultadoSaida(
        questao_id=resultado.questao_id,
        habilidade=resultado.habilidade,
        acertou=resultado.acertou,
        acertou_de_primeira=resultado.acertou_de_primeira,
        tentativas=resultado.tentativas,
        pediu_explicacao=resultado.pediu_explicacao,
        concluido_em=resultado.concluido_em,
    )


@rotas.get("/eu", summary="Dados da conta", response_model=UsuarioSaida, responses=SEM_LOGIN)
def perfil(usuario: UsuarioObrigatorio) -> UsuarioSaida:
    return UsuarioSaida.de(usuario)


@rotas.patch(
    "/eu", summary="Atualiza meta, habilidades em foco e tema", response_model=UsuarioSaida, responses=SEM_LOGIN
)
def atualizar(dados: AtualizacaoDoPerfil, usuario: UsuarioObrigatorio, banco: BancoDep) -> UsuarioSaida:
    if dados.meta_semanal is not None:
        usuario.meta_semanal = dados.meta_semanal
    if dados.habilidades_foco is not None:
        usuario.habilidades_foco = sorted(set(dados.habilidades_foco))
    if dados.tema is not None:
        usuario.tema = dados.tema
    banco.commit()
    return UsuarioSaida.de(usuario)


@rotas.put("/eu/senha", status_code=204, summary="Troca a senha", response_class=Response, responses=SEM_LOGIN)
def trocar_senha(dados: TrocaDeSenha, usuario: UsuarioObrigatorio, banco: BancoDep, token: TokenDep) -> Response:
    contas.trocar_senha(banco, usuario, dados.senha_atual, dados.nova_senha, token or "")
    return Response(status_code=204)


@rotas.delete(
    "/eu",
    status_code=204,
    summary="Apaga a conta e todo o histórico",
    description="Exige a senha. Não dá para desfazer.",
    response_class=Response,
    responses=SEM_LOGIN,
)
def apagar(dados: ConfirmacaoDeSenha, usuario: UsuarioObrigatorio, banco: BancoDep) -> Response:
    contas.apagar_conta(banco, usuario, dados.senha)
    return Response(status_code=204)


@rotas.get(
    "/eu/progresso", summary="Meta da semana, sequência e desempenho por habilidade", response_model=ProgressoSaida
)
def ver_progresso(usuario: UsuarioObrigatorio, banco: BancoDep, tutor: TutorDep) -> ProgressoSaida:
    resultados = _resultados(banco, usuario)
    hoje = progresso.dia_local(agora())
    semana = progresso.inicio_da_semana(hoje)
    recentes = sorted(resultados, key=lambda r: r.concluido_em, reverse=True)[:10]
    return ProgressoSaida(
        total_de_questoes=len(resultados),
        acertos_de_primeira=sum(r.acertou_de_primeira for r in resultados),
        sequencia_de_dias=progresso.sequencia_de_dias(resultados, hoje),
        feitas_na_semana=sum(1 for r in resultados if progresso.dia_local(r.concluido_em) >= semana),
        meta_semanal=usuario.meta_semanal,
        por_habilidade=[HabilidadeSaida(**h.__dict__) for h in progresso.por_habilidade(resultados, tutor.banco)],
        recentes=[_resultado_saida(r) for r in recentes],
    )


@rotas.get(
    "/eu/revisar",
    summary="Questões para revisar",
    description="Questões cuja última tentativa não foi um acerto de primeira.",
    response_model=list[QuestaoParaRevisar],
    responses=SEM_LOGIN,
)
def revisar(usuario: UsuarioObrigatorio, banco: BancoDep, tutor: TutorDep) -> list[QuestaoParaRevisar]:
    pendentes = progresso.questoes_para_revisar(_resultados(banco, usuario))
    saida = []
    for resultado in pendentes:
        try:
            questao = tutor.banco.obter(resultado.questao_id)
        except LookupError:
            continue  # questão que saiu do banco
        saida.append(
            QuestaoParaRevisar(questao=QuestaoResumo.de(questao), ultima_tentativa=_resultado_saida(resultado))
        )
    return saida


@rotas.get(
    "/recomendacoes",
    tags=["Questões"],
    summary="Sugere questões para estudar (usado no modo foco)",
    description=(
        "Com conta: primeiro as questões para revisar, depois as nunca feitas das habilidades em foco. "
        "Sem conta: questões das habilidades informadas, ou sorteadas."
    ),
    response_model=list[QuestaoResumo],
)
def recomendacoes(
    usuario: UsuarioOpcional,
    banco: BancoDep,
    tutor: TutorDep,
    quantidade: Annotated[int, Query(ge=1, le=30)] = 5,
    habilidades: Annotated[
        str | None, Query(description="Códigos separados por vírgula", examples=["MT-H16,CN-H5"])
    ] = None,
) -> list[QuestaoResumo]:
    foco = [h.strip() for h in habilidades.split(",") if h.strip()] if habilidades else None
    if usuario is not None:
        escolhidas = progresso.recomendar(
            tutor.banco, _resultados(banco, usuario), foco or usuario.habilidades_foco, quantidade
        )
    else:
        escolhidas = progresso.recomendar(tutor.banco, [], foco or [], quantidade)
    return [QuestaoResumo.de(q) for q in escolhidas]
