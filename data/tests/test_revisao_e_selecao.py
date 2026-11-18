import selecionar
import validar_revisao


def revisao_valida(**mudancas):
    revisao = {
        "id": "2023-150",
        "enunciado": "Qual é o valor de $\\frac{1}{2}$ de 10?",
        "alternativas": {"A": "2", "B": "5", "C": "10", "D": "20", "E": "50"},
        "depende_de_figura": False,
        "observacao_transcricao": "",
        "gabarito_calculado": "B",
        "resolucao": "Metade de 10 é 5.\nAlternativa B.",
        "enganos": {"A": "Dividiu por 5.", "C": "Ignorou a fração.", "D": "Multiplicou por 2.", "E": "Multiplicou por 5."},
        "conceitos": ["frações"],
    }
    revisao.update(mudancas)
    return revisao


# ---------------------------------------------------------------- validador

def test_revisao_valida_nao_tem_problemas():
    assert validar_revisao.problemas_da_revisao(revisao_valida()) == []


def test_enganos_precisam_cobrir_exatamente_as_alternativas_erradas():
    revisao = revisao_valida(enganos={"A": "x", "B": "y", "C": "z", "D": "w"})
    assert any("enganos" in p for p in validar_revisao.problemas_da_revisao(revisao))


def test_detecta_barra_invertida_sem_escape():
    # "\frac" sem escape no JSON vira o caractere \x0c seguido de "rac"
    revisao = revisao_valida(enunciado="Valor de $\x0crac{1}{2}$")
    assert any("controle" in p for p in validar_revisao.problemas_da_revisao(revisao))


def test_detecta_quebra_de_linha_dentro_de_formula():
    revisao = revisao_valida(enunciado="Se $x \neq 2$")  # \n de \neq virou quebra de linha
    assert any("quebra de linha" in p for p in validar_revisao.problemas_da_revisao(revisao))


def test_detecta_cifrao_desbalanceado():
    revisao = revisao_valida(enunciado="Valor de $x")
    assert any("ímpar" in p for p in validar_revisao.problemas_da_revisao(revisao))


def test_cifrao_escapado_nao_conta_como_formula():
    revisao = revisao_valida(enunciado="Na região $R$, custa R\\$ 2,00 e a senha tem \\$ e $p_1$.")
    assert validar_revisao.problemas_da_revisao(revisao) == []


def test_dinheiro_com_cifrao_sem_escape_e_problema():
    revisao = revisao_valida(enunciado="Custa R$ 2,00.")
    assert any("dinheiro" in p for p in validar_revisao.problemas_da_revisao(revisao))


# ---------------------------------------------------------------- seleção

def test_sem_latex_remove_comandos_para_comparar_com_pdf():
    assert selecionar.sem_latex("$\\frac{1}{2}$").split() == ["1", "2"]


def test_exclui_quando_resolucao_diverge_do_gabarito_oficial():
    questao_oficial = {"anulada": False, "tem_imagem": False, "gabarito": "C",
                       "conferencia": {"item_igual_nos_cadernos_regulares": True}}
    motivos = selecionar.motivos_de_exclusao(questao_oficial, revisao_valida(), 0.95)
    assert motivos == ["resolução chegou em B, gabarito oficial é C"]


def test_exclui_transcricao_muito_diferente_do_pdf():
    questao_oficial = {"anulada": False, "tem_imagem": False, "gabarito": "B",
                       "conferencia": {"item_igual_nos_cadernos_regulares": True}}
    assert selecionar.motivos_de_exclusao(questao_oficial, revisao_valida(), 0.5) == ["transcrição só 50% parecida com o PDF"]


def test_aceita_id_de_natureza_e_de_matematica():
    assert validar_revisao.problemas_da_revisao(revisao_valida(id="2022-91")) == []
    assert validar_revisao.problemas_da_revisao(revisao_valida(id="2025-180")) == []
    assert "id inválido" in validar_revisao.problemas_da_revisao(revisao_valida(id="2022-90"))
    assert "id inválido" in validar_revisao.problemas_da_revisao(revisao_valida(id="2022-181"))
