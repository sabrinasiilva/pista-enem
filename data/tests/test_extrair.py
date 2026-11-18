import extrair


def item(posicao, gabarito, prova="1", cor="AZUL", adaptado="0", codigo=None, habilidade="5",
         anulado="0", motivo="", parametro_b="1.5"):
    return {
        "CO_POSICAO": str(posicao), "SG_AREA": "MT", "CO_ITEM": codigo or f"9{posicao}",
        "TX_GABARITO": gabarito, "CO_HABILIDADE": habilidade, "IN_ITEM_ABAN": anulado,
        "TX_MOTIVO_ABAN": motivo, "NU_PARAM_B": parametro_b, "TX_COR": cor,
        "CO_PROVA": prova, "IN_ITEM_ADAPTADO": adaptado,
    }


# ---------------------------------------------------------------- texto

def test_normalizar_ignora_acentos_pontuacao_e_espacos():
    assert extrair.normalizar("Questão: R$ 1,35 bilhão!") == "questaor135bilhao"


def test_similaridade_de_textos_iguais_apesar_da_formatacao():
    assert extrair.similaridade("1 350 000,00", "1350000,00") == 1.0


def test_similaridade_de_textos_diferentes_e_baixa():
    assert extrair.similaridade("I.", "1") == 0.0


# ---------------------------------------------------------------- PDF

FORMATO_ANTIGO = (
    "Se a pessoa pretende gastar o mínimo possível, irá contratar o operário\n"
    "A\t\nA\t I.\nB\t\nB\t II.\nC\t\nC\t III.\nD\t\nD\t IV.\nE\t\nE\t V.\n18\n"
)

FORMATO_NOVO = (
    "Qual é a massa, em grama, dessa escultura?\n"
    "A 1 198,8\nB 1 296,0\nC 1 360,8\nD 4 665,6\nE\n4 860,0\n22\n"
)


def test_separa_alternativas_no_formato_com_letra_repetida():
    enunciado, alternativas = extrair.separar_alternativas(FORMATO_ANTIGO)
    assert enunciado.endswith("irá contratar o operário")
    assert alternativas == ["I.", "II.", "III.", "IV.", "V."]


def test_separa_alternativas_com_letra_sozinha_e_remove_numero_da_pagina():
    enunciado, alternativas = extrair.separar_alternativas(FORMATO_NOVO)
    assert enunciado == "Qual é a massa, em grama, dessa escultura?"
    assert alternativas == ["1 198,8", "1 296,0", "1 360,8", "4 665,6", "4 860,0"]


def test_sem_as_cinco_alternativas_devolve_none():
    assert extrair.separar_alternativas("Enunciado\nA 1\nB 2\nC 3\n") is None


def test_limpar_pagina_remove_marca_dagua_cabecalho_e_rodape():
    pagina = (
        "ENEM 2022 ENEM 2022 ENEM 2022 ENEM 2022\n"
        "• MATEMÁTICA E SUAS TECNOLOGIAS • 2º DIA • CADERNO 8 • VERDE\n"
        "*020425VE32*\n"
        "MT - 2° dia | Caderno 6 - CINZA - 1ª Aplicação\n"
        "Texto da questão\n"
    )
    assert extrair.limpar_pagina(pagina) == "Texto da questão"


def test_blocos_por_questao_separa_pelo_numero():
    texto = "capa\nQUESTÃO 136\nprimeira\nQUESTÃO 137\t\nsegunda\n"
    blocos = extrair.blocos_por_questao(texto)
    assert blocos[136].strip() == "primeira"
    assert blocos[137].strip() == "segunda"


# ---------------------------------------------------------------- microdados

def test_itens_por_posicao_usa_so_cadernos_regulares_na_mesma_ordem():
    gabaritos = {136: "A", 137: "B"}
    itens = [
        item(136, "A", prova="1"), item(137, "B", prova="1"),                      # regular, mesma ordem
        item(136, "B", prova="2"), item(137, "A", prova="2"),                      # outra ordem
        item(136, "A", prova="3", cor="LARANJA"), item(137, "B", prova="3", cor="LARANJA"),  # adaptado
    ]
    resultado = extrair.itens_por_posicao(itens, gabaritos)
    assert [i["CO_PROVA"] for i in resultado[136]] == ["1"]


