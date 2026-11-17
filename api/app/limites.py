"""Limite de tentativas de login, contra quem tenta adivinhar senhas.

Fica em memória por enquanto; o limite geral de requisições é da Fase 9.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class LimiteDeTentativas:
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
