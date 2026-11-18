import pytest

from app.esquemas import texto_simples


@pytest.mark.parametrize(
    ("markdown", "esperado"),
    [
        ("Custa R\\$ 1,35 bilhão.", "Custa R$ 1,35 bilhão."),
        ("Dígitos $N_1$, $N_2$ e $N_3$.", "Dígitos N1, N2 e N3."),
        ("Vale $\\frac{2}{3}$ do total.", "Vale 2/3 do total."),
        ("Área $2 \\times 3$.", "Área 2 × 3."),
        ("Veja o quadro.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\nQual é?", "Veja o quadro. Qual é?"),
        ("Texto **forte** aqui.", "Texto forte aqui."),
    ],
)
def test_texto_simples(markdown, esperado):
    assert texto_simples(markdown) == esperado


def test_texto_simples_corta_em_palavra_inteira():
    resultado = texto_simples("palavra " * 40, limite=30)
    assert resultado.endswith("…")
    assert len(resultado) <= 31
    assert "palavr…" not in resultado


def test_previas_reais_nao_tem_latex_nem_tabela(banco_real):
    from app.esquemas import QuestaoResumo

    for questao in banco_real.listar():
        previa = QuestaoResumo.de(questao).inicio_do_enunciado
        assert "\\" not in previa and "|" not in previa, questao.id
        assert previa.count("$") == previa.count("R$"), questao.id
