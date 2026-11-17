"""Configurações lidas de variáveis de ambiente (ou do arquivo api/.env, fora do Git)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
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

    @property
    def lista_de_modelos(self) -> list[str]:
        return [m.strip() for m in self.gemini_modelos.split(",") if m.strip()]

    @property
    def lista_de_origens(self) -> list[str]:
        return [o.strip() for o in self.cors_origens.split(",") if o.strip()]


@lru_cache
def configuracoes() -> Configuracoes:
    return Configuracoes()
