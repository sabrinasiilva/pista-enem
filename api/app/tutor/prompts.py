"""Carrega os prompts versionados de prompts/ e monta as instruções de cada momento."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .estados import ESTADOS_PROTEGIDOS, Estado
from .questoes import Questao
from .sessao import Sessao

SECOES_OBRIGATORIAS = frozenset(
    {"sistema", "regra_protegida", "regra_livre", "pista_1", "pista_2", "explicacao", "acerto", "conversa", "reforco"}
)

# momentos em que o tutor fala; cada um tem uma seção no arquivo do prompt
MOMENTOS = frozenset({"pista_1", "pista_2", "explicacao", "acerto", "conversa"})

NIVEL_DE_AJUDA = {
    Estado.RESPONDENDO: "o aluno ainda não marcou nenhuma alternativa. Dê só um empurrão inicial, "
    "como perguntar o que a questão pede ou quais dados importam.",
    Estado.PISTA_1: "o aluno errou uma vez. Ajude apenas com perguntas.",
    Estado.PISTA_2: "o aluno errou duas vezes. Pode dar dicas mais diretas, sem chegar ao resultado.",
    Estado.EXPLICACAO: "a resposta já foi revelada. Ajude livremente.",
    Estado.CONCLUIDA: "a resposta já foi revelada. Ajude livremente.",
}


class PromptInvalido(ValueError):
    pass


@dataclass(frozen=True)
class Prompts:
    versao: str
    secoes: dict[str, str]

    @classmethod
    def carregar(cls, pasta: Path, versao: str) -> Prompts:
        caminho = Path(pasta) / f"{versao}.md"
        if not caminho.exists():
            raise PromptInvalido(f"prompt não encontrado: {caminho}")
        secoes = {}
        partes = re.split(r"(?m)^## ", caminho.read_text(encoding="utf-8"))
        for parte in partes[1:]:
            nome, _, corpo = parte.partition("\n")
            secoes[nome.strip()] = corpo.strip()
        faltando = SECOES_OBRIGATORIAS - secoes.keys()
        if faltando:
            raise PromptInvalido(f"{versao}: faltam as seções {sorted(faltando)}")
        return cls(versao, secoes)

    def sistema(self, questao: Questao, sessao: Sessao, momento: str, reforco: bool = False) -> str:
        """Instrução de sistema completa: regras, contexto da questão e o que fazer agora."""
        if momento not in MOMENTOS:
            raise ValueError(f"momento desconhecido: {momento}")
        protegido = sessao.estado in ESTADOS_PROTEGIDOS
        regra = self.secoes["regra_protegida" if protegido else "regra_livre"]
        contexto = self.secoes["sistema"].format_map(
            {
                "regra_da_resposta": regra,
                "area": questao.area_nome,
                "fonte": questao.fonte,
                "enunciado": questao.enunciado,
                "alternativas": "\n".join(f"{a.letra}) {a.texto}" for a in questao.alternativas),
                "gabarito": questao.gabarito,
                "resolucao": questao.resolucao,
                "habilidade": f"{questao.habilidade}: {questao.habilidade_descricao}",
                "tentativas": _tentativas(questao, sessao),
            }
        )
        instrucao = self.secoes[momento].format_map({"nivel_de_ajuda": NIVEL_DE_AJUDA[sessao.estado]})
        partes = [contexto, instrucao]
        if reforco:
            partes.append(self.secoes["reforco"])
        return "\n\n".join(partes)


def _tentativas(questao: Questao, sessao: Sessao) -> str:
    if not sessao.tentativas:
        return "nenhuma ainda"
    linhas = []
    for letra in sessao.tentativas:
        engano = questao.alternativa(letra).engano_provavel
        linhas.append(f"- {letra}: {engano}" if engano else f"- {letra}: (alternativa correta)")
    return "\n".join(linhas)
