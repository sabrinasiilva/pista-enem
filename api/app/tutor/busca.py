"""Busca por texto (TF-IDF): questões parecidas e habilidades prováveis de uma questão.

Com algumas centenas de questões e 60 habilidades, tudo cabe na memória e é calculado na
inicialização. Por isso não há pgvector nem embeddings (a decisão está em docs/ARQUITETURA.md).
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence

from .questoes import BancoDeQuestoes, Questao

# palavras sem acento, porque o texto é normalizado antes
PALAVRAS_VAZIAS = frozenset(
    """
    ate apos com como contra das dos ela elas ele eles entre essa esse esta estao este isso mais mas menos
    nas nos num numa para pela pelas pelo pelos por qual quais quando que sao seja sem ser seu seus sua suas
    sobre tem tambem uma umas uns foi ter tinha muito cada outro outra outros outras mesmo mesma
    alternativa questao valor figura texto apresenta apresentado acordo caso forma
    """.split()  # noqa: SIM905 - lista longa, mais legível como texto
)
TAMANHO_DO_RADICAL = 7  # "proporcional", "proporcionalidade" e "proporcao" viram quase o mesmo radical


def palavras(texto: str) -> list[str]:
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\\[a-z]+", " ", texto)  # comandos LaTeX
    return [p[:TAMANHO_DO_RADICAL] for p in re.findall(r"[a-z]{3,}", texto) if p not in PALAVRAS_VAZIAS]


Vetor = dict[str, float]


def _normalizar(vetor: Vetor) -> Vetor:
    norma = math.sqrt(sum(v * v for v in vetor.values()))
    return {k: v / norma for k, v in vetor.items()} if norma else {}


def cosseno(a: Vetor, b: Vetor) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(peso * b.get(termo, 0.0) for termo, peso in a.items())


class IndiceTfIdf:
    def __init__(self, documentos: Sequence[str]):
        contagens = [Counter(palavras(d)) for d in documentos]
        frequencia = Counter(termo for c in contagens for termo in c)
        total = len(documentos)
        self.idf = {termo: math.log((1 + total) / (1 + n)) + 1 for termo, n in frequencia.items()}
        self.vetores = [self._pesar(c) for c in contagens]

    def _pesar(self, contagem: Counter) -> Vetor:
        return _normalizar({t: (1 + math.log(n)) * self.idf[t] for t, n in contagem.items() if t in self.idf})

    def vetor(self, texto: str) -> Vetor:
        return self._pesar(Counter(palavras(texto)))


def texto_da_questao(questao: Questao) -> str:
    alternativas = " ".join(a.texto for a in questao.alternativas)
    conceitos = " ".join(questao.conceitos)
    # os conceitos resumem o assunto: contam mais que o enunciado, que tem muito contexto
    return f"{questao.enunciado} {alternativas} {conceitos} {conceitos} {conceitos}"


class BuscaDeQuestoes:
    """Questões parecidas: mesma área, texto e conceitos próximos, com bônus para a mesma habilidade."""

    BONUS_MESMA_HABILIDADE = 0.25

    def __init__(self, banco: BancoDeQuestoes):
        self._questoes = sorted(banco.listar(), key=lambda q: q.id)
        indice = IndiceTfIdf([texto_da_questao(q) for q in self._questoes])
        self._vetores = dict(zip((q.id for q in self._questoes), indice.vetores, strict=True))

    def parecidas(self, questao: Questao, quantidade: int = 3, excluir: Iterable[str] = ()) -> list[Questao]:
        fora = {questao.id, *excluir}
        vetor = self._vetores[questao.id]
        pontuadas = [
            (
                cosseno(vetor, self._vetores[outra.id])
                + self.BONUS_MESMA_HABILIDADE * (outra.habilidade_chave == questao.habilidade_chave),
                outra.id,
                outra,
            )
            for outra in self._questoes
            if outra.area == questao.area and outra.id not in fora
        ]
        pontuadas.sort(key=lambda t: (-t[0], t[1]))
        return [q for _, _, q in pontuadas[:quantidade]]


def habilidades_provaveis(
    texto: str,
    matriz: dict[str, str],
    vizinhas: Sequence[tuple[float, str]] = (),
    quantidade: int = 5,
) -> list[str]:
    """Ordena as habilidades da matriz para um texto de questão.

    Junta dois sinais:
    - semelhança do texto com a descrição de cada habilidade (`matriz`: código -> descrição);
    - votos das questões vizinhas já classificadas (`vizinhas`: (semelhança, código)).
    """
    codigos = sorted(matriz)
    indice = IndiceTfIdf([matriz[c] for c in codigos] + [texto])
    consulta = indice.vetores[-1]
    pontos: dict[str, float] = defaultdict(float)
    for codigo, vetor in zip(codigos, indice.vetores, strict=False):
        pontos[codigo] += cosseno(consulta, vetor)
    for semelhanca, codigo in vizinhas:
        pontos[codigo] += semelhanca
    return sorted(codigos, key=lambda c: (-pontos[c], c))[:quantidade]
