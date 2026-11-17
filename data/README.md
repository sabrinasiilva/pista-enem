# data/

Scripts e arquivos das questões do Pista. A explicação completa (fontes, licenças e problemas encontrados) está em [docs/DADOS.md](../docs/DADOS.md).

## Arquivos

| Arquivo | O que é |
|---|---|
| `questoes-mvp.json` | **As 60 questões usadas pelo tutor**, revisadas e anotadas |
| `questoes.json` | As 135 questões de Matemática de 2022 a 2024, com a conferência automática de cada uma |
| `matriz_matematica.json` | Competências e habilidades de Matemática da matriz de referência |
| `RELATORIO.md` | Questões escolhidas, cobertura da matriz e motivo de cada exclusão (gerado) |
| `anotacoes/revisao/` | Transcrição revisada, resolução e enganos de cada questão candidata |
| `brutos/` | PDFs, microdados e imagens baixados (não versionado) |

## Como rodar

Requer Python 3.12 ou mais novo.

```bash
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r data/requirements.txt

python data/baixar.py       # baixa as fontes para data/brutos/ (~40 MB)
python data/extrair.py      # gera questoes.json e matriz_matematica.json
python data/renderizar.py   # imagens das páginas oficiais, para revisar
python data/selecionar.py   # gera questoes-mvp.json e RELATORIO.md

python -m pytest data/tests
```

## Revisar uma questão

1. Abra a imagem da página indicada em `data/brutos/paginas/indice.json`.
2. Edite a questão no arquivo de `anotacoes/revisao/`.
3. Rode `python data/validar_revisao.py <arquivo>` e depois `python data/selecionar.py`.
