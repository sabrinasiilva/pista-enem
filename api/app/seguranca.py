"""Senhas, tokens de acesso e códigos de recuperação.

- Senhas e códigos de recuperação: scrypt (biblioteca padrão do Python), com sal aleatório.
- Tokens de acesso: 32 bytes aleatórios; no banco fica só o SHA-256 deles.
- Comparações em tempo constante, para não vazar informação pelo tempo de resposta.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets

# parâmetros do scrypt: custo 2^14, como recomendado para logins interativos
_N, _R, _P = 2**14, 8, 1
_ALFABETO_DO_CODIGO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # sem 0/O, 1/I/L, para não confundir


def _b64(dados: bytes) -> str:
    return base64.b64encode(dados).decode()


def gerar_hash(segredo: str) -> str:
    sal = secrets.token_bytes(16)
    derivado = hashlib.scrypt(segredo.encode(), salt=sal, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${_b64(sal)}${_b64(derivado)}"


def conferir_hash(segredo: str, guardado: str) -> bool:
    try:
        nome, n, r, p, sal, esperado = guardado.split("$")
        if nome != "scrypt":
            return False
        derivado = hashlib.scrypt(segredo.encode(), salt=base64.b64decode(sal), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(derivado, base64.b64decode(esperado))
    except (ValueError, TypeError):
        return False


# hash calculado uma vez para comparar quando o apelido não existe: o tempo de resposta
# fica igual ao de uma senha errada, e ninguém descobre quais apelidos existem
HASH_FICTICIO = gerar_hash("senha-que-nao-existe")


def gerar_token() -> str:
    return secrets.token_urlsafe(32)


def hash_do_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def gerar_codigo_de_recuperacao() -> str:
    """Código no formato XXXX-XXXX-XXXX-XXXX (cerca de 79 bits de aleatoriedade)."""
    letras = "".join(secrets.choice(_ALFABETO_DO_CODIGO) for _ in range(16))
    return "-".join(letras[i : i + 4] for i in range(0, 16, 4))


def normalizar_codigo(codigo: str) -> str:
    """Aceita o código com ou sem hífens e em minúsculas."""
    letras = re.sub(r"[^A-Za-z0-9]", "", codigo).upper()
    return "-".join(letras[i : i + 4] for i in range(0, len(letras), 4))
