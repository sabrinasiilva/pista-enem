"""Regras das contas: cadastro, login, recuperação, troca de senha e exclusão."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from . import seguranca
from .banco import Acesso, Resultado, Usuario
from .tutor.sessao import agora

VALIDADE_DO_ACESSO = timedelta(days=30)
APELIDO = re.compile(r"^[a-z0-9_.]{3,20}$")


class ErroDeConta(Exception):
    def __init__(self, status: int, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.status = status
        self.codigo = codigo
        self.mensagem = mensagem


def validar_apelido(apelido: str) -> str:
    apelido = apelido.strip().lower()
    if not APELIDO.fullmatch(apelido):
        raise ErroDeConta(
            422,
            "apelido_invalido",
            "Use de 3 a 20 caracteres: letras sem acento, números, ponto ou sublinhado.",
        )
    return apelido


SENHAS_COMUNS = frozenset(
    {
        "12345678",
        "123456789",
        "1234567890",
        "87654321",
        "11111111",
        "00000000",
        "12341234",
        "password",
        "password1",
        "senha123",
        "senha1234",
        "senhasenha",
        "qwerty123",
        "qwertyuiop",
        "abcdefgh",
        "abc12345",
        "abcd1234",
        "iloveyou",
        "brasil123",
        "enem2025",
        "enem2026",
    }
)


def validar_senha(senha: str, apelido: str) -> None:
    if len(senha) < 8:
        raise ErroDeConta(422, "senha_fraca", "A senha precisa ter pelo menos 8 caracteres.")
    if len(senha) > 128:
        raise ErroDeConta(422, "senha_longa", "A senha pode ter no máximo 128 caracteres.")
    if senha.lower() in SENHAS_COMUNS or apelido in senha.lower() or len(set(senha)) <= 2:
        raise ErroDeConta(422, "senha_fraca", "Essa senha é fácil de adivinhar. Escolha outra.")


@dataclass(frozen=True)
class Entrada:
    usuario: Usuario
    token: str
    codigo_de_recuperacao: str | None = None


def _novo_acesso(banco: Session, usuario: Usuario) -> str:
    token = seguranca.gerar_token()
    banco.add(
        Acesso(token_hash=seguranca.hash_do_token(token), usuario_id=usuario.id, expira_em=agora() + VALIDADE_DO_ACESSO)
    )
    return token


def criar_conta(
    banco: Session, apelido: str, senha: str, meta_semanal: int = 10, habilidades_foco: list[str] | None = None
) -> Entrada:
    apelido = validar_apelido(apelido)
    validar_senha(senha, apelido)
    if banco.scalar(select(Usuario).where(Usuario.apelido == apelido)):
        raise ErroDeConta(409, "apelido_em_uso", "Esse apelido já está em uso. Escolha outro.")
    codigo = seguranca.gerar_codigo_de_recuperacao()
    usuario = Usuario(
        apelido=apelido,
        senha_hash=seguranca.gerar_hash(senha),
        codigo_recuperacao_hash=seguranca.gerar_hash(codigo),
        meta_semanal=meta_semanal,
        habilidades_foco=habilidades_foco or [],
    )
    banco.add(usuario)
    banco.flush()
    token = _novo_acesso(banco, usuario)
    banco.commit()
    return Entrada(usuario, token, codigo)


def entrar(banco: Session, apelido: str, senha: str) -> Entrada:
    usuario = banco.scalar(select(Usuario).where(Usuario.apelido == apelido.strip().lower()))
    guardado = usuario.senha_hash if usuario else seguranca.HASH_FICTICIO
    if not seguranca.conferir_hash(senha, guardado) or usuario is None:
        raise ErroDeConta(401, "credenciais_invalidas", "Apelido ou senha incorretos.")
    token = _novo_acesso(banco, usuario)
    banco.commit()
    return Entrada(usuario, token)


def recuperar(banco: Session, apelido: str, codigo: str, nova_senha: str) -> Entrada:
    """Troca a senha usando o código de recuperação. O código usado deixa de valer e um novo é gerado."""
    usuario = banco.scalar(select(Usuario).where(Usuario.apelido == apelido.strip().lower()))
    guardado = usuario.codigo_recuperacao_hash if usuario else seguranca.HASH_FICTICIO
    if not seguranca.conferir_hash(seguranca.normalizar_codigo(codigo), guardado) or usuario is None:
        raise ErroDeConta(401, "codigo_invalido", "Apelido ou código de recuperação incorretos.")
    validar_senha(nova_senha, usuario.apelido)
    novo_codigo = seguranca.gerar_codigo_de_recuperacao()
    usuario.senha_hash = seguranca.gerar_hash(nova_senha)
    usuario.codigo_recuperacao_hash = seguranca.gerar_hash(novo_codigo)
    banco.execute(delete(Acesso).where(Acesso.usuario_id == usuario.id))  # derruba os outros aparelhos
    token = _novo_acesso(banco, usuario)
    banco.commit()
    return Entrada(usuario, token, novo_codigo)


def usuario_do_token(banco: Session, token: str) -> Usuario | None:
    acesso = banco.get(Acesso, seguranca.hash_do_token(token))
    if acesso is None:
        return None
    expira = acesso.expira_em if acesso.expira_em.tzinfo else acesso.expira_em.replace(tzinfo=agora().tzinfo)
    if expira < agora():
        banco.delete(acesso)
        banco.commit()
        return None
    return banco.get(Usuario, acesso.usuario_id)


def limpar_acessos_vencidos(banco: Session) -> int:
    """Apaga os tokens que já venceram, para não guardar nada além do necessário."""
    apagados = banco.execute(delete(Acesso).where(Acesso.expira_em < agora())).rowcount
    banco.commit()
    return apagados or 0


def sair(banco: Session, token: str) -> None:
    banco.execute(delete(Acesso).where(Acesso.token_hash == seguranca.hash_do_token(token)))
    banco.commit()


def trocar_senha(banco: Session, usuario: Usuario, senha_atual: str, nova_senha: str, token_atual: str) -> None:
    if not seguranca.conferir_hash(senha_atual, usuario.senha_hash):
        raise ErroDeConta(401, "senha_incorreta", "A senha atual está incorreta.")
    validar_senha(nova_senha, usuario.apelido)
    usuario.senha_hash = seguranca.gerar_hash(nova_senha)
    # mantém só o acesso deste aparelho
    banco.execute(
        delete(Acesso).where(Acesso.usuario_id == usuario.id, Acesso.token_hash != seguranca.hash_do_token(token_atual))
    )
    banco.commit()


def apagar_conta(banco: Session, usuario: Usuario, senha: str) -> None:
    """Apaga a conta e todo o histórico (LGPD, direito à eliminação dos dados)."""
    if not seguranca.conferir_hash(senha, usuario.senha_hash):
        raise ErroDeConta(401, "senha_incorreta", "A senha está incorreta.")
    # apaga explicitamente, sem depender do ON DELETE CASCADE estar ativo no banco
    banco.execute(delete(Resultado).where(Resultado.usuario_id == usuario.id))
    banco.execute(delete(Acesso).where(Acesso.usuario_id == usuario.id))
    banco.delete(usuario)
    banco.commit()
