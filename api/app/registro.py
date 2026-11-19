"""Uma linha de log por requisição, sem dado pessoal.

Substitui o log de acesso do uvicorn, que grava o IP do aluno e a URL completa. Aqui fica só o
método, o caminho (sem a query string), o status e o tempo. O texto das mensagens nunca entra no log.
"""

from __future__ import annotations

import logging
import time

from .cabecalhos import App, Escopo, Mensagem

logger = logging.getLogger("pista.requisicoes")


class RegistroDeRequisicoes:
    def __init__(self, app: App):
        self.app = app

    async def __call__(self, escopo: Escopo, receber, enviar) -> None:
        if escopo["type"] != "http":
            await self.app(escopo, receber, enviar)
            return
        inicio = time.monotonic()
        status = 500  # se a resposta nem começar, foi erro

        async def enviar_e_anotar(mensagem: Mensagem) -> None:
            nonlocal status
            if mensagem["type"] == "http.response.start":
                status = mensagem["status"]
            await enviar(mensagem)

        try:
            await self.app(escopo, receber, enviar_e_anotar)
        finally:
            milissegundos = (time.monotonic() - inicio) * 1000
            logger.info("%s %s %d %.0fms", escopo["method"], escopo["path"], status, milissegundos)
