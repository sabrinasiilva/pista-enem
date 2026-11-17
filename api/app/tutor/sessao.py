"""Sessão anônima de uma questão e suas mensagens."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from .estados import ESTADOS_FINAIS, Estado

Papel = Literal["aluno", "tutor"]
# o que aconteceu para a mensagem do tutor não vir direto da IA
Protecao = Literal["entrada", "pedido_de_resposta", "saida", "plano_b"]


def agora() -> datetime:
    return datetime.now(UTC)


@dataclass
class Mensagem:
    papel: Papel
    texto: str
    estado: Estado
    protecao: Protecao | None = None
    vazamentos_bloqueados: int = 0
    modelo: str | None = None
    tokens: int | None = None
    criada_em: datetime = field(default_factory=agora)


@dataclass
class Sessao:
    questao_id: str
    versao_prompt: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    estado: Estado = Estado.RESPONDENDO
    tentativas: list[str] = field(default_factory=list)
    mensagens: list[Mensagem] = field(default_factory=list)
    criada_em: datetime = field(default_factory=agora)

    @property
    def resposta_revelada(self) -> bool:
        return self.estado in ESTADOS_FINAIS

    def registrar(self, mensagem: Mensagem) -> Mensagem:
        self.mensagens.append(mensagem)
        return mensagem
