"""Integração com o Gemini: tempo limite, novas tentativas e modelo reserva.

Se todos os modelos falharem, levanta `ErroDaIA` e o motor do tutor usa o plano B
(mensagens escritas à mão e a resolução anotada da questão).
"""

from __future__ import annotations

import asyncio
import logging
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


class ClienteGemini:
    def __init__(
        self,
        chave: str,
        modelos: Sequence[str],
        tempo_limite: float = 20.0,
        tentativas_por_modelo: int = 2,
        nivel_de_raciocinio: str = "low",
        maximo_de_tokens: int = 2048,
        espera_inicial: float = 0.5,
        cliente: Any | None = None,
    ):
        if not modelos:
            raise ValueError("informe pelo menos um modelo")
        if cliente is None:
            from google import genai

            cliente = genai.Client(api_key=chave)
        self._cliente = cliente
        self.modelos = tuple(modelos)
        self.tempo_limite = tempo_limite
        self.tentativas_por_modelo = tentativas_por_modelo
        self.espera_inicial = espera_inicial
        self._configuracao_base = {
            "max_output_tokens": maximo_de_tokens,
            "thinking_config": {"thinking_level": nivel_de_raciocinio},
        }

    def _configuracao(self, sistema: str) -> dict[str, Any]:
        return {**self._configuracao_base, "system_instruction": sistema}

    async def gerar(self, sistema: str, conversa: Sequence[Turno]) -> RespostaDaIA:
        ultimo_erro: Exception | None = None
        for modelo in self.modelos:
            for tentativa in range(self.tentativas_por_modelo):
                try:
                    resposta = await asyncio.wait_for(
                        self._cliente.aio.models.generate_content(
                            model=modelo, contents=_conteudos(conversa), config=self._configuracao(sistema)
                        ),
                        timeout=self.tempo_limite,
                    )
                    texto = (resposta.text or "").strip()
                    if not texto:
                        raise ErroDaIA("resposta vazia")
                    uso = getattr(resposta, "usage_metadata", None)
                    return RespostaDaIA(texto, modelo, getattr(uso, "total_token_count", None))
                except Exception as erro:  # noqa: BLE001 - qualquer falha da IA vira plano B
                    ultimo_erro = erro
                    logger.warning(
                        "falha na IA", extra={"modelo": modelo, "tentativa": tentativa + 1, "erro": type(erro).__name__}
                    )
                    if _erro_definitivo(erro):
                        break
                    if tentativa + 1 < self.tentativas_por_modelo:
                        await asyncio.sleep(self.espera_inicial * 2**tentativa)
        raise ErroDaIA("todos os modelos falharam") from ultimo_erro

    async def gerar_em_trechos(self, sistema: str, conversa: Sequence[Turno]) -> AsyncIterator[str]:
        """Streaming real. Só tenta outro modelo se a falha acontecer antes do primeiro trecho."""
        ultimo_erro: Exception | None = None
        for modelo in self.modelos:
            enviou_algo = False
            try:
                fluxo = await asyncio.wait_for(
                    self._cliente.aio.models.generate_content_stream(
                        model=modelo, contents=_conteudos(conversa), config=self._configuracao(sistema)
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
                logger.warning("falha na IA (streaming)", extra={"modelo": modelo, "erro": type(erro).__name__})
                if enviou_algo:
                    raise ErroDaIA("a resposta foi interrompida") from erro
        raise ErroDaIA("todos os modelos falharam") from ultimo_erro
