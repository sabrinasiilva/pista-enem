"""Ambiente das migrações do Alembic. Uso (dentro de api/): alembic upgrade head"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.banco import Base
from app.config import Configuracoes

config = context.config
if config.config_file_name is not None and config.attributes.get("configurar_logs", True):
    fileConfig(config.config_file_name)

if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", Configuracoes().database_url.replace("%", "%%"))

target_metadata = Base.metadata


def rodar_offline() -> None:
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def rodar_online() -> None:
    motor = engine_from_config(
        config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with motor.connect() as conexao:
        # render_as_batch: o SQLite só altera tabelas recriando-as
        context.configure(connection=conexao, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    rodar_offline()
else:
    rodar_online()
