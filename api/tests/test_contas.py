"""Testes de integração das contas, do perfil e do progresso."""

from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.banco import Acesso, Resultado
from app.config import Configuracoes
from app.main import criar_app
from app.tutor.motor import Tutor
from app.tutor.questoes import BancoDeQuestoes
from tests.auxiliares import questao_exemplo

SENHA = "girassol-azul-42"


@pytest.fixture
def cliente(prompts, motor):
    banco_de_questoes = BancoDeQuestoes(
        [questao_exemplo(), questao_exemplo(id="2099-141", numero=141, habilidade="H16")]
    )
    tutor = Tutor(banco_de_questoes, prompts, None)  # sem IA: respostas do plano B
    with TestClient(criar_app(Configuracoes(), tutor, motor), raise_server_exceptions=False) as cliente:
        yield cliente


def cadastrar(cliente, apelido="estudante_1", senha=SENHA, **extras) -> dict:
    resposta = cliente.post("/contas", json={"apelido": apelido, "senha": senha, **extras})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def autorizacao(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def resolver(cliente, token, questao="2099-140", letras=("C",)) -> str:
    sessao = cliente.post("/sessoes", json={"questao_id": questao}, headers=autorizacao(token)).json()["id"]
    for letra in letras:
        cliente.post(f"/sessoes/{sessao}/respostas", json={"alternativa": letra}, headers=autorizacao(token))
    return sessao


# ---------------------------------------------------------------- cadastro e login


def test_cadastro_devolve_token_e_codigo_de_recuperacao(cliente):
    corpo = cadastrar(cliente, "Ana.Estuda", meta_semanal=15, habilidades_foco=["H16", "H3", "H16"])
    assert corpo["token"]
    assert len(corpo["codigo_de_recuperacao"]) == 19  # XXXX-XXXX-XXXX-XXXX
    assert corpo["usuario"]["apelido"] == "ana.estuda"
    assert corpo["usuario"]["meta_semanal"] == 15
    assert corpo["usuario"]["habilidades_foco"] == ["H16", "H3"]
    assert corpo["usuario"]["tema"] == "sistema"
    assert "senha" not in str(corpo["usuario"])


@pytest.mark.parametrize("apelido", ["ab", "nome com espaço", "maria@email.com", "joão", "x" * 21])
def test_apelido_invalido(cliente, apelido):
    resposta = cliente.post("/contas", json={"apelido": apelido, "senha": SENHA})
    assert resposta.status_code == 422


@pytest.mark.parametrize("senha", ["12345678", "aaaaaaaa", "estudante_1-forte", "curta"])
def test_senha_fraca(cliente, senha):
    resposta = cliente.post("/contas", json={"apelido": "estudante_1", "senha": senha})
    assert resposta.status_code == 422


def test_apelido_em_uso_sem_diferenciar_maiusculas(cliente):
    cadastrar(cliente, "estudante_1")
    resposta = cliente.post("/contas", json={"apelido": "ESTUDANTE_1", "senha": SENHA})
    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "apelido_em_uso"


def test_habilidade_invalida_no_foco(cliente):
    resposta = cliente.post("/contas", json={"apelido": "estudante_1", "senha": SENHA, "habilidades_foco": ["H99"]})
    assert resposta.status_code == 422


def test_entrar_e_sair(cliente):
    cadastrar(cliente)
    corpo = cliente.post("/contas/entrar", json={"apelido": "Estudante_1", "senha": SENHA}).json()
    token = corpo["token"]
    assert corpo["codigo_de_recuperacao"] is None
    assert cliente.get("/eu", headers=autorizacao(token)).status_code == 200
    assert cliente.post("/contas/sair", headers=autorizacao(token)).status_code == 204
    resposta = cliente.get("/eu", headers=autorizacao(token))
    assert resposta.status_code == 401
    assert resposta.json()["erro"]["codigo"] == "sessao_expirada"


def test_mesma_mensagem_para_apelido_inexistente_e_senha_errada(cliente):
    cadastrar(cliente)
    errada = cliente.post("/contas/entrar", json={"apelido": "estudante_1", "senha": "outra-senha-qualquer"})
    inexistente = cliente.post("/contas/entrar", json={"apelido": "ninguem", "senha": SENHA})
    assert errada.status_code == inexistente.status_code == 401
    assert errada.json() == inexistente.json()


def test_limite_de_tentativas_de_login(cliente):
    cadastrar(cliente)
    for _ in range(5):
        cliente.post("/contas/entrar", json={"apelido": "estudante_1", "senha": "errada-errada"})
    resposta = cliente.post("/contas/entrar", json={"apelido": "estudante_1", "senha": SENHA})
    assert resposta.status_code == 429
    assert resposta.json()["erro"]["codigo"] == "tentativas_demais"


def test_sem_token_nao_acessa_o_perfil(cliente):
    resposta = cliente.get("/eu")
    assert resposta.status_code == 401
    assert resposta.json()["erro"]["codigo"] == "login_necessario"
    assert resposta.headers["www-authenticate"] == "Bearer"


def test_token_expirado(cliente, motor):
    token = cadastrar(cliente)["token"]
    with Session(motor) as banco:
        for acesso in banco.scalars(select(Acesso)):
            acesso.expira_em = acesso.expira_em - timedelta(days=31)
        banco.commit()
    assert cliente.get("/eu", headers=autorizacao(token)).status_code == 401


def test_token_nunca_fica_no_banco(cliente, motor):
    token = cadastrar(cliente)["token"]
    with Session(motor) as banco:
        hashes = list(banco.scalars(select(Acesso.token_hash)))
    assert token not in hashes and len(hashes) == 1


# ---------------------------------------------------------------- recuperação e senha


def test_recuperar_com_codigo(cliente):
    corpo = cadastrar(cliente)
    outro_aparelho = cliente.post("/contas/entrar", json={"apelido": "estudante_1", "senha": SENHA}).json()["token"]
    codigo = corpo["codigo_de_recuperacao"].lower().replace("-", "")  # aceita sem hífen e em minúsculas

    recuperado = cliente.post(
        "/contas/recuperar",
        json={"apelido": "estudante_1", "codigo_de_recuperacao": codigo, "nova_senha": "nova-senha-segura"},
    )
    assert recuperado.status_code == 200
    novo_codigo = recuperado.json()["codigo_de_recuperacao"]
    assert novo_codigo and novo_codigo != corpo["codigo_de_recuperacao"]
    assert cliente.get("/eu", headers=autorizacao(outro_aparelho)).status_code == 401  # aparelhos derrubados
    assert (
        cliente.post("/contas/entrar", json={"apelido": "estudante_1", "senha": "nova-senha-segura"}).status_code == 200
    )

    # o código antigo não vale mais
    de_novo = cliente.post(
        "/contas/recuperar",
        json={"apelido": "estudante_1", "codigo_de_recuperacao": codigo, "nova_senha": "outra-senha-boa"},
    )
    assert de_novo.status_code == 401


def test_trocar_senha_mantem_so_este_aparelho(cliente):
    token = cadastrar(cliente)["token"]
    outro = cliente.post("/contas/entrar", json={"apelido": "estudante_1", "senha": SENHA}).json()["token"]
    errada = cliente.put(
        "/eu/senha", json={"senha_atual": "errada!!", "nova_senha": "nova-senha-segura"}, headers=autorizacao(token)
    )
    assert errada.status_code == 401
    certa = cliente.put(
        "/eu/senha", json={"senha_atual": SENHA, "nova_senha": "nova-senha-segura"}, headers=autorizacao(token)
    )
    assert certa.status_code == 204
    assert cliente.get("/eu", headers=autorizacao(token)).status_code == 200
    assert cliente.get("/eu", headers=autorizacao(outro)).status_code == 401


# ---------------------------------------------------------------- perfil


def test_atualizar_perfil(cliente):
    token = cadastrar(cliente)["token"]
    corpo = cliente.patch(
        "/eu",
        json={"meta_semanal": 20, "habilidades_foco": ["H21", "H1"], "tema": "escuro"},
        headers=autorizacao(token),
    ).json()
    assert corpo["meta_semanal"] == 20
    assert corpo["habilidades_foco"] == ["H1", "H21"]
    assert corpo["tema"] == "escuro"
    assert cliente.patch("/eu", json={"tema": "roxo"}, headers=autorizacao(token)).status_code == 422


def test_apagar_conta_apaga_o_historico(cliente, motor):
    token = cadastrar(cliente)["token"]
    resolver(cliente, token)
    assert cliente.request("DELETE", "/eu", json={"senha": "errada!!"}, headers=autorizacao(token)).status_code == 401
    assert cliente.request("DELETE", "/eu", json={"senha": SENHA}, headers=autorizacao(token)).status_code == 204
    with Session(motor) as banco:
        assert banco.scalar(select(func.count()).select_from(Resultado)) == 0
        assert banco.scalar(select(func.count()).select_from(Acesso)) == 0
    assert cliente.post("/contas/entrar", json={"apelido": "estudante_1", "senha": SENHA}).status_code == 401


# ---------------------------------------------------------------- sessões e progresso


def test_sessao_da_conta_grava_o_resultado_uma_vez(cliente, motor):
    token = cadastrar(cliente)["token"]
    sessao = resolver(cliente, token, letras=("B", "C"))  # errou e depois acertou
    cliente.post(f"/sessoes/{sessao}/mensagens", json={"texto": "por quê?"}, headers=autorizacao(token))
    with Session(motor) as banco:
        resultados = list(banco.scalars(select(Resultado)))
    assert len(resultados) == 1
    assert resultados[0].acertou and not resultados[0].acertou_de_primeira
    assert resultados[0].tentativas == 2


def test_sessao_anonima_nao_grava_nada(cliente, motor):
    sessao = cliente.post("/sessoes", json={"questao_id": "2099-140"}).json()["id"]
    cliente.post(f"/sessoes/{sessao}/respostas", json={"alternativa": "C"})
    with Session(motor) as banco:
        assert banco.scalar(select(func.count()).select_from(Resultado)) == 0


def test_sessao_de_uma_conta_e_invisivel_para_outras(cliente):
    dona = cadastrar(cliente, "dona_da_sessao")["token"]
    outra = cadastrar(cliente, "outra_pessoa")["token"]
    sessao = cliente.post("/sessoes", json={"questao_id": "2099-140"}, headers=autorizacao(dona)).json()["id"]
    assert cliente.get(f"/sessoes/{sessao}", headers=autorizacao(outra)).status_code == 404
    assert cliente.get(f"/sessoes/{sessao}").status_code == 404
    assert (
        cliente.post(f"/sessoes/{sessao}/respostas", json={"alternativa": "C"}, headers=autorizacao(outra)).status_code
        == 404
    )
    assert cliente.get(f"/sessoes/{sessao}", headers=autorizacao(dona)).status_code == 200


def test_explicacao_tambem_grava_resultado(cliente):
    token = cadastrar(cliente)["token"]
    sessao = resolver(cliente, token, letras=("B",))
    cliente.post(f"/sessoes/{sessao}/explicacao", json={"confirmar": True}, headers=autorizacao(token))
    progresso = cliente.get("/eu/progresso", headers=autorizacao(token)).json()
    assert progresso["recentes"][0]["pediu_explicacao"] is True


def test_progresso(cliente):
    token = cadastrar(cliente, meta_semanal=3)["token"]
    resolver(cliente, token, "2099-140", ("C",))  # acerto de primeira
    resolver(cliente, token, "2099-141", ("A", "C"))  # acerto depois de errar
    corpo = cliente.get("/eu/progresso", headers=autorizacao(token)).json()
    assert corpo["total_de_questoes"] == 2
    assert corpo["acertos_de_primeira"] == 1
    assert corpo["feitas_na_semana"] == 2
    assert corpo["meta_semanal"] == 3
    assert corpo["sequencia_de_dias"] == 1
    habilidades = {h["codigo"]: h for h in corpo["por_habilidade"]}
    assert habilidades["H3"]["acertos_de_primeira"] == 1
    assert habilidades["H16"] == {**habilidades["H16"], "feitas": 1, "acertos_de_primeira": 0}


def test_revisar_lista_so_o_que_nao_foi_acertado_de_primeira(cliente):
    token = cadastrar(cliente)["token"]
    resolver(cliente, token, "2099-140", ("C",))
    resolver(cliente, token, "2099-141", ("A", "C"))
    revisar = cliente.get("/eu/revisar", headers=autorizacao(token)).json()
    assert [r["questao"]["id"] for r in revisar] == ["2099-141"]
    # refez e acertou de primeira: sai da lista
    resolver(cliente, token, "2099-141", ("C",))
    assert cliente.get("/eu/revisar", headers=autorizacao(token)).json() == []


def test_recomendacoes_priorizam_revisao_e_foco(cliente):
    token = cadastrar(cliente, habilidades_foco=["H16"])["token"]
    resolver(cliente, token, "2099-140", ("A", "C"))  # H3, errou primeiro: vai para revisão
    ids = [q["id"] for q in cliente.get("/recomendacoes", params={"quantidade": 2}, headers=autorizacao(token)).json()]
    assert ids == ["2099-140", "2099-141"]


def test_recomendacoes_sem_conta_filtram_por_habilidade(cliente):
    ids = [q["id"] for q in cliente.get("/recomendacoes", params={"quantidade": 1, "habilidades": "H16"}).json()]
    assert ids == ["2099-141"]
