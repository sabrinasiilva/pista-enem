"""Monta o tutor a partir das configurações."""

from __future__ import annotations

from ..config import Configuracoes
from ..limites import CotaDiaria, IAComCota
from .ia import ClienteGemini
from .motor import Tutor
from .prompts import Prompts
from .questoes import BancoDeQuestoes


def criar_tutor(config: Configuracoes) -> Tutor:
    ia = None
    if config.gemini_api_key is not None and config.gemini_api_key.get_secret_value():
        gemini = ClienteGemini(
            chave=config.gemini_api_key.get_secret_value(),
            modelos=config.lista_de_modelos,
            tempo_limite=config.ia_tempo_limite,
            tentativas_por_modelo=config.ia_tentativas_por_modelo,
            nivel_de_raciocinio=config.ia_nivel_de_raciocinio,
        )
        ia = IAComCota(gemini, CotaDiaria(config.ia_cota_diaria))
    return Tutor(
        banco=BancoDeQuestoes.de_arquivo(config.arquivo_questoes),
        prompts=Prompts.carregar(config.pasta_prompts, config.versao_prompt),
        ia=ia,
    )
