"""Cabeçalhos de segurança em todas as respostas da API.

Middleware ASGI puro (e não BaseHTTPMiddleware) para não atrapalhar o streaming da conversa.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

Escopo = MutableMapping[str, Any]
Mensagem = MutableMapping[str, Any]
App = Callable[[Escopo, Callable[[], Awaitable[Mensagem]], Callable[[Mensagem], Awaitable[None]]], Awaitable[None]]

# A API só devolve JSON: nada pode ser carregado nem embutido a partir dela.
CSP_DA_API = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
# A documentação (Swagger e ReDoc) carrega scripts e estilos do jsDelivr e tem script inline.
CSP_DA_DOCUMENTACAO = (
    "default-src 'none'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; img-src 'self' data: https://fastapi.tiangolo.com https://cdn.redoc.ly; "
    "connect-src 'self'; worker-src blob:; frame-ancestors 'none'; base-uri 'none'"
)
CAMINHOS_DA_DOCUMENTACAO = ("/docs", "/redoc")

CABECALHOS_FIXOS = {
    b"x-content-type-options": b"nosniff",
    b"x-frame-options": b"DENY",
    b"referrer-policy": b"no-referrer",
    b"strict-transport-security": b"max-age=31536000; includeSubDomains",
    b"permissions-policy": b"camera=(), microphone=(), geolocation=()",
    b"cross-origin-opener-policy": b"same-origin",
}


class CabecalhosDeSeguranca:
    def __init__(self, app: App):
        self.app = app

    async def __call__(self, escopo: Escopo, receber, enviar) -> None:
        if escopo["type"] != "http":
            await self.app(escopo, receber, enviar)
            return
        documentacao = escopo.get("path", "").startswith(CAMINHOS_DA_DOCUMENTACAO)
        csp = (CSP_DA_DOCUMENTACAO if documentacao else CSP_DA_API).encode()

        async def enviar_com_cabecalhos(mensagem: Mensagem) -> None:
            if mensagem["type"] == "http.response.start":
                atuais = list(mensagem.get("headers", []))
                existentes = {nome.lower() for nome, _ in atuais}
                extras = [(n, v) for n, v in CABECALHOS_FIXOS.items() if n not in existentes]
                if b"content-security-policy" not in existentes:
                    extras.append((b"content-security-policy", csp))
                if not documentacao and b"cache-control" not in existentes:
                    extras.append((b"cache-control", b"no-store"))  # respostas com dados da conta
                mensagem["headers"] = atuais + extras
            await enviar(mensagem)

        await self.app(escopo, receber, enviar_com_cabecalhos)
