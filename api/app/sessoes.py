"""Guarda as sessões em memória enquanto o banco de dados não chega (Fase 5).

Cada sessão tem um lock próprio, para que duas requisições ao mesmo tempo
não mudem o estado dela em paralelo.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import timedelta

from .tutor.sessao import Sessao, agora


class SessaoNaoEncontrada(LookupError):
    pass


@dataclass
class _Entrada:
    sessao: Sessao
    trava: asyncio.Lock = field(default_factory=asyncio.Lock)


class RepositorioDeSessoes:
    def __init__(self, validade: timedelta = timedelta(hours=24), maximo: int = 10_000):
        self.validade = validade
        self.maximo = maximo
        self._entradas: dict[str, _Entrada] = {}

    def __len__(self) -> int:
        return len(self._entradas)

    def guardar(self, sessao: Sessao) -> None:
        self._limpar()
        if len(self._entradas) >= self.maximo:
            # descarta a sessão mais antiga para não crescer sem limite
            mais_antiga = min(self._entradas.values(), key=lambda e: e.sessao.criada_em)
            del self._entradas[mais_antiga.sessao.id]
        self._entradas[sessao.id] = _Entrada(sessao)

    def obter(self, id_sessao: str) -> tuple[Sessao, asyncio.Lock]:
        entrada = self._entradas.get(id_sessao)
        if entrada is None or self._expirada(entrada.sessao):
            raise SessaoNaoEncontrada(id_sessao)
        return entrada.sessao, entrada.trava

    def _expirada(self, sessao: Sessao) -> bool:
        return agora() - sessao.criada_em > self.validade

    def _limpar(self) -> None:
        for id_sessao in [i for i, e in self._entradas.items() if self._expirada(e.sessao)]:
            del self._entradas[id_sessao]
