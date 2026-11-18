"""Confere os arquivos de dados versionados. Não precisa de rede nem dos arquivos brutos."""

import json
import re
from pathlib import Path

import pytest

PASTA = Path(__file__).resolve().parents[1]
LETRAS = list("ABCDE")


def carregar(nome):
    return json.loads((PASTA / nome).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def mvp():
    return carregar("questoes-mvp.json")


@pytest.fixture(scope="module")
def todas():
    return {q["id"]: q for q in carregar("questoes.json")}


@pytest.fixture(scope="module")
def matriz():
    return carregar("matriz_matematica.json")


def test_matriz_tem_7_competencias_e_30_habilidades(matriz):
    assert [c["codigo"] for c in matriz["competencias"]] == [f"C{i}" for i in range(1, 8)]
    assert [h["codigo"] for h in matriz["habilidades"]] == [f"H{i}" for i in range(1, 31)]
    assert all(h["descricao"] for h in matriz["habilidades"])


def test_questoes_extraidas_tem_45_por_ano(todas):
    for ano in (2022, 2023, 2024):
        assert sum(1 for q in todas.values() if q["ano"] == ano) == 45


def test_gabarito_do_conjunto_confere_com_microdados(todas):
    assert all(q["conferencia"]["gabarito_confere_com_microdados"] for q in todas.values())


def test_mvp_tem_60_questoes_unicas(mvp):
    ids = [q["id"] for q in mvp]
    assert len(ids) == 60
    assert len(set(ids)) == 60


def test_mvp_gabarito_igual_ao_oficial(mvp, todas):
    for questao in mvp:
        assert questao["gabarito"] in LETRAS
        assert questao["gabarito"] == todas[questao["id"]]["gabarito"], questao["id"]


def test_mvp_cinco_alternativas_com_engano_nas_erradas(mvp):
    for questao in mvp:
        assert [a["letra"] for a in questao["alternativas"]] == LETRAS, questao["id"]
        for alternativa in questao["alternativas"]:
            assert alternativa["texto"].strip(), questao["id"]
            if alternativa["letra"] == questao["gabarito"]:
                assert alternativa["engano_provavel"] is None, questao["id"]
            else:
                assert alternativa["engano_provavel"].strip(), questao["id"]


def test_mvp_sem_imagem_e_sem_anuladas(mvp, todas):
    for questao in mvp:
        assert not todas[questao["id"]]["tem_imagem"]
        assert not todas[questao["id"]]["anulada"]


def test_mvp_habilidade_e_competencia_da_matriz(mvp, matriz, todas):
    habilidades = {h["codigo"]: h for h in matriz["habilidades"]}
    for questao in mvp:
        codigo = questao["habilidade"]["codigo"]
        assert codigo == todas[questao["id"]]["habilidade"], questao["id"]
        assert questao["competencia"]["codigo"] == habilidades[codigo]["competencia"]


def test_mvp_fonte_registrada(mvp):
    for questao in mvp:
        fonte = questao["fonte"]
        assert fonte["orgao"] == "Inep"
        assert fonte["url"].startswith("https://download.inep.gov.br/")
        assert fonte["item_inep"]
        assert f"questão {questao['numero']}" in fonte["prova"]


def test_mvp_textos_sem_caracteres_de_controle_e_formulas_fechadas(mvp):
    controle = re.compile(r"[\x00-\x09\x0b-\x1f]")
    for questao in mvp:
        textos = [questao["enunciado"], questao["resolucao"]]
        textos += [a["texto"] for a in questao["alternativas"]]
        textos += [a["engano_provavel"] for a in questao["alternativas"] if a["engano_provavel"]]
        for texto in textos:
            assert not controle.search(texto), questao["id"]
            assert len(re.findall(r"(?<!\\)\$", texto)) % 2 == 0, questao["id"]
            assert not re.search(r"(?<!\$)R\$\s*\d", texto), f"{questao['id']}: use R\\$"


def test_mvp_sem_resquicio_da_versao_para_leitor_de_tela(mvp):
    """O texto do conjunto original escrevia fórmulas por extenso; o MVP não pode ter isso."""
    padroes = re.compile(r"fração, numerador|abre parêntese|fecha parêntese|índice \d", re.I)
    for questao in mvp:
        textos = [questao["enunciado"]] + [a["texto"] for a in questao["alternativas"]]
        assert not any(padroes.search(t) for t in textos), questao["id"]
