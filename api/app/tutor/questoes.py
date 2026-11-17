"""Banco de questões do tutor, carregado de data/questoes-mvp.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

LETRAS = ("A", "B", "C", "D", "E")


class QuestaoNaoEncontrada(LookupError):
    pass


@dataclass(frozen=True)
class Alternativa:
    letra: str
    texto: str
    engano_provavel: str | None


@dataclass(frozen=True)
class Questao:
    id: str
    ano: int
    numero: int
    area: str
    enunciado: str
    alternativas: tuple[Alternativa, ...]
    gabarito: str
    resolucao: str
    habilidade: str
    habilidade_descricao: str
    conceitos: tuple[str, ...]
    dificuldade_tri: float | None
    fonte: str
    url_fonte: str

    def alternativa(self, letra: str) -> Alternativa:
        for alternativa in self.alternativas:
            if alternativa.letra == letra:
                return alternativa
        raise ValueError(f"alternativa inválida: {letra}")

    @property
    def correta(self) -> Alternativa:
        return self.alternativa(self.gabarito)

    @classmethod
    def de_dicionario(cls, dados: dict) -> Questao:
        return cls(
            id=dados["id"],
            ano=dados["ano"],
            numero=dados["numero"],
            area=dados["area"],
            enunciado=dados["enunciado"],
            alternativas=tuple(
                Alternativa(a["letra"], a["texto"], a["engano_provavel"]) for a in dados["alternativas"]
            ),
            gabarito=dados["gabarito"],
            resolucao=dados["resolucao"],
            habilidade=dados["habilidade"]["codigo"],
            habilidade_descricao=dados["habilidade"]["descricao"],
            conceitos=tuple(dados["conceitos"]),
            dificuldade_tri=dados["dificuldade_tri"],
            fonte=dados["fonte"]["prova"],
            url_fonte=dados["fonte"]["url"],
        )


class BancoDeQuestoes:
    def __init__(self, questoes: list[Questao]):
        self._por_id = {q.id: q for q in questoes}

    @classmethod
    def de_arquivo(cls, caminho: Path) -> BancoDeQuestoes:
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
        return cls([Questao.de_dicionario(d) for d in dados])

    def __len__(self) -> int:
        return len(self._por_id)

    def obter(self, id_questao: str) -> Questao:
        try:
            return self._por_id[id_questao]
        except KeyError:
            raise QuestaoNaoEncontrada(id_questao) from None

    def listar(self, area: str | None = None, ano: int | None = None) -> list[Questao]:
        return [q for q in self._por_id.values() if (area is None or q.area == area) and (ano is None or q.ano == ano)]
