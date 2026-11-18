"""Banco de dados: contas, acessos e resultados das questões.

Localmente usa SQLite (api/pista.db). Na Fase 5, o mesmo código roda no PostgreSQL do Neon,
trocando só a variável DATABASE_URL. As tabelas são criadas pelas migrações do Alembic.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Engine, ForeignKey, Integer, String, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .tutor.sessao import agora


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    """Conta sem dados pessoais: só um apelido escolhido pelo aluno."""

    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    apelido: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(200))
    codigo_recuperacao_hash: Mapped[str] = mapped_column(String(200))
    meta_semanal: Mapped[int] = mapped_column(Integer, default=10)
    habilidades_foco: Mapped[list[str]] = mapped_column(JSON, default=list)
    tema: Mapped[str] = mapped_column(String(10), default="sistema")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class Acesso(Base):
    """Token de acesso. Só o hash fica no banco, então um vazamento do banco não dá acesso às contas."""

    __tablename__ = "acessos"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    usuario_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Resultado(Base):
    """Como terminou uma questão resolvida por um aluno com conta."""

    __tablename__ = "resultados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    questao_id: Mapped[str] = mapped_column(String(20), index=True)
    habilidade: Mapped[str] = mapped_column(String(5))
    acertou: Mapped[bool] = mapped_column(Boolean)
    acertou_de_primeira: Mapped[bool] = mapped_column(Boolean)
    tentativas: Mapped[int] = mapped_column(Integer)
    pediu_explicacao: Mapped[bool] = mapped_column(Boolean)
    concluido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, index=True)


def criar_motor(url: str) -> Engine:
    if url.startswith("sqlite"):
        motor = create_engine(url, connect_args={"check_same_thread": False})

        @event.listens_for(motor, "connect")
        def _ativar_chaves_estrangeiras(conexao, _):
            cursor = conexao.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return motor
    return create_engine(url, pool_pre_ping=True)


def fabrica_de_sessoes(motor: Engine) -> sessionmaker[Session]:
    return sessionmaker(motor, expire_on_commit=False)


def abrir(fabrica: sessionmaker[Session]) -> Iterator[Session]:
    with fabrica() as sessao:
        yield sessao
