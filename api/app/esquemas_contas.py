"""Formatos de entrada e saída das contas e do progresso."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from .banco import Usuario
from .esquemas import Esquema, QuestaoResumo

Tema = Literal["claro", "escuro", "sistema"]
CodigoDeHabilidade = Annotated[str, Field(pattern=r"^H([1-9]|[12][0-9]|30)$", examples=["H16"])]


class UsuarioSaida(Esquema):
    id: str
    apelido: str
    meta_semanal: int
    habilidades_foco: list[str]
    tema: Tema
    criado_em: datetime

    @classmethod
    def de(cls, usuario: Usuario) -> UsuarioSaida:
        return cls(
            id=usuario.id,
            apelido=usuario.apelido,
            meta_semanal=usuario.meta_semanal,
            habilidades_foco=usuario.habilidades_foco,
            tema=usuario.tema,  # type: ignore[arg-type]
            criado_em=usuario.criado_em,
        )


class Cadastro(Esquema):
    apelido: str = Field(min_length=3, max_length=20, examples=["estudante_2026"])
    senha: str = Field(min_length=8, max_length=128)
    meta_semanal: int = Field(default=10, ge=1, le=200)
    habilidades_foco: list[CodigoDeHabilidade] = Field(default_factory=list, max_length=30)


class Login(Esquema):
    apelido: str = Field(min_length=1, max_length=20)
    senha: str = Field(min_length=1, max_length=128)


class Recuperacao(Esquema):
    apelido: str = Field(min_length=1, max_length=20)
    codigo_de_recuperacao: str = Field(min_length=16, max_length=24, examples=["ABCD-EFGH-JKMN-PQRS"])
    nova_senha: str = Field(min_length=8, max_length=128)


class AcessoSaida(Esquema):
    token: str = Field(description="Envie no cabeçalho Authorization: Bearer <token>")
    usuario: UsuarioSaida
    codigo_de_recuperacao: str | None = Field(
        default=None, description="Só aparece no cadastro e na recuperação. Mostre uma vez e não guarde."
    )


class AtualizacaoDoPerfil(Esquema):
    meta_semanal: int | None = Field(default=None, ge=1, le=200)
    habilidades_foco: list[CodigoDeHabilidade] | None = Field(default=None, max_length=30)
    tema: Tema | None = None


class TrocaDeSenha(Esquema):
    senha_atual: str = Field(min_length=1, max_length=128)
    nova_senha: str = Field(min_length=8, max_length=128)


class ConfirmacaoDeSenha(Esquema):
    senha: str = Field(min_length=1, max_length=128)


class HabilidadeSaida(Esquema):
    codigo: str
    descricao: str
    feitas: int
    acertos_de_primeira: int


class ResultadoSaida(Esquema):
    questao_id: str
    habilidade: str
    acertou: bool
    acertou_de_primeira: bool
    tentativas: int
    pediu_explicacao: bool
    concluido_em: datetime


class ProgressoSaida(Esquema):
    total_de_questoes: int
    acertos_de_primeira: int
    sequencia_de_dias: int
    feitas_na_semana: int
    meta_semanal: int
    por_habilidade: list[HabilidadeSaida]
    recentes: list[ResultadoSaida]


class QuestaoParaRevisar(Esquema):
    questao: QuestaoResumo
    ultima_tentativa: ResultadoSaida
