import pytest

from app.tutor.estados import Estado, TransicaoInvalida, apos_pedido_de_explicacao, apos_resposta


@pytest.mark.parametrize(
    ("estado", "acertou", "esperado"),
    [
        (Estado.RESPONDENDO, True, Estado.CONCLUIDA),
        (Estado.RESPONDENDO, False, Estado.PISTA_1),
        (Estado.PISTA_1, True, Estado.CONCLUIDA),
        (Estado.PISTA_1, False, Estado.PISTA_2),
        (Estado.PISTA_2, True, Estado.CONCLUIDA),
        (Estado.PISTA_2, False, Estado.EXPLICACAO),
    ],
)
def test_transicoes_apos_resposta(estado, acertou, esperado):
    assert apos_resposta(estado, acertou) == esperado


@pytest.mark.parametrize("estado", [Estado.EXPLICACAO, Estado.CONCLUIDA])
def test_nao_responde_depois_de_encerrada(estado):
    with pytest.raises(TransicaoInvalida) as erro:
        apos_resposta(estado, True)
    assert erro.value.codigo == "sessao_encerrada"


@pytest.mark.parametrize("estado", [Estado.PISTA_1, Estado.PISTA_2])
def test_explicacao_com_confirmacao(estado):
    assert apos_pedido_de_explicacao(estado, confirmado=True) == Estado.EXPLICACAO


def test_explicacao_exige_confirmacao():
    with pytest.raises(TransicaoInvalida) as erro:
        apos_pedido_de_explicacao(Estado.PISTA_1, confirmado=False)
    assert erro.value.codigo == "confirmacao_necessaria"


def test_explicacao_exige_uma_tentativa_antes():
    with pytest.raises(TransicaoInvalida) as erro:
        apos_pedido_de_explicacao(Estado.RESPONDENDO, confirmado=True)
    assert erro.value.codigo == "tente_antes"


@pytest.mark.parametrize("estado", [Estado.EXPLICACAO, Estado.CONCLUIDA])
def test_explicacao_depois_de_encerrada(estado):
    with pytest.raises(TransicaoInvalida):
        apos_pedido_de_explicacao(estado, confirmado=True)
