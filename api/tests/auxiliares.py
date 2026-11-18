"""Auxiliares dos testes: questão de exemplo e IA simulada."""

from __future__ import annotations

from collections.abc import Sequence

from app.tutor.ia import ErroDaIA, RespostaDaIA, Turno
from app.tutor.questoes import Alternativa, Questao


def questao_exemplo(**mudancas) -> Questao:
    dados = {
        "id": "2099-140",
        "ano": 2099,
        "numero": 140,
        "area": "matematica",
        "enunciado": "Um operário cobra R\\$ 120,00 por hora e trabalha 8 horas por dia. Quanto ele recebe em um dia?",
        "alternativas": (
            Alternativa("A", "R\\$ 15,00", "Dividiu o preço pelas horas: $120 \\div 8 = 15$."),
            Alternativa("B", "R\\$ 128,00", "Somou em vez de multiplicar: $120 + 8 = 128$."),
            Alternativa("C", "R\\$ 960,00", None),
            Alternativa("D", "R\\$ 1 200,00", "Multiplicou por 10 horas em vez de 8."),
            Alternativa("E", "R\\$ 9 600,00", "Errou a posição da vírgula: $960 \\times 10$."),
        ),
        "gabarito": "C",
        "resolucao": "Multiplique o preço por hora pelas horas: $120 \\times 8 = 960$.\nAlternativa C.",
        "habilidade": "H3",
        "habilidade_descricao": "Resolver situação-problema envolvendo conhecimentos numéricos.",
        "conceitos": ("multiplicação",),
        "dificuldade_tri": 0.5,
        "fonte": "ENEM 2099, questão de exemplo",
        "url_fonte": "https://download.inep.gov.br/exemplo.pdf",
    }
    dados.update(mudancas)
    return Questao(**dados)


class IAFalsa:
    """IA simulada: devolve as respostas da lista, em ordem. Um item Exception vira falha."""

    def __init__(self, *respostas: str | Exception):
        self.respostas = list(respostas)
        self.chamadas: list[tuple[str, list[Turno]]] = []

    def _proxima(self, sistema: str, conversa: Sequence[Turno]) -> str:
        self.chamadas.append((sistema, list(conversa)))
        if not self.respostas:
            raise AssertionError("a IA foi chamada mais vezes do que o esperado")
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    async def gerar(self, sistema: str, conversa: Sequence[Turno]) -> RespostaDaIA:
        return RespostaDaIA(self._proxima(sistema, conversa), "modelo-falso", 10)

    async def gerar_em_trechos(self, sistema: str, conversa: Sequence[Turno]):
        texto = self._proxima(sistema, conversa)
        for palavra in texto.split(" "):
            yield palavra + " "


FALHA = ErroDaIA("falhou")
