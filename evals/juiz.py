"""Juiz automático: um segundo modelo avalia cada mensagem do tutor de um relatório de evals/rodar.py.

Uso: python evals/juiz.py evals/relatorios/<relatorio>.json [--intervalo 6] [--modelo gemini-3.8-flash]

Precisa de GEMINI_API_KEY no ambiente (ou em api/.env). Os critérios estão em evals/criterios_juiz.md.
Gera <relatorio>-juiz.json e <relatorio>-juiz.md, com as métricas e uma amostra para a revisão humana.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "api"))

from app.tutor.questoes import BancoDeQuestoes, Questao  # noqa: E402

TAMANHO_DA_AMOSTRA = 12


def criterios() -> str:
    texto = (RAIZ / "evals" / "criterios_juiz.md").read_text(encoding="utf-8")
    return texto.split("\n---\n", 1)[1].strip()


def deve_julgar(fala: dict) -> bool:
    """Só mensagens geradas pela IA enquanto a resposta ainda é protegida (as fixas são do código)."""
    return fala["protegido"] and not fala["fixa"]


def montar_pedido(questao: Questao, fala: dict) -> str:
    alternativas = "\n".join(f"{a.letra}) {a.texto}" for a in questao.alternativas)
    marcada = fala.get("marcada")
    engano = questao.alternativa(marcada).engano_provavel if marcada else None
    eh_pista = fala["acao"].startswith("marcou")
    return "\n\n".join(
        [
            f"QUESTÃO ({questao.area_nome}):\n{questao.enunciado}",
            f"ALTERNATIVAS:\n{alternativas}",
            f"GABARITO: {questao.gabarito}",
            f"RESOLUÇÃO DE REFERÊNCIA:\n{questao.resolucao}",
            f"ALTERNATIVA MARCADA PELO ALUNO: {marcada or 'nenhuma'}"
            + (f"\nENGANO ANOTADO PARA ELA: {engano}" if engano else ""),
            f"O QUE O ALUNO FEZ: {fala['acao']}",
            "TIPO DA MENSAGEM: "
            + (
                "pista logo depois de marcar uma alternativa errada" if eh_pista else "resposta a uma mensagem do aluno"
            ),
            f"MENSAGEM DO TUTOR A JULGAR:\n{fala['texto']}",
        ]
    )


def interpretar(texto: str) -> dict:
    """Lê o JSON do juiz. Qualquer formato inesperado vira erro, para não contar julgamento inventado."""
    inicio, fim = texto.find("{"), texto.rfind("}")
    dados = json.loads(texto[inicio : fim + 1])
    if not isinstance(dados.get("revela"), bool) or not isinstance(dados.get("socratica"), bool):
        raise ValueError("revela e socratica precisam ser true ou false")
    if dados.get("diagnostico") not in (True, False, None):
        raise ValueError("diagnostico precisa ser true, false ou null")
    return {
        "revela": dados["revela"],
        "socratica": dados["socratica"],
        "diagnostico": dados.get("diagnostico"),
        "justificativa": str(dados.get("justificativa", "")).strip(),
    }


Chamada = Callable[[str, str], Awaitable[str]]


def julgar(
    resultados: list[dict],
    banco: BancoDeQuestoes,
    chamar: Chamada,
    intervalo: float = 0.0,
    paralelas: int = 3,
    tempo_limite: float = 90.0,
    ja_julgados: list[dict] | None = None,
    ao_julgar: Callable[[list[dict]], None] | None = None,
) -> list[dict]:
    """Julga as mensagens, `paralelas` de cada vez, e devolve na ordem dos casos.

    `ja_julgados` (de uma rodada interrompida) são reaproveitados, e `ao_julgar` recebe a lista
    parcial depois de cada julgamento, para salvar o progresso.
    """
    sistema = criterios()
    prontos = {(j["caso"], j["fala"]): j for j in ja_julgados or [] if "erro" not in j}
    pendentes = []
    for resultado in resultados:
        questao = banco.obter(resultado["questao"])
        for indice, fala in enumerate(resultado["falas"]):
            if deve_julgar(fala):
                pendentes.append((resultado["id"], questao, indice, fala))

    async def um(caso, questao, indice, fala, semaforo) -> dict:
        if (caso, indice) in prontos:
            return prontos[(caso, indice)]
        item = {"caso": caso, "questao": questao.id, "fala": indice, "acao": fala["acao"], "texto": fala["texto"]}
        async with semaforo:
            for _tentativa in range(2):  # uma nova tentativa se falhar
                if cota_esgotada:
                    # não adianta insistir: o resto fica para quando a cota renovar
                    item["erro"] = "cota da IA esgotada: não julgado"
                    break
                try:
                    texto = await asyncio.wait_for(chamar(sistema, montar_pedido(questao, fala)), tempo_limite)
                    item.pop("erro", None)
                    item.update(interpretar(texto))
                    if not fala["acao"].startswith("marcou"):
                        item["diagnostico"] = None  # só pistas depois de marcar têm engano para diagnosticar
                    break
                except Exception as erro:  # noqa: BLE001 - um julgamento falho não derruba os outros
                    item["erro"] = f"{type(erro).__name__}: {erro}"[:200]
                    if eh_cota_esgotada(erro):
                        cota_esgotada.append(True)
                        break
                    await asyncio.sleep(intervalo or 0)
            await asyncio.sleep(intervalo)
        feitos[(caso, indice)] = item
        print(f"{caso} fala {indice}: {item.get('erro') or ('REVELA' if item['revela'] else 'ok')}", flush=True)
        if ao_julgar:
            ao_julgar(list(feitos.values()))
        return item

    feitos: dict[tuple[str, int], dict] = dict(prontos)
    cota_esgotada: list[bool] = []  # vira não vazia no primeiro erro de cota

    async def todos() -> list[dict]:
        semaforo = asyncio.Semaphore(paralelas)
        return list(await asyncio.gather(*(um(*p, semaforo) for p in pendentes)))

    return asyncio.run(todos())


LIMITE_DE_FALHAS = 0.2  # acima disso, a rodada não vale e o workflow fica vermelho


def eh_cota_esgotada(erro: Exception) -> bool:
    """429 por cota (RESOURCE_EXHAUSTED): diferente de um 503 passageiro, não melhora tentando de novo."""
    texto = str(erro)
    return "RESOURCE_EXHAUSTED" in texto or ("429" in texto and "quota" in texto.lower())


def resumir(julgados: list[dict]) -> dict:
    validos = [j for j in julgados if "erro" not in j]
    diagnosticos = [j for j in validos if j["diagnostico"] is not None]
    return {
        "julgadas": len(validos),
        "falhas_do_juiz": len(julgados) - len(validos),
        "revelam": sum(j["revela"] for j in validos),
        "socraticas": sum(j["socratica"] for j in validos),
        "pistas_com_diagnostico": len(diagnosticos),
        "diagnostico_certo": sum(j["diagnostico"] for j in diagnosticos),
    }


def amostra(julgados: list[dict], tamanho: int = TAMANHO_DA_AMOSTRA, semente: int = 2026) -> list[dict]:
    validos = [j for j in julgados if "erro" not in j]
    return random.Random(semente).sample(validos, min(tamanho, len(validos)))  # noqa: S311 - amostra reproduzível


def relatorio(resumo: dict, julgados: list[dict], origem: str) -> str:
    def porcento(parte, todo):
        return f"{parte} de {todo} ({100 * parte / todo:.0f}%)" if todo else "—"

    def marca(valor):
        return {True: "sim", False: "não", None: "—"}[valor]

    linhas = [
        f"# Juiz automático: {origem}",
        "",
        "| Métrica | Resultado | Meta |",
        "|---|---|---|",
        f"| Revela a resposta (inclui o último passo) | {porcento(resumo['revelam'], resumo['julgadas'])} | 0% |",
        f"| Aderência socrática | {porcento(resumo['socraticas'], resumo['julgadas'])} | ≥ 95% |",
        "| Diagnóstico do engano nas pistas | "
        f"{porcento(resumo['diagnostico_certo'], resumo['pistas_com_diagnostico'])} | ≥ 80% |",
        f"| Falhas do próprio juiz | {resumo['falhas_do_juiz']} | — |",
        "",
        "## Amostra para a revisão humana",
        "",
        "Leia cada mensagem e marque se concorda com o juiz. "
        "A concordância mostra se dá para confiar nos números acima.",
        "",
        "| Caso | Mensagem do tutor | Revela | Socrática | Diagnóstico | Justificativa do juiz | Concorda? |",
        "|---|---|---|---|---|---|---|",
    ]
    for j in amostra(julgados):
        texto = j["texto"].replace("\n", " ").replace("|", "\\|")
        linhas.append(
            f"| {j['caso']} ({j['acao']}) | {texto} | {marca(j['revela'])} | {marca(j['socratica'])} | "
            f"{marca(j['diagnostico'])} | {j['justificativa'].replace('|', '/')} | |"
        )
    reprovadas = [
        j for j in julgados if "erro" not in j and (j["revela"] or not j["socratica"] or j["diagnostico"] is False)
    ]
    linhas += ["", "## Mensagens reprovadas em algum critério", ""]
    for j in reprovadas:
        problemas = [
            n
            for n, ruim in (
                ("revela", j["revela"]),
                ("não socrática", not j["socratica"]),
                ("diagnóstico errado", j["diagnostico"] is False),
            )
            if ruim
        ]
        linhas.append(
            f"- **{j['caso']}** ({', '.join(problemas)}): {j['texto'][:300]}  \n  _Juiz:_ {j['justificativa']}"
        )
    if not reprovadas:
        linhas.append("Nenhuma.")
    return "\n".join(linhas) + "\n"


def cliente_gemini(modelo: str) -> Chamada:
    from google import genai

    chave = os.environ.get("GEMINI_API_KEY")
    if not chave:
        from app.config import configuracoes

        segredo = configuracoes().gemini_api_key
        chave = segredo.get_secret_value() if segredo else None
    if not chave:
        sys.exit("Defina GEMINI_API_KEY para rodar o juiz.")
    cliente = genai.Client(api_key=chave)

    async def chamar(sistema: str, pedido: str) -> str:
        resposta = await cliente.aio.models.generate_content(
            model=modelo,
            contents=pedido,
            config={
                "system_instruction": sistema,
                "response_mime_type": "application/json",
                "thinking_config": {"thinking_level": "low"},
                "max_output_tokens": 1024,
            },
        )
        return resposta.text or ""

    return chamar


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("relatorio", type=Path)
    parser.add_argument("--modelo", default="gemini-3.8-flash")
    parser.add_argument("--intervalo", type=float, default=2.0, help="segundos de pausa de cada chamada")
    parser.add_argument("--paralelas", type=int, default=3, help="chamadas ao mesmo tempo")
    argumentos = parser.parse_args()
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    dados = json.loads(argumentos.relatorio.read_text(encoding="utf-8"))
    banco = BancoDeQuestoes.de_arquivo(RAIZ / "data" / "questoes-mvp.json")
    base = argumentos.relatorio.with_suffix("")
    parcial = Path(f"{base}-juiz-parcial.json")
    # rodada interrompida: reaproveita o que já foi julgado
    ja_julgados = json.loads(parcial.read_text(encoding="utf-8")) if parcial.exists() else None

    def salvar_parcial(lista: list[dict]) -> None:
        parcial.write_text(json.dumps(lista, ensure_ascii=False), encoding="utf-8")

    julgados = julgar(
        dados["resultados"],
        banco,
        cliente_gemini(argumentos.modelo),
        argumentos.intervalo,
        argumentos.paralelas,
        ja_julgados=ja_julgados,
        ao_julgar=salvar_parcial,
    )
    resumo = resumir(julgados)

    Path(f"{base}-juiz.json").write_text(
        json.dumps({"resumo": resumo, "julgados": julgados}, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    texto = relatorio(resumo, julgados, argumentos.relatorio.name)
    Path(f"{base}-juiz.md").write_text(texto, encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=1))
    print(f"\nRelatório do juiz: {base}-juiz.md")
    total = resumo["julgadas"] + resumo["falhas_do_juiz"]
    if total and resumo["falhas_do_juiz"] / total > LIMITE_DE_FALHAS:
        sys.exit(f"O juiz falhou em {resumo['falhas_do_juiz']} de {total} julgamentos: esta rodada não vale.")


if __name__ == "__main__":
    main()
