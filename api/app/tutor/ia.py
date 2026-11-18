"""Integração com o Gemini: tempo limite, novas tentativas e modelo reserva.

Se todos os modelos falharem, levanta `ErroDaIA` e o motor do tutor usa o plano B
(mensagens escritas à mão e a resolução anotada da questão).
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol

logger = logging.getLogger(__name__)

PapelDaConversa = Literal["aluno", "tutor"]
Turno = tuple[PapelDaConversa, str]


class ErroDaIA(Exception):
    pass


@dataclass(frozen=True)
class RespostaDaIA:
    texto: str
    modelo: str
    tokens: int | None = None


class ClienteDeIA(Protocol):
    async def gerar(self, sistema: str, conversa: Sequence[Turno]) -> RespostaDaIA: ...

    def gerar_em_trechos(self, sistema: str, conversa: Sequence[Turno]) -> AsyncIterator[str]: ...


def _conteudos(conversa: Sequence[Turno]) -> list[dict[str, Any]]:
    return [{"role": "user" if papel == "aluno" else "model", "parts": [{"text": texto}]} for papel, texto in conversa]


def _erro_definitivo(erro: Exception) -> bool:
    """Erros que não melhoram tentando de novo: chave inválida, requisição malformada."""
    codigo = getattr(erro, "code", None)
    return isinstance(codigo, int) and 400 <= codigo < 500 and codigo not in (408, 429)


def ler_modelos(texto: Sequence[str], nivel_padrao: str) -> tuple[tuple[str, str], ...]:
    """Lê "modelo:nivel" (o nível de raciocínio é opcional). Cada modelo aceita níveis diferentes:
    o Flash-Lite responde rápido com "minimal", que o 3.8 Flash não aceita."""
    modelos = []
    for item in texto:
        nome, _, nivel = item.strip().partition(":")
        modelos.append((nome.strip(), nivel.strip() or nivel_padrao))
    return tuple(modelos)


class ClienteGemini:
    def __init__(
        self,
        chave: str,
        modelos: Sequence[str],
        tempo_limite: float = 12.0,
        tentativas_por_modelo: int = 2,
        nivel_de_raciocinio: str = "low",
        maximo_de_tokens: int = 1024,
        espera_inicial: float = 0.5,
        cliente: Any | None = None,
    ):
        if not modelos:
            raise ValueError("informe pelo menos um modelo")
        if cliente is None:
            from google import genai

            cliente = genai.Client(api_key=chave)
        self._cliente = cliente
        self.modelos = ler_modelos(modelos, nivel_de_raciocinio)
        self.tempo_limite = tempo_limite
        self.tentativas_por_modelo = tentativas_por_modelo
        self.espera_inicial = espera_inicial
        self.maximo_de_tokens = maximo_de_tokens

    def _configuracao(self, sistema: str, nivel: str) -> dict[str, Any]:
        return {
            "system_instruction": sistema,
            "max_output_tokens": self.maximo_de_tokens,
            "thinking_config": {"thinking_level": nivel},
        }

    async def gerar(self, sistema: str, conversa: Sequence[Turno]) -> RespostaDaIA:
        ultimo_erro: Exception | None = None
        for modelo, nivel in self.modelos:
            for tentativa in range(self.tentativas_por_modelo):
                inicio = time.monotonic()
                try:
                    resposta = await asyncio.wait_for(
                        self._cliente.aio.models.generate_content(
                            model=modelo, contents=_conteudos(conversa), config=self._configuracao(sistema, nivel)
                        ),
                        timeout=self.tempo_limite,
                    )
                    texto = (resposta.text or "").strip()
                    if not texto:
                        raise ErroDaIA("resposta vazia")
                    uso = getattr(resposta, "usage_metadata", None)
                    tokens = getattr(uso, "total_token_count", None)
                    logger.info("ia modelo=%s segundos=%.1f tokens=%s", modelo, time.monotonic() - inicio, tokens)
                    return RespostaDaIA(texto, modelo, tokens)
                except Exception as erro:  # noqa: BLE001 - qualquer falha da IA vira plano B
                    ultimo_erro = erro
                    logger.warning(
                        "falha na IA modelo=%s tentativa=%d segundos=%.1f erro=%s",
                        modelo,
                        tentativa + 1,
                        time.monotonic() - inicio,
                        type(erro).__name__,
                    )
                    if _erro_definitivo(erro):
                        break
                    if tentativa + 1 < self.tentativas_por_modelo:
                        await asyncio.sleep(self.espera_inicial * 2**tentativa)
        raise ErroDaIA("todos os modelos falharam") from ultimo_erro

    async def gerar_em_trechos(self, sistema: str, conversa: Sequence[Turno]) -> AsyncIterator[str]:
        """Streaming real. Só tenta outro modelo se a falha acontecer antes do primeiro trecho."""
        ultimo_erro: Exception | None = None
        for modelo, nivel in self.modelos:
            enviou_algo = False
            try:
                fluxo = await asyncio.wait_for(
                    self._cliente.aio.models.generate_content_stream(
                        model=modelo, contents=_conteudos(conversa), config=self._configuracao(sistema, nivel)
                    ),
                    timeout=self.tempo_limite,
                )
                async for parte in fluxo:
                    if parte.text:
                        enviou_algo = True
                        yield parte.text
                if enviou_algo:
                    return
                raise ErroDaIA("resposta vazia")
            except Exception as erro:  # noqa: BLE001
                ultimo_erro = erro
                logger.warning("falha na IA (streaming) modelo=%s erro=%s", modelo, type(erro).__name__)
                if enviou_algo:
                    raise ErroDaIA("a resposta foi interrompida") from erro
        raise ErroDaIA("todos os modelos falharam") from ultimo_erro
