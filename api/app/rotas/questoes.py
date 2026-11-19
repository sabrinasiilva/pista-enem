from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response

from .. import dependencias
from ..esquemas import Erro, QuestaoDetalhe, QuestaoResumo
from ..tutor.motor import Tutor
from ..tutor.questoes import QuestaoNaoEncontrada

rotas = APIRouter(prefix="/questoes", tags=["Questões"])

TutorDep = Annotated[Tutor, Depends(dependencias.tutor)]


@rotas.get("", summary="Lista as questões", response_model=list[QuestaoResumo])
def listar(
    tutor: TutorDep,
    area: Annotated[str | None, Query(description="Área do conhecimento", examples=["matematica"])] = None,
    ano: Annotated[int | None, Query(ge=2009, le=2100, description="Ano da prova", examples=[2023])] = None,
) -> list[QuestaoResumo]:
    questoes = sorted(tutor.banco.listar(area=area, ano=ano), key=lambda q: (q.ano, q.numero))
    return [QuestaoResumo.de(q) for q in questoes]


@rotas.get(
    "/{questao_id}/parecidas",
    summary="Questões parecidas para praticar",
    description="Mesma área, assunto e conceitos próximos; a mesma habilidade conta a favor.",
    response_model=list[QuestaoResumo],
    responses={404: {"model": Erro}},
)
def parecidas(
    questao_id: str, tutor: TutorDep, quantidade: Annotated[int, Query(ge=1, le=10)] = 3
) -> list[QuestaoResumo]:
    questao = tutor.banco.obter(questao_id)
    return [QuestaoResumo.de(q) for q in tutor.busca.parecidas(questao, quantidade)]


@rotas.get(
    "/{questao_id}",
    summary="Mostra uma questão para resolver",
    description="Enunciado e alternativas. O gabarito nunca é enviado aqui.",
    response_model=QuestaoDetalhe,
    responses={404: {"model": Erro}},
)
def obter(questao_id: str, tutor: TutorDep) -> QuestaoDetalhe:
    return QuestaoDetalhe.de(tutor.banco.obter(questao_id))


@rotas.get(
    "/{questao_id}/figuras/{numero}",
    summary="Figura da questão (PNG)",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}, 404: {"model": Erro}},
)
def figura(questao_id: str, tutor: TutorDep, numero: Annotated[int, Path(ge=1, le=10)]) -> Response:
    questao = tutor.banco.obter(questao_id)
    imagens = tutor.banco.imagens(questao)
    if numero > len(imagens):
        raise QuestaoNaoEncontrada(f"{questao_id}, figura {numero}")
    # a figura da prova não muda: o navegador pode guardar por um dia
    return Response(imagens[numero - 1], media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})