def test_itens_por_posicao_ignora_questao_anulada_ao_comparar_gabaritos():
    gabaritos = {136: "Anulado", 137: "B"}
    itens = [item(136, "X", anulado="1"), item(137, "B")]
    assert len(extrair.itens_por_posicao(itens, gabaritos)[136]) == 1


def test_dados_oficiais_de_item_normal():
    oficial = extrair.dados_oficiais([item(140, "E", habilidade="16", parametro_b="2.1")])
    assert oficial["gabarito"] == "E"
    assert oficial["habilidade"] == 16
    assert oficial["dificuldade_tri"] == 2.1
    assert oficial["anulada"] is False
    assert oficial["conflito_entre_cadernos"] is False


def test_dados_oficiais_de_item_anulado_nao_tem_gabarito():
    oficial = extrair.dados_oficiais([item(157, "X", anulado="1", motivo="anulado pedagogicamente")])
    assert oficial["gabarito"] is None
    assert oficial["anulada"] is True
    assert oficial["motivo_abandono"] == "anulado pedagogicamente"
    assert oficial["fora_da_tri"] is False


def test_item_fora_da_tri_por_motivo_estatistico_continua_com_gabarito():
    oficial = extrair.dados_oficiais([item(177, "E", anulado="1", motivo="Convergência", parametro_b="")])
    assert oficial["gabarito"] == "E"
    assert oficial["anulada"] is False
    assert oficial["fora_da_tri"] is True


def test_dados_oficiais_detecta_conflito_entre_cadernos():
    oficial = extrair.dados_oficiais([item(150, "A", codigo="1"), item(150, "A", codigo="2", prova="2")])
    assert oficial["conflito_entre_cadernos"] is True


def test_dados_oficiais_sem_parametro_tri():
    assert extrair.dados_oficiais([item(150, "A", parametro_b="")])["dificuldade_tri"] is None


# ---------------------------------------------------------------- matriz

MATRIZ = """
MATEMÁTICA E SUAS
Competência de área 1
Construir significados para os números naturais, inteiros,
racionais e reais.
H1 –\tReconhecer, no contexto social, diferentes significados.
H2 –\tIdentificar padrões numéricos
ou princípios de contagem.
MATRIZES DE REFERÊNCIA
14
Competência de área 2
Utilizar o conhecimento geométrico.
H6 –\tInterpretar a localização.
Competência de área 1
Compreender as ciências naturais.
H1 –\tReconhecer características de fenômenos ondulatórios.
"""


def test_extrair_matriz_pega_so_matematica_e_junta_linhas_quebradas():
    matriz = extrair.extrair_matriz(MATRIZ)
    assert [c["codigo"] for c in matriz["competencias"]] == ["C1", "C2"]
    assert matriz["competencias"][0]["descricao"] == "Construir significados para os números naturais, inteiros, racionais e reais."
    assert [h["codigo"] for h in matriz["habilidades"]] == ["H1", "H2", "H6"]
    assert matriz["habilidades"][1]["descricao"] == "Identificar padrões numéricos ou princípios de contagem."
    assert matriz["habilidades"][2]["competencia"] == "C2"


def test_blocos_reconhecem_o_formato_de_2025():
    blocos = extrair.blocos_por_questao("Questão 141\nprimeira\nQuestão 142\nsegunda\n")
    assert blocos[141].strip() == "primeira"
    assert blocos[142].strip() == "segunda"


def test_cabecalho_de_2025_e_removido():
    pagina = "MATEMÁTICA E SUAS TECNOLOGIAS | 2º DIA | CADERNO 7 | AZUL\nTexto da questão"
    assert extrair.limpar_pagina(pagina) == "Texto da questão"


def test_aceita_ate_tres_posicoes_com_questao_substituta():
    gabaritos = {136: "A", 137: "B", 138: "C", 139: "D"}
    itens = [item(136, "A"), item(137, "B"), item(138, "E"), item(139, "D")]  # 138: substituta no conjunto
    assert len(extrair.itens_por_posicao(itens, gabaritos)[138]) == 1
