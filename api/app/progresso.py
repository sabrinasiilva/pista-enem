"""Progresso do aluno: meta da semana, sequência de dias, habilidades, erros e recomendações."""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone

from .banco import Resultado
from .tutor.questoes import BancoDeQuestoes, Questao

# horário de Brasília (o Brasil não tem horário de verão desde 2019)
FUSO = timezone(timedelta(hours=-3))


def dia_local(momento: datetime) -> date:
    if momento.tzinfo is None:  # o SQLite devolve datas sem fuso; elas foram gravadas em UTC
        momento = momento.replace(tzinfo=UTC)
    return momento.astimezone(FUSO).date()


def inicio_da_semana(hoje: date) -> date:
    return hoje - timedelta(days=hoje.weekday())  # segunda-feira


def sequencia_de_dias(resultados: Sequence[Resultado], hoje: date) -> int:
    """Dias seguidos com pelo menos uma questão. Se hoje ainda não teve, conta até ontem."""
    dias = {dia_local(r.concluido_em) for r in resultados}
    dia = hoje if hoje in dias else hoje - timedelta(days=1)
    total = 0
    while dia in dias:
        total += 1
        dia -= timedelta(days=1)
    return total


@dataclass(frozen=True)
class Habilidade:
    codigo: str
    descricao: str
    feitas: int
    acertos_de_primeira: int


def por_habilidade(resultados: Sequence[Resultado], banco: BancoDeQuestoes) -> list[Habilidade]:
    descricoes = {q.habilidade: q.habilidade_descricao for q in banco.listar()}
    feitas: dict[str, int] = defaultdict(int)
    acertos: dict[str, int] = defaultdict(int)
    for resultado in resultados:
        feitas[resultado.habilidade] += 1
        acertos[resultado.habilidade] += resultado.acertou_de_primeira
    return [
        Habilidade(codigo, descricoes.get(codigo, ""), feitas[codigo], acertos[codigo])
        for codigo in sorted(feitas, key=lambda c: int(c[1:]))
    ]


def ultimo_por_questao(resultados: Sequence[Resultado]) -> dict[str, Resultado]:
    ultimos: dict[str, Resultado] = {}
    for resultado in sorted(resultados, key=lambda r: r.concluido_em):
        ultimos[resultado.questao_id] = resultado
    return ultimos


def questoes_para_revisar(resultados: Sequence[Resultado]) -> list[Resultado]:
    """Questões cuja última tentativa não foi um acerto de primeira, da mais recente para a mais antiga."""
    pendentes = [r for r in ultimo_por_questao(resultados).values() if not r.acertou_de_primeira]
    return sorted(pendentes, key=lambda r: r.concluido_em, reverse=True)


def recomendar(
    banco: BancoDeQuestoes,
    resultados: Sequence[Resultado],
    habilidades_foco: Sequence[str],
    quantidade: int,
    semente: int | None = None,
) -> list[Questao]:
    """Escolhe questões nesta ordem de prioridade:
    1. erradas que ainda não foram refeitas com acerto de primeira;
    2. nunca feitas, das habilidades em foco;
    3. nunca feitas, de outras habilidades;
    4. já acertadas (só para completar a quantidade).
    """
    sorteio = random.Random(semente)  # noqa: S311 - sorteio de questões, não é uso criptográfico
    ultimos = ultimo_por_questao(resultados)
    revisar = {r.questao_id for r in questoes_para_revisar(resultados)}
    foco = set(habilidades_foco)

    def prioridade(questao: Questao) -> int:
        if questao.id in revisar:
            return 0
        if questao.id not in ultimos:
            return 1 if questao.habilidade in foco else 2
        return 3

    questoes = banco.listar()
    sorteio.shuffle(questoes)
    return sorted(questoes, key=prioridade)[:quantidade]


def registrar_resultado(sessao_do_banco, sessao_do_tutor, questao: Questao) -> Resultado:
    """Grava como terminou uma questão. Chamado uma vez, quando a resposta é revelada."""
    from .tutor.estados import Estado

    acertou = sessao_do_tutor.estado == Estado.CONCLUIDA
    resultado = Resultado(
        usuario_id=sessao_do_tutor.usuario_id,
        questao_id=questao.id,
        habilidade=questao.habilidade,
        acertou=acertou,
        acertou_de_primeira=acertou and len(sessao_do_tutor.tentativas) == 1,
        tentativas=len(sessao_do_tutor.tentativas),
        pediu_explicacao=sessao_do_tutor.estado == Estado.EXPLICACAO,
    )
    sessao_do_banco.add(resultado)
    sessao_do_banco.commit()
    return resultado
