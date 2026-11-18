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
    gemini_modelos: str = "gemini-3.8-flash,gemini-3.5-flash-lite"  # principal e reservas, em ordem
    ia_tempo_limite: float = 20.0
    ia_tentativas_por_modelo: int = 2
    ia_nivel_de_raciocinio: Literal["low", "medium", "high"] = "low"

    versao_prompt: str = "tutor_v1"
    arquivo_questoes: Path = RAIZ_DO_REPOSITORIO / "data" / "questoes-mvp.json"
    pasta_prompts: Path = RAIZ_DO_REPOSITORIO / "prompts"

    # endereços do front-end que podem chamar a API, separados por vírgula
    cors_origens: str = "http://localhost:5173"

    # banco de dados: SQLite local por padrão; na Fase 5, PostgreSQL (Neon)
    database_url: str = f"sqlite:///{(PASTA_API / 'pista.db').as_posix()}"
    migrar_ao_iniciar: bool = True

    @field_validator("database_url")
    @classmethod
    def _usar_psycopg(cls, url: str) -> str:
        """O Neon entrega "postgresql://..."; o SQLAlchemy precisa saber qual driver usar."""
        for prefixo in ("postgres://", "postgresql://"):
            if url.startswith(prefixo):
                return "postgresql+psycopg://" + url[len(prefixo) :]
        return url

    @property
    def lista_de_modelos(self) -> list[str]:
        return [m.strip() for m in self.gemini_modelos.split(",") if m.strip()]

    @property
    def lista_de_origens(self) -> list[str]:
        return [o.strip() for o in self.cors_origens.split(",") if o.strip()]


@lru_cache
def configuracoes() -> Configuracoes:
    return Configuracoes()
