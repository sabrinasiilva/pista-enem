"""Máquina de estados da sessão.

    respondendo ──acertou──▶ concluida
         │errou
         ▼
      pista_1 ──acertou──▶ concluida
         │errou              ▲
         ▼                   │acertou
      pista_2 ───────────────┘
         │errou (ou pediu a explicação em pista_1/pista_2, com confirmação)
         ▼
     explicacao

A resposta correta só pode aparecer em `explicacao` e `concluida`.
"""

from __future__ import annotations

from enum import StrEnum


class Estado(StrEnum):
    RESPONDENDO = "respondendo"
    PISTA_1 = "pista_1"
    PISTA_2 = "pista_2"
    EXPLICACAO = "explicacao"
    CONCLUIDA = "concluida"


PROXIMO_APOS_ERRO = {
    Estado.RESPONDENDO: Estado.PISTA_1,
    Estado.PISTA_1: Estado.PISTA_2,
    Estado.PISTA_2: Estado.EXPLICACAO,
}

ESTADOS_PROTEGIDOS = frozenset({Estado.RESPONDENDO, Estado.PISTA_1, Estado.PISTA_2})
ESTADOS_FINAIS = frozenset({Estado.EXPLICACAO, Estado.CONCLUIDA})


class TransicaoInvalida(Exception):
    """Ação que não é permitida no estado atual da sessão."""

    def __init__(self, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


def apos_resposta(estado: Estado, acertou: bool) -> Estado:
    if estado in ESTADOS_FINAIS:
        raise TransicaoInvalida("sessao_encerrada", "Esta questão já foi encerrada.")
    return Estado.CONCLUIDA if acertou else PROXIMO_APOS_ERRO[estado]


def apos_pedido_de_explicacao(estado: Estado, confirmado: bool) -> Estado:
    if estado == Estado.RESPONDENDO:
        raise TransicaoInvalida("tente_antes", "Marque uma alternativa pelo menos uma vez antes de pedir a explicação.")
    if estado in ESTADOS_FINAIS:
        raise TransicaoInvalida("sessao_encerrada", "Esta questão já foi encerrada.")
    if not confirmado:
        raise TransicaoInvalida(
            "confirmacao_necessaria", "Confirme que quer ver a resposta antes de pedir a explicação."
        )
    return Estado.EXPLICACAO
