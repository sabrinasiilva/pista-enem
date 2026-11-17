import asyncio
from types import SimpleNamespace

import pytest

from app.tutor.ia import ClienteGemini, ErroDaIA

pytestmark = pytest.mark.anyio


class ErroComCodigo(Exception):
    def __init__(self, code: int):
        super().__init__(f"HTTP {code}")
        self.code = code


class ModelosFalsos:
    """Imita client.aio.models do SDK do Gemini."""

    def __init__(self, *efeitos):
        self.efeitos = list(efeitos)
        self.chamadas: list[str] = []

    async def generate_content(self, model, contents, config):
        self.chamadas.append(model)
        efeito = self.efeitos.pop(0)
        if isinstance(efeito, Exception):
            raise efeito
        if efeito == "demora":
            await asyncio.sleep(1)
        return SimpleNamespace(text=efeito, usage_metadata=SimpleNamespace(total_token_count=42))

    async def generate_content_stream(self, model, contents, config):
        self.chamadas.append(model)
        efeito = self.efeitos.pop(0)
        if isinstance(efeito, Exception):
            raise efeito

        async def fluxo():
            for palavra in efeito.split(" "):
                yield SimpleNamespace(text=palavra + " ")

        return fluxo()


def cliente(*efeitos, modelos=("principal", "reserva"), tentativas=2):
    falsos = ModelosFalsos(*efeitos)
    gemini = ClienteGemini(
        chave="falsa",
        modelos=modelos,
        tempo_limite=0.05,
        tentativas_por_modelo=tentativas,
        espera_inicial=0,
        cliente=SimpleNamespace(aio=SimpleNamespace(models=falsos)),
    )
    return gemini, falsos


async def test_sucesso_na_primeira():
    gemini, falsos = cliente("Olá")
    resposta = await gemini.gerar("sistema", [("aluno", "oi")])
    assert resposta.texto == "Olá"
    assert resposta.modelo == "principal"
    assert resposta.tokens == 42
    assert falsos.chamadas == ["principal"]


async def test_tenta_de_novo_depois_de_erro_temporario():
    gemini, falsos = cliente(ErroComCodigo(503), "Olá")
    assert (await gemini.gerar("s", [("aluno", "oi")])).texto == "Olá"
    assert falsos.chamadas == ["principal", "principal"]


async def test_tempo_limite_conta_como_falha():
    gemini, falsos = cliente("demora", "Olá")
    assert (await gemini.gerar("s", [("aluno", "oi")])).texto == "Olá"
    assert falsos.chamadas == ["principal", "principal"]


async def test_usa_o_modelo_reserva_quando_o_principal_falha():
    gemini, falsos = cliente(ErroComCodigo(503), ErroComCodigo(429), "Olá")
    resposta = await gemini.gerar("s", [("aluno", "oi")])
    assert resposta.modelo == "reserva"
    assert falsos.chamadas == ["principal", "principal", "reserva"]


async def test_erro_definitivo_nao_repete_no_mesmo_modelo():
    gemini, falsos = cliente(ErroComCodigo(400), "Olá")
    await gemini.gerar("s", [("aluno", "oi")])
    assert falsos.chamadas == ["principal", "reserva"]


async def test_resposta_vazia_conta_como_falha():
    gemini, _ = cliente("", "Olá")
    assert (await gemini.gerar("s", [("aluno", "oi")])).texto == "Olá"


async def test_todos_falham_levanta_erro_da_ia():
    gemini, _ = cliente(*[ErroComCodigo(503)] * 4)
    with pytest.raises(ErroDaIA):
        await gemini.gerar("s", [("aluno", "oi")])


async def test_streaming_entrega_trechos():
    gemini, _ = cliente("uma resposta em partes")
    trechos = [t async for t in gemini.gerar_em_trechos("s", [("aluno", "oi")])]
    assert "".join(trechos).strip() == "uma resposta em partes"


async def test_streaming_usa_reserva_se_falhar_antes_de_comecar():
    gemini, falsos = cliente(ErroComCodigo(503), "ok")
    trechos = [t async for t in gemini.gerar_em_trechos("s", [("aluno", "oi")])]
    assert "".join(trechos).strip() == "ok"
    assert falsos.chamadas == ["principal", "reserva"]


def test_exige_pelo_menos_um_modelo():
    with pytest.raises(ValueError):
        ClienteGemini(chave="x", modelos=[], cliente=object())


def test_converte_papeis_para_o_formato_do_gemini():
    from app.tutor.ia import _conteudos

    assert _conteudos([("aluno", "oi"), ("tutor", "olá")]) == [
        {"role": "user", "parts": [{"text": "oi"}]},
        {"role": "model", "parts": [{"text": "olá"}]},
    ]
