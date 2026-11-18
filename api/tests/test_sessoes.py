from datetime import timedelta

import pytest

from app.sessoes import RepositorioDeSessoes, SessaoNaoEncontrada
from app.tutor.sessao import Sessao, agora


def nova(**campos) -> Sessao:
    return Sessao("2099-140", "tutor_v1", **campos)


def test_guarda_e_obtem():
    repositorio = RepositorioDeSessoes()
    sessao = nova()
    repositorio.guardar(sessao)
    obtida, trava = repositorio.obter(sessao.id)
    assert obtida is sessao
    assert trava is repositorio.obter(sessao.id)[1]  # o mesmo lock para a mesma sessão


def test_sessao_expirada_nao_e_encontrada():
    repositorio = RepositorioDeSessoes(validade=timedelta(hours=1))
    velha = nova(criada_em=agora() - timedelta(hours=2))
    repositorio.guardar(velha)
    with pytest.raises(SessaoNaoEncontrada):
        repositorio.obter(velha.id)


def test_descarta_a_mais_antiga_quando_chega_no_limite():
    repositorio = RepositorioDeSessoes(maximo=2)
    primeira = nova(criada_em=agora() - timedelta(minutes=3))
    segunda = nova(criada_em=agora() - timedelta(minutes=2))
    terceira = nova()
    for sessao in (primeira, segunda, terceira):
        repositorio.guardar(sessao)
    assert len(repositorio) == 2
    with pytest.raises(SessaoNaoEncontrada):
        repositorio.obter(primeira.id)


def test_ids_sao_aleatorios_e_unicos():
    assert len({nova().id for _ in range(100)}) == 100
