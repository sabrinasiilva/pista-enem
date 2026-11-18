"""Configurações lidas de variáveis de ambiente (ou do arquivo api/.env, fora do Git)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PASTA_API = Path(__file__).resolve().parents[1]
RAIZ_DO_REPOSITORIO = PASTA_API.parent


class Configuracoes(BaseSettings):
    model_config = SettingsConfigDict(env_file=PASTA_API / ".env", env_file_encoding="utf-8", extra="ignore")

    # IA. Sem chave, o tutor funciona só com o plano B (mensagens fixas e resolução anotada).
    gemini_api_key: SecretStr | None = None
    # principal e reservas, em ordem, no formato "modelo:nível de raciocínio".
    # O Flash-Lite com "minimal" responde em poucos segundos; o 3.8 Flash é a reserva, mais lento.
    gemini_modelos: str = "gemini-3.5-flash-lite:minimal,gemini-3.8-flash:low"
    ia_tempo_limite: float = 12.0
    ia_tentativas_por_modelo: int = 2
    ia_nivel_de_raciocinio: Literal["minimal", "low", "medium", "high"] = "low"  # para modelos sem nível

    versao_prompt: str = "tutor_v1"
    arquivo_questoes: Path = RAIZ_DO_REPOSITORIO / "data" / "questoes-mvp.json"
    pasta_prompts: Path = RAIZ_DO_REPOSITORIO / "prompts"

    # endereços do front-end que podem chamar a API, separados por vírgula
    cors_origens: str = "http://localhost:5173"

    # banco de dados: SQLite local por padrão; em produção, PostgreSQL (Neon)
    database_url: str = f"sqlite:///{(PASTA_API / 'pista.db').as_posix()}"
    # usuário dono do banco, só para as migrações (criar e alterar tabelas). Assim o dia a dia
    # da API usa um usuário que não consegue apagar tabelas. Sem isto, usa database_url.
    migracoes_database_url: str | None = None
    migrar_ao_iniciar: bool = True

    # limites de uso (Fase 6). Ações com IA: responder, conversar e pedir a explicação.
    limite_ia_por_ip: int = 40  # a cada 10 minutos
    limite_ia_por_sessao: int = 40  # no total
    limite_sessoes_por_ip: int = 30  # a cada 10 minutos
    ia_cota_diaria: int = 1500  # chamadas ao Gemini por dia; depois disso, plano B
    # cabeçalho com o IP real do aluno. No Render, a Cloudflare define o True-Client-IP,
    # que o cliente não consegue forjar (o X-Forwarded-For consegue). Vazio: usa a conexão.
    cabecalho_ip_do_cliente: str = "true-client-ip"

    @field_validator("database_url", "migracoes_database_url")
    @classmethod
    def _usar_psycopg(cls, url: str | None) -> str | None:
        """O Neon entrega "postgresql://..."; o SQLAlchemy precisa saber qual driver usar."""
        if not url:
            return None if url is None else url
        for prefixo in ("postgres://", "postgresql://"):
            if url.startswith(prefixo):
                return "postgresql+psycopg://" + url[len(prefixo) :]
        return url

    @property
    def url_das_migracoes(self) -> str:
        return self.migracoes_database_url or self.database_url

    @property
    def lista_de_modelos(self) -> list[str]:
        return [m.strip() for m in self.gemini_modelos.split(",") if m.strip()]

    @property
    def lista_de_origens(self) -> list[str]:
        return [o.strip() for o in self.cors_origens.split(",") if o.strip()]


@lru_cache
def configuracoes() -> Configuracoes:
    return Configuracoes()
