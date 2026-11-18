import pytest

from app.config import RAIZ_DO_REPOSITORIO
from app.tutor.estados import Estado
from app.tutor.prompts import PromptInvalido, Prompts
from app.tutor.questoes import QuestaoNaoEncontrada
from app.tutor.sessao import Sessao
from tests.auxiliares import questao_exemplo

# ---------------------------------------------------------------- banco de questões


def test_banco_carrega_pelo_menos_as_60_questoes_de_matematica(banco_real):
    assert len(banco_real.listar(area="matematica")) >= 60


def test_banco_filtra_por_ano_e_area(banco_real):
    de_2023 = banco_real.listar(ano=2023)
    assert de_2023 and all(q.ano == 2023 for q in de_2023)
    assert all(q.area == "natureza" for q in banco_real.listar(area="natureza"))


def test_banco_obter_questao_inexistente(banco_real):
    with pytest.raises(QuestaoNaoEncontrada):
        banco_real.obter("1999-999")


def test_toda_questao_tem_engano_nas_alternativas_erradas(banco_real):
    for questao in banco_real.listar():
        for alternativa in questao.alternativas:
            assert (alternativa.engano_provavel is None) == (alternativa.letra == questao.gabarito)


# ---------------------------------------------------------------- prompts


def test_prompt_tem_todas_as_secoes(prompts):
    assert prompts.versao == "tutor_v1"


def test_prompt_inexistente():
    with pytest.raises(PromptInvalido):
        Prompts.carregar(RAIZ_DO_REPOSITORIO / "prompts", "tutor_v999")


def test_prompt_sem_secao_obrigatoria(tmp_path):
    (tmp_path / "quebrado.md").write_text("# quebrado\n\n## sistema\n\nOi\n", encoding="utf-8")
    with pytest.raises(PromptInvalido):
        Prompts.carregar(tmp_path, "quebrado")


def test_sistema_protegido_inclui_regra_e_enganos_das_tentativas(prompts):
    questao = questao_exemplo()
    sessao = Sessao(questao.id, "tutor_v1", estado=Estado.PISTA_1, tentativas=["B"])
    texto = prompts.sistema(questao, sessao, "pista_1")
    assert "REGRA MAIS IMPORTANTE" in texto
    assert "Somou em vez de multiplicar" in texto
    for campo in ("{regra_da_resposta}", "{enunciado}", "{tentativas}", "{nivel_de_ajuda}"):
        assert campo not in texto
    assert "UMA pergunta" in texto


def test_sistema_livre_depois_de_revelar(prompts):
    questao = questao_exemplo()
    sessao = Sessao(questao.id, "tutor_v1", estado=Estado.EXPLICACAO, tentativas=["B", "D", "A"])
    texto = prompts.sistema(questao, sessao, "conversa")
    assert "REGRA MAIS IMPORTANTE" not in texto
    assert "já conhece a resposta" in texto


def test_sistema_com_reforco(prompts):
    questao = questao_exemplo()
    sessao = Sessao(questao.id, "tutor_v1", estado=Estado.PISTA_1, tentativas=["B"])
    assert "ATENÇÃO" in prompts.sistema(questao, sessao, "pista_1", reforco=True)


def test_momento_desconhecido(prompts):
    questao = questao_exemplo()
    with pytest.raises(ValueError):
        prompts.sistema(questao, Sessao(questao.id, "tutor_v1"), "inventado")


@pytest.mark.parametrize("estado", list(Estado))
def test_prompt_monta_para_todas_as_questoes_reais_e_estados(banco_real, prompts, estado):
    for questao in banco_real.listar():
        errada = next(a.letra for a in questao.alternativas if a.letra != questao.gabarito)
        sessao = Sessao(questao.id, "tutor_v1", estado=estado, tentativas=[errada])
        assert questao.enunciado in prompts.sistema(questao, sessao, "conversa")


@pytest.mark.parametrize("versao", sorted(p.stem for p in (RAIZ_DO_REPOSITORIO / "prompts").glob("tutor_v*.md")))
@pytest.mark.parametrize("area", ["matematica", "natureza"])
def test_toda_versao_do_prompt_monta_todos_os_momentos(versao, area):
    prompts = Prompts.carregar(RAIZ_DO_REPOSITORIO / "prompts", versao)
    questao = questao_exemplo(area=area)
    for estado in (Estado.RESPONDENDO, Estado.PISTA_1, Estado.EXPLICACAO):
        sessao = Sessao(questao.id, versao, estado=estado, tentativas=["B"] if estado != Estado.RESPONDENDO else [])
        for momento in ("pista_1", "pista_2", "explicacao", "acerto", "conversa"):
            assert questao.enunciado in prompts.sistema(questao, sessao, momento)


def test_tutor_v2_diz_a_area_da_questao():
    prompts = Prompts.carregar(RAIZ_DO_REPOSITORIO / "prompts", "tutor_v2")
    questao = questao_exemplo(area="natureza")
    sistema = prompts.sistema(questao, Sessao(questao.id, "tutor_v2"), "conversa")
    assert "tutor de Ciências da Natureza" in sistema
    assert "último passo" in sistema


def test_chave_de_habilidade_inclui_a_area():
    from app.tutor.questoes import chave_de_habilidade

    assert questao_exemplo().habilidade_chave == "MT-H3"
    assert questao_exemplo(area="natureza").habilidade_chave == "CN-H3"
    assert chave_de_habilidade("H16") == "MT-H16"
    assert chave_de_habilidade("CN-H30") == "CN-H30"
    with pytest.raises(ValueError):
        chave_de_habilidade("CN-H31")
