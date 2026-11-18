"""Testes do juiz automático (evals/juiz.py), com um modelo falso."""

import sys

import pytest

from app.config import RAIZ_DO_REPOSITORIO
from app.tutor.questoes import BancoDeQuestoes
from tests.auxiliares import questao_exemplo

sys.path.insert(0, str(RAIZ_DO_REPOSITORIO / "evals"))
import juiz  # noqa: E402


def fala(acao="marcou B", texto="Você somou ou multiplicou?", protegido=True, fixa=None, marcada="B"):
    return {"acao": acao, "texto": texto, "protegido": protegido, "fixa": fixa, "marcada": marcada}


def test_criterios_vem_do_arquivo_e_pedem_json():
    texto = juiz.criterios()
    assert "revela" in texto and "socratica" in texto and "diagnostico" in texto
    assert texto.startswith("Você avalia")


def test_pedido_leva_gabarito_e_engano_da_alternativa_marcada():
    pedido = juiz.montar_pedido(questao_exemplo(), fala())
    assert "GABARITO: C" in pedido
    assert "Somou em vez de multiplicar" in pedido
    assert "pista logo depois de marcar" in pedido


def test_interpretar_aceita_json_com_texto_em_volta_e_recusa_formato_errado():
    assert juiz.interpretar('ok {"revela": false, "socratica": true, "diagnostico": null, "justificativa": "x"}')[
        "socratica"
    ]
    with pytest.raises(ValueError):
        juiz.interpretar('{"revela": "não", "socratica": true}')


def test_julgar_ignora_mensagens_fixas_e_livres_e_conta_falhas():
    respostas = iter(['{"revela": false, "socratica": true, "diagnostico": true, "justificativa": "ok"}', "lixo"])

    async def chamar(sistema, pedido):
        return next(respostas)

    resultados = [
        {
            "id": "erro-01",
            "questao": "2099-140",
            "falas": [
                fala(),
                fala(acao="escreveu: qual a letra?", texto="Mensagem fixa", fixa="pedido da resposta"),
                fala(acao="escreveu: e agora?", marcada="B"),
                fala(protegido=False, texto="A resposta é C."),
            ],
        }
    ]
    julgados = juiz.julgar(resultados, BancoDeQuestoes([questao_exemplo()]), chamar)
    assert [j["fala"] for j in julgados] == [0, 2]
    resumo = juiz.resumir(julgados)
    assert resumo == {
        "julgadas": 1,
        "falhas_do_juiz": 1,
        "revelam": 0,
        "socraticas": 1,
        "pistas_com_diagnostico": 1,
        "diagnostico_certo": 1,
    }
    assert "Amostra para a revisão humana" in juiz.relatorio(resumo, julgados, "teste.json")


def test_diagnostico_so_conta_em_pista_depois_de_marcar():
    async def chamar(sistema, pedido):
        return '{"revela": false, "socratica": true, "diagnostico": false, "justificativa": "x"}'

    resultados = [{"id": "m-01", "questao": "2099-140", "falas": [fala(acao="escreveu: me ajuda")]}]
    assert juiz.julgar(resultados, BancoDeQuestoes([questao_exemplo()]), chamar)[0]["diagnostico"] is None


def test_julgar_reaproveita_o_que_ja_foi_julgado_e_salva_o_progresso():
    chamadas = []

    async def chamar(sistema, pedido):
        chamadas.append(pedido)
        return '{"revela": false, "socratica": true, "diagnostico": true, "justificativa": "ok"}'

    resultados = [{"id": "erro-01", "questao": "2099-140", "falas": [fala(), fala(acao="marcou D", marcada="D")]}]
    ja = [
        {
            "caso": "erro-01",
            "questao": "2099-140",
            "fala": 0,
            "acao": "marcou B",
            "texto": "x",
            "revela": False,
            "socratica": False,
            "diagnostico": False,
            "justificativa": "antigo",
        }
    ]
    salvos = []
    julgados = juiz.julgar(
        resultados, BancoDeQuestoes([questao_exemplo()]), chamar, ja_julgados=ja, ao_julgar=salvos.append
    )
    assert len(chamadas) == 1
    assert [j["justificativa"] for j in julgados] == ["antigo", "ok"]
    assert len(salvos[-1]) == 2


def test_julgamento_que_estoura_o_tempo_vira_falha():
    import asyncio

    async def chamar(sistema, pedido):
        await asyncio.sleep(1)
        return "{}"

    resultados = [{"id": "erro-01", "questao": "2099-140", "falas": [fala()]}]
    julgados = juiz.julgar(resultados, BancoDeQuestoes([questao_exemplo()]), chamar, tempo_limite=0.01)
    assert "TimeoutError" in julgados[0]["erro"]


def test_para_de_chamar_quando_a_cota_acaba():
    chamadas = []

    async def chamar(sistema, pedido):
        chamadas.append(pedido)
        raise RuntimeError("429 RESOURCE_EXHAUSTED. You exceeded your current quota")

    resultados = [{"id": "erro-01", "questao": "2099-140", "falas": [fala(), fala(acao="marcou D", marcada="D")]}]
    julgados = juiz.julgar(resultados, BancoDeQuestoes([questao_exemplo()]), chamar, paralelas=1)
    assert len(chamadas) == 1
    assert "não julgado" in julgados[1]["erro"]
