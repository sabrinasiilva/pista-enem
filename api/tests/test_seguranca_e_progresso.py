from datetime import UTC, date, datetime, timedelta

from app import seguranca
from app.banco import Resultado
from app.limites import LimiteDeTentativas
from app.progresso import dia_local, inicio_da_semana, sequencia_de_dias


def test_hash_confere_so_com_o_segredo_certo():
    guardado = seguranca.gerar_hash("minha-senha")
    assert guardado.startswith("scrypt$")
    assert seguranca.conferir_hash("minha-senha", guardado)
    assert not seguranca.conferir_hash("outra-senha", guardado)
    assert not seguranca.conferir_hash("minha-senha", "lixo")


def test_mesma_senha_gera_hashes_diferentes():
    assert seguranca.gerar_hash("igual") != seguranca.gerar_hash("igual")


def test_codigo_de_recuperacao_sem_letras_ambiguas():
    codigos = {seguranca.gerar_codigo_de_recuperacao() for _ in range(50)}
    assert len(codigos) == 50
    for codigo in codigos:
        assert len(codigo) == 19 and codigo.count("-") == 3
        assert not set(codigo) & set("01OIL")


def test_normalizar_codigo():
    assert seguranca.normalizar_codigo(" abcd efgh-jkmnpqrs ") == "ABCD-EFGH-JKMN-PQRS"


def test_limite_de_tentativas():
    limite = LimiteDeTentativas(maximo=2)
    assert not limite.bloqueado("a")
    limite.registrar_falha("a", "ip")
    limite.registrar_falha("a", "ip")
    assert limite.bloqueado("a") and limite.bloqueado("b", "ip")
    limite.zerar("a")
    assert not limite.bloqueado("a")


def resultado_em(dia: date) -> Resultado:
    momento = datetime(dia.year, dia.month, dia.day, 15, tzinfo=UTC)  # meio-dia em Brasília
    return Resultado(concluido_em=momento)


def test_sequencia_de_dias():
    hoje = date(2026, 11, 18)
    dias = [hoje, hoje - timedelta(days=1), hoje - timedelta(days=2), hoje - timedelta(days=4)]
    assert sequencia_de_dias([resultado_em(d) for d in dias], hoje) == 3


def test_sequencia_continua_se_hoje_ainda_nao_estudou():
    hoje = date(2026, 11, 18)
    assert sequencia_de_dias([resultado_em(hoje - timedelta(days=1))], hoje) == 1
    assert sequencia_de_dias([resultado_em(hoje - timedelta(days=2))], hoje) == 0


def test_dia_usa_o_horario_de_brasilia():
    # 01:00 UTC do dia 18 ainda é dia 17 em Brasília
    assert dia_local(datetime(2026, 11, 18, 1, tzinfo=UTC)) == date(2026, 11, 17)
    assert dia_local(datetime(2026, 11, 18, 1)) == date(2026, 11, 17)  # sem fuso: tratado como UTC


def test_semana_comeca_na_segunda():
    assert inicio_da_semana(date(2026, 11, 22)) == date(2026, 11, 16)  # domingo -> segunda anterior
