"""Guardrails de entrada (o que o aluno manda) e de saída (o que a IA responde).

Entrada: limita o tamanho e reconhece tentativas de manipulação do prompt e pedidos
diretos da resposta, que são respondidos com mensagens fixas, sem chamar a IA.

Saída: antes da explicação, detecta se a resposta da IA revela a alternativa correta,
pela letra ("alternativa C", "(C)") ou pelo conteúdo (o valor ou o texto da alternativa).
A detecção é conservadora: na dúvida, bloqueia e o motor pede outra resposta.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from .questoes import Questao

LIMITE_DE_CARACTERES = 1000
TAMANHO_MINIMO_DO_TEXTO = 3  # alternativas mais curtas ("I.", "6") só são checadas como número

MotivoDeBloqueio = Literal["vazia", "longa", "manipulacao"]


# ---------------------------------------------------------------- normalização


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento e sem LaTeX, com números agrupados e pontuação virando espaço.

    "R\\$ 1 350 000,00" -> "r 1350000,00"; "$\\frac{35}{64}$" -> "35 64".
    """
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    texto = re.sub(r"\\[a-z]+", " ", texto)  # comandos LaTeX: \frac, \times, \cdot...
    texto = texto.replace(" ", " ").replace(" ", " ")
    # separador de milhar: "1 350 000" e "1.350.000" viram "1350000"
    texto = re.sub(r"(?<=\d)[ .](?=\d{3}(?!\d))", "", texto)
    texto = re.sub(r"(?<=\d),(?=\d)", "#", texto)  # protege a vírgula decimal
    texto = re.sub(r"[^a-z0-9#]+", " ", texto)
    return " ".join(texto.replace("#", ",").split())


def contem(texto_normalizado: str, trecho_normalizado: str) -> bool:
    return f" {trecho_normalizado} " in f" {texto_normalizado} "


# ---------------------------------------------------------------- entrada

PADROES_DE_MANIPULACAO = [
    r"\bignor[aeo]\w* (as |todas as |suas |essas |tuas )?(instruc|regra|orientac|diretriz)",
    r"\besquec[ae]\w* (as |todas as |suas |essas )?(instruc|regra|orientac)",
    r"\bdesconsider[ae]\w* (as |todas as |suas )?(instruc|regra)",
    r"\bignore (all |the |your |previous )*(instructions|rules)",
    r"\bvoce (agora )?(e|eh|sera) (um|uma|o|a) (outro|outra|nova|novo|assistente|ia|modelo)",
    r"\b(a partir de agora|agora) voce (e|eh|vai ser)\b",
    r"\bfinja (que|ser)\b",
    r"\b(modo|mode) (desenvolvedor|developer|dan|jailbreak|deus|admin)",
    r"\bjailbreak\b",
    r"\b(prompt|instrucoes) (do |de )?sistema\b",
    r"\bsystem prompt\b",
    r"\b(mostre|revele|repita|imprima|escreva|diga) (as |suas |tuas )?(instrucoes|regras)\b",
    r"\bsou (o |a |seu |sua )?(professor|professora|desenvolvedor|desenvolvedora|criador|criadora|administrador)\b",
]

PADROES_DE_PEDIDO_DA_RESPOSTA = [
    r"\bqual (e |eh |seria )?a (resposta|alternativa|letra|opcao) (certa|correta)",
    r"\b(qual|que) (e |eh )?a (resposta|letra|alternativa)\b",
    r"\b(me |nos )?(da|de|diz|diga|fala|fale|passa|passe|manda|mande|conta|conte) "
    r"(logo |so |apenas )?a (resposta|letra|alternativa)",
    r"\b(so|apenas) (quero|preciso) (d)?a (resposta|letra|alternativa)",
    r"\b(gabarito|resposta certa|resposta correta)\b",
]

_MANIPULACAO = [re.compile(p) for p in PADROES_DE_MANIPULACAO]
_PEDIDO = [re.compile(p) for p in PADROES_DE_PEDIDO_DA_RESPOSTA]


@dataclass(frozen=True)
class VerificacaoDeEntrada:
    permitida: bool
    motivo: MotivoDeBloqueio | None = None


def verificar_entrada(texto: str) -> VerificacaoDeEntrada:
    if not texto.strip():
        return VerificacaoDeEntrada(False, "vazia")
    if len(texto) > LIMITE_DE_CARACTERES:
        return VerificacaoDeEntrada(False, "longa")
    normalizado = normalizar(texto)
    if any(p.search(normalizado) for p in _MANIPULACAO):
        return VerificacaoDeEntrada(False, "manipulacao")
    return VerificacaoDeEntrada(True)


def pede_a_resposta(texto: str) -> bool:
    normalizado = normalizar(texto)
    return any(p.search(normalizado) for p in _PEDIDO)


# ---------------------------------------------------------------- saída

# A letra é procurada no texto original (com acentos e maiúsculas): sem acento, "é" vira "e"
# e se confunde com a alternativa E; e o artigo "a" se confunde com a alternativa A.
_CHAVE = r"(?i:alternativas?|letra|op[çc][ãa]o|item|resposta|gabarito|marque|marcar|escolha|escolher|assinale)"
_MEIO = r"(?:\s+(?i:correta|certa|final))?(?:\s*(?i:é|e|eh|seria|será|sera|:))?(?:\s+(?i:a|o))?"


def _revela_a_letra(texto: str, letra: str) -> bool:
    maiuscula = re.compile(rf"\b{_CHAVE}{_MEIO}\s*\(?{letra}\)?(?!\w)")
    # letra minúscula só conta quando fecha a frase: "a resposta é a c."
    minuscula = re.compile(rf"\b{_CHAVE}{_MEIO}\s+\(?{letra.lower()}\)?(?=\s*[.,;!?]|\s*$)")
    if maiuscula.search(texto) or minuscula.search(texto):
        return True
    # "(C)" e "C)" no começo da linha são formas de citar alternativa
    if re.search(rf"(^|\s)\(\s*{letra}\s*\)", texto):
        return True
    return bool(re.search(rf"(?m)^\s*\**{letra}\s*[\).:]\s", texto))


def _trechos_da_alternativa(questao: Questao) -> list[str]:
    """Partes da alternativa correta que, se aparecerem na resposta, revelam o gabarito."""
    alternativa = normalizar(questao.correta.texto)
    trechos = []
    if len(alternativa.replace(" ", "")) >= TAMANHO_MINIMO_DO_TEXTO:
        trechos.append(alternativa)
    # números da alternativa que só existem nela (e não no enunciado nem nas outras)
    outras = " ".join(normalizar(a.texto) for a in questao.alternativas if a.letra != questao.gabarito)
    enunciado = normalizar(questao.enunciado)
    for numero in re.findall(r"\d+(?:,\d+)?", alternativa):
        formas = [numero]
        sem_centavos = re.fullmatch(r"(\d+),0+", numero)
        if sem_centavos:  # "960,00" também aparece como "960"
            formas.append(sem_centavos.group(1))
        trechos += [f for f in formas if not contem(enunciado, f) and not contem(outras, f)]
    return trechos


def revela_a_resposta(texto: str, questao: Questao) -> bool:
    """True se o texto entrega a alternativa correta, pela letra ou pelo conteúdo."""
    if _revela_a_letra(texto, questao.gabarito):
        return True
    normalizado = normalizar(texto)
    enunciado = normalizar(questao.enunciado)
    for trecho in _trechos_da_alternativa(questao):
        # se o trecho já está no enunciado, citá-lo não entrega nada
        if contem(normalizado, trecho) and not contem(enunciado, trecho):
            return True
    return False
