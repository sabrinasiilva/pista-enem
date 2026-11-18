"""Fontes dos dados e onde cada uma é salva.

Tudo o que é baixado vai para data/brutos/, que não é versionado.
"""

from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent
PASTA_BRUTOS = PASTA_DADOS / "brutos"

ANOS = (2022, 2023, 2024)

# Conjunto de dados da Maritaca AI (licença Apache-2.0), fixado numa revisão
# para que a extração seja reproduzível.
MARITACA_REVISAO = "b2a7257356b0f56b740d57f23f8a575542ff6c0c"
MARITACA_URL = "https://huggingface.co/datasets/maritaca-ai/enem/resolve/{revisao}/{ano}.jsonl"

# Microdados do Enem (Inep). Só a tabela de itens é extraída de dentro do zip.
MICRODADOS_URL = "https://download.inep.gov.br/microdados/microdados_enem_{ano}.zip"

# Caderno de questões do 2º dia que corresponde à ordem das questões no
# conjunto da Maritaca. Descoberto comparando gabaritos e textos.
CADERNOS = {
    2022: {"codigo": 6, "cor": "CINZA"},
    2023: {"codigo": 8, "cor": "ROSA"},
    2024: {"codigo": 8, "cor": "VERDE"},
}
PROVA_URL = "https://download.inep.gov.br/enem/provas_e_gabaritos/{ano}_PV_impresso_D2_CD{codigo}.pdf"

MATRIZ_URL = "https://download.inep.gov.br/enem/outros_documentos/enem_matriz_de_referencia_v1.pdf"

PRIMEIRA_QUESTAO_MATEMATICA = 136
ULTIMA_QUESTAO_MATEMATICA = 180


def caminho_maritaca(ano: int) -> Path:
    return PASTA_BRUTOS / f"maritaca_{ano}.jsonl"


def caminho_itens(ano: int) -> Path:
    return PASTA_BRUTOS / f"itens_prova_{ano}.csv"


def caminho_prova(ano: int) -> Path:
    return PASTA_BRUTOS / f"prova_{ano}_d2_cd{CADERNOS[ano]['codigo']}.pdf"


def caminho_matriz() -> Path:
    return PASTA_BRUTOS / "matriz_referencia.pdf"


def url_prova(ano: int) -> str:
    return PROVA_URL.format(ano=ano, codigo=CADERNOS[ano]["codigo"])
