from app.tutor.busca import BuscaDeQuestoes, habilidades_provaveis, palavras
from app.tutor.questoes import BancoDeQuestoes
from tests.auxiliares import questao_exemplo


def test_palavras_tira_acentos_latex_e_palavras_vazias():
    assert palavras(r"A proporção $\frac{1}{2}$ é para o cálculo") == ["proporc", "calculo"]


def banco():
    return BancoDeQuestoes(
        [
            questao_exemplo(
                id="2099-136", enunciado="Uma piscina tem volume de água em litros.", conceitos=("volume",)
            ),
            questao_exemplo(
                id="2099-137",
                enunciado="O volume de água da caixa, em litros, é",
                conceitos=("volume",),
                habilidade="H14",
            ),
            questao_exemplo(id="2099-138", enunciado="A média das notas dos alunos foi", conceitos=("média",)),
            questao_exemplo(id="2099-91", area="natureza", enunciado="O volume de água evaporada em litros"),
        ]
    )


def test_parecida_e_a_de_mesmo_assunto_e_mesma_area():
    dados = banco()
    busca = BuscaDeQuestoes(dados)
    parecidas = busca.parecidas(dados.obter("2099-136"), quantidade=2)
    assert [q.id for q in parecidas] == ["2099-137", "2099-138"]
    assert busca.parecidas(dados.obter("2099-136"), quantidade=5, excluir=["2099-137"])[0].id == "2099-138"


def test_habilidades_provaveis_usa_a_descricao_e_os_votos():
    matriz = {"H1": "Calcular volumes de sólidos", "H2": "Interpretar gráficos de barras"}
    assert habilidades_provaveis("volume do cubo e volumes", matriz, quantidade=1) == ["H1"]
    assert habilidades_provaveis("volume", matriz, vizinhas=[(5.0, "H2")], quantidade=1) == ["H2"]
