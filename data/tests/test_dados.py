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


def test_questoes_extraidas_tem_45_por_area_e_ano(todas):
    grupos = [("matematica", ano) for ano in (2022, 2023, 2024, 2025)] + [("natureza", ano) for ano in (2022, 2023, 2024)]
    for area, ano in grupos:
        assert sum(1 for q in todas.values() if q["area"] == area and q["ano"] == ano) == 45, (area, ano)


def test_gabarito_do_conjunto_confere_com_microdados(todas):
    """Só diverge onde o conjunto aberto traz a questão substituta do caderno adaptado (no máximo 3 por prova)."""
    divergentes = [q for q in todas.values() if not q["conferencia"]["gabarito_confere_com_microdados"]]
    assert len(divergentes) <= 3
    assert all(q["conferencia"]["pendencias"] for q in divergentes)


def test_matrizes_das_duas_areas():
    for area, competencias in (("matematica", 7), ("natureza", 8)):
        matriz = carregar(f"matriz_{area}.json")
        assert len(matriz["competencias"]) == competencias, area
        assert [h["codigo"] for h in matriz["habilidades"]] == [f"H{i}" for i in range(1, 31)], area
        assert all(h["competencia"] for h in matriz["habilidades"]), area


def test_banco_tem_pelo_menos_60_questoes_por_area_sem_repetir(mvp):
    ids = [q["id"] for q in mvp]
    assert len(ids) == len(set(ids))
    for area in ("matematica", "natureza"):
        assert sum(q["area"] == area for q in mvp) >= 60, area


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


def test_mvp_habilidade_e_competencia_da_matriz_da_area(mvp, todas):
    matrizes = {area: {h["codigo"]: h for h in carregar(f"matriz_{area}.json")["habilidades"]}
                for area in ("matematica", "natureza")}
    for questao in mvp:
        codigo = questao["habilidade"]["codigo"]
        assert codigo == todas[questao["id"]]["habilidade"], questao["id"]
        assert questao["area"] == todas[questao["id"]]["area"], questao["id"]
        assert questao["habilidade"]["descricao"] == matrizes[questao["area"]][codigo]["descricao"], questao["id"]
        assert questao["competencia"]["codigo"] == matrizes[questao["area"]][codigo]["competencia"], questao["id"]


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
