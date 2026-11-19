"""Questões com figura: a API entrega a imagem, o tutor recebe a imagem e a descrição."""

from __future__ import annotations

import pytest

from app.tutor.ia import _conteudos
from app.tutor.questoes import BancoDeQuestoes, Figura
from tests.auxiliares import questao_exemplo

PNG = b"\x89PNG\r\n\x1a\nfigura-de-teste"
DESCRICAO = "Gráfico de barras com o preço por hora em cada dia da semana."


@pytest.fixture
def banco_com_figura(tmp_path):
    (tmp_path / "2099-140-1.png").write_bytes(PNG)
    questao = questao_exemplo(figuras=(Figura("2099-140-1.png", DESCRICAO),))
    return BancoDeQuestoes([questao], tmp_path)


def test_questao_traz_a_figura_com_descricao(montar, banco_com_figura):
    cliente, _ = montar(banco=banco_com_figura)
    dados = cliente.get("/questoes/2099-140").json()
    assert dados["figuras"] == [{"url": "/questoes/2099-140/figuras/1", "descricao": DESCRICAO}]


def test_rota_entrega_o_png_com_cache(montar, banco_com_figura):
    cliente, _ = montar(banco=banco_com_figura)
    resposta = cliente.get("/questoes/2099-140/figuras/1")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "image/png"
    assert resposta.headers["cache-control"] == "public, max-age=86400"
    assert resposta.content == PNG
    assert cliente.get("/questoes/2099-140/figuras/2").status_code == 404


def test_questao_sem_figura_tem_lista_vazia(montar):
    cliente, _ = montar()
    assert cliente.get("/questoes/2099-140").json()["figuras"] == []


def test_tutor_manda_a_imagem_e_a_descricao_para_a_ia(montar, banco_com_figura):
    cliente, ia = montar("Pense de novo: o que o gráfico mostra?", banco=banco_com_figura)
    sessao = cliente.post("/sessoes", json={"questao_id": "2099-140"}).json()["id"]
    cliente.post(f"/sessoes/{sessao}/respostas", json={"alternativa": "B"})
    assert ia.imagens_recebidas == [[PNG]]
    sistema = ia.chamadas[0][0]
    assert f"[Figura 1: {DESCRICAO}]" in sistema


def test_imagens_vao_no_primeiro_turno_do_aluno():
    conteudos = _conteudos([("tutor", "Oi"), ("aluno", "marquei B"), ("aluno", "e agora?")], [PNG])
    assert conteudos[0]["parts"] == [{"text": "Oi"}]
    assert conteudos[1]["parts"][0] == {"inline_data": {"mime_type": "image/png", "data": PNG}}
    assert conteudos[1]["parts"][1] == {"text": "marquei B"}
    assert len(conteudos[2]["parts"]) == 1
