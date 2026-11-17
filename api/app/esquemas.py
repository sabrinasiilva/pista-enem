"""Formatos de entrada e saída da API (validados pelo Pydantic e mostrados no Swagger)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .tutor.estados import Estado
from .tutor.questoes import Questao
from .tutor.sessao import Mensagem, Sessao

Letra = Literal["A", "B", "C", "D", "E"]


class Esquema(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- erros


class DetalheDoErro(Esquema):
    codigo: str = Field(examples=["sessao_nao_encontrada"])
    mensagem: str = Field(examples=["Sessão não encontrada ou expirada."])
    detalhes: list[dict] | None = None


class Erro(Esquema):
    erro: DetalheDoErro


# ---------------------------------------------------------------- questões


class Habilidade(Esquema):
    codigo: str = Field(examples=["H16"])
    descricao: str


class Fonte(Esquema):
    prova: str = Field(examples=["ENEM 2022, 2º dia, caderno 6 (cinza), questão 141"])
    url: str


class AlternativaSaida(Esquema):
    letra: Letra
    texto: str


class QuestaoResumo(Esquema):
    id: str = Field(examples=["2022-141"])
    ano: int
    numero: int
    area: str = Field(examples=["matematica"])
    habilidade: str = Field(examples=["H16"])
    inicio_do_enunciado: str

    @classmethod
    def de(cls, questao: Questao) -> QuestaoResumo:
        inicio = questao.enunciado[:140].rsplit(" ", 1)[0] + "…" if len(questao.enunciado) > 140 else questao.enunciado
        return cls(
            id=questao.id,
            ano=questao.ano,
            numero=questao.numero,
            area=questao.area,
            habilidade=questao.habilidade,
            inicio_do_enunciado=inicio,
        )


class QuestaoDetalhe(Esquema):
    """Questão para resolver. O gabarito, a resolução e os enganos ficam só no servidor."""

    id: str
    ano: int
    numero: int
    area: str
    enunciado: str = Field(description="Markdown com fórmulas em LaTeX entre $...$")
    alternativas: list[AlternativaSaida]
    habilidade: Habilidade
    fonte: Fonte

    @classmethod
    def de(cls, questao: Questao) -> QuestaoDetalhe:
        return cls(
            id=questao.id,
            ano=questao.ano,
            numero=questao.numero,
            area=questao.area,
            enunciado=questao.enunciado,
            alternativas=[AlternativaSaida(letra=a.letra, texto=a.texto) for a in questao.alternativas],
            habilidade=Habilidade(codigo=questao.habilidade, descricao=questao.habilidade_descricao),
            fonte=Fonte(prova=questao.fonte, url=questao.url_fonte),
        )


# ---------------------------------------------------------------- sessões


class MensagemSaida(Esquema):
    papel: Literal["aluno", "tutor"]
    texto: str
    estado: Estado
    criada_em: datetime

    @classmethod
    def de(cls, mensagem: Mensagem) -> MensagemSaida:
        return cls(papel=mensagem.papel, texto=mensagem.texto, estado=mensagem.estado, criada_em=mensagem.criada_em)


class NovaSessao(Esquema):
    questao_id: str = Field(examples=["2022-141"])


class SessaoSaida(Esquema):
    id: str
    questao_id: str
    estado: Estado
    tentativas: list[Letra]
    gabarito: Letra | None = Field(description="Só aparece depois que a resposta é revelada")
    mensagens: list[MensagemSaida]

    @classmethod
    def de(cls, sessao: Sessao, gabarito: str) -> SessaoSaida:
        return cls(
            id=sessao.id,
            questao_id=sessao.questao_id,
            estado=sessao.estado,
            tentativas=sessao.tentativas,
            gabarito=gabarito if sessao.resposta_revelada else None,
            mensagens=[MensagemSaida.de(m) for m in sessao.mensagens],
        )


class RespostaEntrada(Esquema):
    alternativa: Letra = Field(examples=["B"])


class RespostaSaida(Esquema):
    acertou: bool
    estado: Estado
    tentativas: list[Letra]
    gabarito: Letra | None = Field(description="Só aparece depois que a resposta é revelada")
    mensagem: MensagemSaida


class MensagemEntrada(Esquema):
    # o limite fino (1 000 caracteres) é do guardrail, que responde com uma mensagem amigável;
    # este limite só impede requisições enormes
    texto: str = Field(min_length=1, max_length=5000, examples=["Não sei por onde começar."])


class ExplicacaoEntrada(Esquema):
    confirmar: bool = Field(description="Precisa ser true: o aluno confirma que quer ver a resposta")


class ExplicacaoSaida(Esquema):
    estado: Estado
    gabarito: Letra
    mensagem: MensagemSaida


class Saude(Esquema):
    status: Literal["ok"]
    versao: str
    questoes: int
    ia: Literal["gemini", "desativada"]
    prompt: str
