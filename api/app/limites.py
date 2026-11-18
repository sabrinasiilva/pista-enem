"""Limites de uso: tentativas de login, requisições por IP e por sessão, e cota diária da IA.

Ficam em memória: valem para a instância que está rodando (o plano gratuito tem uma só).
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator, Callable, Sequence
from datetime import date, datetime, timedelta, timezone

from .tutor.ia import ClienteDeIA, ErroDaIA, RespostaDaIA, Turno

logger = logging.getLogger(__name__)
FUSO = timezone(timedelta(hours=-3))


class LimiteDeTentativas:
    """Janela deslizante: no máximo `maximo` eventos por chave a cada `janela_em_segundos`."""

    def __init__(self, maximo: int = 5, janela_em_segundos: float = 15 * 60):
        self.maximo = maximo
        self.janela = janela_em_segundos
        self._falhas: dict[str, deque[float]] = defaultdict(deque)

    def _limpar(self, chave: str, agora: float) -> deque[float]:
        falhas = self._falhas[chave]
        while falhas and agora - falhas[0] > self.janela:
            falhas.popleft()
        return falhas

    def bloqueado(self, *chaves: str) -> bool:
        agora = time.monotonic()
        return any(len(self._limpar(chave, agora)) >= self.maximo for chave in chaves)

    def registrar_falha(self, *chaves: str) -> None:
        agora = time.monotonic()
        for chave in chaves:
            self._limpar(chave, agora).append(agora)

    def zerar(self, *chaves: str) -> None:
        for chave in chaves:
            self._falhas.pop(chave, None)


class LimiteDeRequisicoes(LimiteDeTentativas):
    """Conta toda requisição (não só falhas)."""

    def permitir(self, *chaves: str) -> bool:
        if self.bloqueado(*chaves):
            return False
        self.registrar_falha(*chaves)
        return True


def hoje_em_brasilia() -> date:
    return datetime.now(FUSO).date()


class CotaDiaria:
    """Quantas chamadas à IA podem ser feitas por dia (horário de Brasília). Protege o plano gratuito."""

    def __init__(self, limite: int, relogio: Callable[[], date] = hoje_em_brasilia):
        self.limite = limite
        self._relogio = relogio
        self._dia = relogio()
        self.usadas = 0

    def _virar_o_dia(self) -> None:
        hoje = self._relogio()
        if hoje != self._dia:
            self._dia, self.usadas = hoje, 0

    @property
    def esgotada(self) -> bool:
        self._virar_o_dia()
        return self.usadas >= self.limite

    def consumir(self) -> bool:
        if self.esgotada:
            return False
        self.usadas += 1
        if self.usadas == self.limite:
            logger.warning("cota diária da IA esgotada (%d chamadas); o tutor segue no plano B até amanhã", self.limite)
        return True


class IAComCota:
    """Envolve o cliente da IA: sem cota, levanta ErroDaIA e o tutor usa o plano B (não dá erro para o aluno)."""

    def __init__(self, ia: ClienteDeIA, cota: CotaDiaria):
        self._ia = ia
        self.cota = cota

    async def gerar(self, sistema: str, conversa: Sequence[Turno]) -> RespostaDaIA:
        if not self.cota.consumir():
            raise ErroDaIA("cota diária esgotada")
        return await self._ia.gerar(sistema, conversa)

    async def gerar_em_trechos(self, sistema: str, conversa: Sequence[Turno]) -> AsyncIterator[str]:
        if not self.cota.consumir():
            raise ErroDaIA("cota diária esgotada")
        async for trecho in self._ia.gerar_em_trechos(sistema, conversa):
            yield trecho
