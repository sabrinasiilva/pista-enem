"""Acesso ao tutor e às sessões a partir das rotas."""

from __future__ import annotations

from fastapi import Request

from .sessoes import RepositorioDeSessoes
from .tutor.motor import Tutor


def tutor(request: Request) -> Tutor:
    return request.app.state.tutor


def sessoes(request: Request) -> RepositorioDeSessoes:
    return request.app.state.sessoes
