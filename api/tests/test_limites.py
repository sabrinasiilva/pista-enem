"""Limites de uso: por IP, por sessão e cota diária da IA."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.config import Configuracoes
from app.limites import CotaDiaria, IAComCota, LimiteDeRequisicoes
from app.main import criar_app
from app.tutor import motor
from app.tutor.ia import ErroDaIA
from app.tutor.motor import Tutor
from app.tutor.questoes import BancoDeQuestoes
from tests.auxiliares import IAFalsa, questao_exemplo

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------- peças


def test_limite_de_requisicoes():
    limite = LimiteDeRequisicoes(maximo=2, janela_em_segundos=60)
    assert limite.permitir("a") and limite.permitir("a")
    assert not limite.permitir("a")
    assert limite.permitir("b")


def test_cota_diaria_vira_no_dia_seguinte():
    dia = [date(2026, 11, 18)]
    cota = CotaDiaria(2, relogio=lambda: dia[0])
    assert cota.consumir() and cota.consumir()
    assert not cota.consumir() and cota.esgotada
    dia[0] = date(2026, 11, 19)
    assert not cota.esgotada and cota.consumir()


async def test_sem_cota_o_tutor_usa_o_plano_b(prompts):
    ia = IAComCota(IAFalsa("pista da IA"), CotaDiaria(0))
    tutor = Tutor(BancoDeQuestoes([questao_exemplo()]), prompts, ia)
    sessao = tutor.nova_sessao("2099-140")
    resultado = await tutor.responder(sessao, "B")
    assert resultado.mensagem.texto == motor.PISTA_PADRAO_1
    assert resultado.mensagem.protecao == "plano_b"
    with pytest.raises(ErroDaIA):
        await ia.gerar("s", [("aluno", "oi")])


# ---------------------------------------------------------------- na API


@pytest.fixture
def montar(prompts, motor):
    abertos = []

    def _montar(cota: int = 100, **limites) -> TestClient:
        ia = IAComCota(IAFalsa(*["Que operação você usou?"] * 50), CotaDiaria(cota))
        tutor = Tutor(BancoDeQuestoes([questao_exemplo()]), prompts, ia)
        cliente = TestClient(criar_app(Configuracoes(**limites), tutor, motor), raise_server_exceptions=False)
        cliente.__enter__()
        abertos.append(cliente)
        return cliente

    yield _montar
    for cliente in abertos:
        cliente.__exit__(None, None, None)


def ip(endereco: str) -> dict:
    return {"True-Client-IP": endereco}


def abrir(cliente, cabecalhos=None) -> str:
    return cliente.post("/sessoes", json={"questao_id": "2099-140"}, headers=cabecalhos or {}).json()["id"]


def test_limite_por_ip_nas_acoes_com_ia(montar):
    cliente = montar(limite_ia_por_ip=2)
    for _ in range(2):
        sessao = abrir(cliente, ip("1.1.1.1"))
        assert (
            cliente.post(f"/sessoes/{sessao}/mensagens", json={"texto": "não sei"}, headers=ip("1.1.1.1")).status_code
            == 200
        )
    sessao = abrir(cliente, ip("1.1.1.1"))
    bloqueado = cliente.post(f"/sessoes/{sessao}/respostas", json={"alternativa": "B"}, headers=ip("1.1.1.1"))
    assert bloqueado.status_code == 429
    assert bloqueado.json()["erro"]["codigo"] == "muitas_requisicoes"
    assert bloqueado.headers["retry-after"] == "600"
    # outro aluno, em outro IP, não é afetado
    outra = abrir(cliente, ip("2.2.2.2"))
    assert (
        cliente.post(f"/sessoes/{outra}/respostas", json={"alternativa": "B"}, headers=ip("2.2.2.2")).status_code == 200
    )


def test_limite_por_sessao(montar):
    cliente = montar(limite_ia_por_sessao=2)
    sessao = abrir(cliente)
    for _ in range(2):
        assert cliente.post(f"/sessoes/{sessao}/mensagens", json={"texto": "e agora?"}).status_code == 200
    resposta = cliente.post(f"/sessoes/{sessao}/mensagens", json={"texto": "e agora?"})
    assert resposta.status_code == 429
    assert "Abra a questão de novo" in resposta.json()["erro"]["mensagem"]


def test_limite_de_sessoes_por_ip(montar):
    cliente = montar(limite_sessoes_por_ip=2)
    abrir(cliente, ip("3.3.3.3"))
    abrir(cliente, ip("3.3.3.3"))
    assert cliente.post("/sessoes", json={"questao_id": "2099-140"}, headers=ip("3.3.3.3")).status_code == 429


def test_health_avisa_quando_a_cota_acaba(montar):
    cliente = montar(cota=1)
    assert cliente.get("/health").json()["ia"] == "gemini"
    sessao = abrir(cliente)
    cliente.post(f"/sessoes/{sessao}/respostas", json={"alternativa": "B"})
    assert cliente.get("/health").json()["ia"] == "cota_esgotada"


def test_limite_de_login_e_por_ip_real(montar):
    """Antes, atrás do proxy, todos os alunos dividiam o mesmo IP: 5 erros de qualquer um bloqueavam todos."""
    cliente = montar()
    for numero in range(5):
        cliente.post("/contas/entrar", json={"apelido": f"alguem{numero}", "senha": "errada!!"}, headers=ip("6.6.6.6"))
    bloqueado = cliente.post("/contas/entrar", json={"apelido": "outro", "senha": "errada!!"}, headers=ip("6.6.6.6"))
    assert bloqueado.status_code == 429
    livre = cliente.post("/contas/entrar", json={"apelido": "outro", "senha": "errada!!"}, headers=ip("7.7.7.7"))
    assert livre.status_code == 401
