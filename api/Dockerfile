# Imagem da API do Pista. Construa a partir da raiz do repositório:
#   docker build -f api/Dockerfile -t pista-api .
#   docker run --rm -p 8000:8000 --env-file api/.env pista-api
#
# Roda como usuário sem privilégios (uid 1000, o mesmo que o Hugging Face Spaces usa).
# A porta vem da variável PORT (8000 por padrão; o Hugging Face Spaces usa 7860).
# As migrações do banco rodam ao iniciar. Sem DATABASE_URL própria, usa SQLite na pasta do
# usuário, que some quando o container é recriado; o banco de verdade é o PostgreSQL da Fase 5.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000 \
    ARQUIVO_QUESTOES=/app/data/questoes-mvp.json \
    PASTA_PROMPTS=/app/prompts \
    DATABASE_URL=sqlite:////home/pista/pista.db

WORKDIR /app

RUN useradd --create-home --uid 1000 pista

COPY api/requirements.txt .
RUN pip install -r requirements.txt

COPY api/app ./app
COPY api/alembic.ini ./alembic.ini
COPY api/migrations ./migrations
COPY prompts ./prompts
COPY data/questoes-mvp.json ./data/questoes-mvp.json

USER pista
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health', timeout=4)"

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers"]
