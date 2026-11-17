"""Usa o tutor pelo terminal, sem a API web.

Uso (dentro de api/):
    python -m app.tutor.terminal            # questão aleatória
    python -m app.tutor.terminal 2022-140   # questão específica

Comandos: uma letra de A a E responde; "?" pede a explicação; "sair" encerra;
qualquer outro texto é uma mensagem para o tutor.
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys

from ..config import configuracoes
from .estados import ESTADOS_FINAIS, TransicaoInvalida
from .fabrica import criar_tutor
from .questoes import LETRAS


def _mostrar(rotulo: str, texto: str) -> None:
    print(f"\n{rotulo}: {texto}\n")


async def _rodar(id_questao: str | None) -> None:
    tutor = criar_tutor(configuracoes())
    if tutor.ia is None:
        print("Aviso: GEMINI_API_KEY não configurada. O tutor vai usar só o plano B.")
    # sorteio de questão, não é uso criptográfico
    questao = tutor.banco.obter(id_questao) if id_questao else random.choice(tutor.banco.listar())  # noqa: S311
    sessao = tutor.nova_sessao(questao.id)

    print(f"\n{questao.fonte}\n\n{questao.enunciado}\n")
    for alternativa in questao.alternativas:
        print(f"  {alternativa.letra}) {alternativa.texto}")

    while True:
        try:
            entrada = (await asyncio.to_thread(input, f"\n[{sessao.estado}] você> ")).strip()
        except (EOFError, KeyboardInterrupt):
            break
        if entrada.lower() == "sair":
            break
        try:
            if entrada.upper() in LETRAS:
                resultado = await tutor.responder(sessao, entrada)
                _mostrar("Acertou!" if resultado.acertou else "Ainda não", resultado.mensagem.texto)
            elif entrada == "?":
                mensagem = await tutor.explicar(sessao, confirmado=True)
                _mostrar("Explicação", mensagem.texto)
            else:
                print("\ntutor> ", end="", flush=True)
                async for trecho in tutor.conversar_em_trechos(sessao, entrada):
                    print(trecho, end="", flush=True)
                print()
        except TransicaoInvalida as erro:
            print(f"\n({erro.mensagem})")
        if sessao.estado in ESTADOS_FINAIS:
            print("\n(questão encerrada; você ainda pode conversar sobre ela ou digitar 'sair')")


def main() -> None:
    parser = argparse.ArgumentParser(description="Tutor Pista no terminal")
    parser.add_argument("questao", nargs="?", help="id da questão, por exemplo 2022-140")
    argumentos = parser.parse_args()
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(_rodar(argumentos.questao))


if __name__ == "__main__":
    main()
