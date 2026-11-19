"""Motor do tutor: decide o que acontece a cada ação do aluno.

Regras centrais:
- quem decide se o aluno acertou é o código, comparando com o gabarito;
- enquanto a resposta está protegida, toda mensagem da IA passa pelo guardrail de saída;
  se vazar, a IA tenta de novo com um reforço; se vazar outra vez, vai uma pista escrita à mão;
- se a IA falhar (ou não houver chave configurada), o tutor usa o plano B.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from . import guardrails
from .busca import BuscaDeQuestoes
from .estados import ESTADOS_PROTEGIDOS, Estado, TransicaoInvalida, apos_pedido_de_explicacao, apos_resposta
from .ia import ClienteDeIA, ErroDaIA, Turno
from .prompts import Prompts
from .questoes import LETRAS, BancoDeQuestoes, Questao
from .sessao import Mensagem, Protecao, Sessao

logger = logging.getLogger(__name__)

TENTATIVAS_CONTRA_VAZAMENTO = 2
PALAVRAS_POR_TRECHO = 4

MENSAGEM_DE_MANIPULACAO = (
    "Aqui eu só posso ajudar com esta questão, e sem entregar a resposta antes da hora. "
    "Que tal me contar em que parte você travou?"
)
MENSAGEM_LONGA = (
    f"Sua mensagem passou do limite de {guardrails.LIMITE_DE_CARACTERES} caracteres. Pode resumir a sua dúvida?"
)
MENSAGEM_VAZIA = "Pode escrever a sua dúvida?"
PEDIDO_ANTES_DE_TENTAR = (
    "Ainda não vou te dar a resposta: o melhor jeito de aprender é tentar primeiro. "
    "Marque a alternativa que parecer mais certa, mesmo na dúvida, e eu te ajudo a partir daí."
)
PEDIDO_DEPOIS_DE_TENTAR = (
    "Eu não entrego a resposta direto, mas posso te dar outra pista. "
    "Se preferir ver a resolução completa, use a opção de pedir a explicação."
)
PISTA_PADRAO_1 = (
    "Vamos revisar juntos. Releia a pergunta com calma: o que exatamente ela pede? "
    "Confira se você usou todos os dados do enunciado."
)
PISTA_PADRAO_2 = "Uma dica: {engano} Confira se foi isso que aconteceu na sua conta e tente de novo."
PISTA_PADRAO_2_GENERICA = (
    "Uma dica: refaça a conta passo a passo, escrevendo cada etapa, e confira as unidades "
    "e o que a pergunta pede no final. Qual foi o primeiro passo que você fez?"
)
CONVERSA_PADRAO = (
    "Não consegui pensar em uma boa pista agora. Comece listando os dados do enunciado: "
    "qual deles parece mais importante para responder?"
)
CONVERSA_LIVRE_PADRAO = "Não consegui responder agora. Tente de novo em alguns instantes."
ACERTO_PADRAO = (
    "Isso mesmo, a alternativa {letra} está correta! "
    "Como você chegou nela? Explicar com as suas palavras ajuda a fixar o raciocínio."
)
EXPLICACAO_PADRAO = "A resposta é a alternativa {letra}.\n\n{resolucao}"


@dataclass(frozen=True)
class ResultadoDaResposta:
    acertou: bool
    estado: Estado
    mensagem: Mensagem


class Tutor:
    def __init__(self, banco: BancoDeQuestoes, prompts: Prompts, ia: ClienteDeIA | None = None):
        self.banco = banco
        self.prompts = prompts
        self.ia = ia
        self._busca: BuscaDeQuestoes | None = None

    @property
    def busca(self) -> BuscaDeQuestoes:
        """Índice das questões parecidas, montado no primeiro uso."""
        if self._busca is None:
            self._busca = BuscaDeQuestoes(self.banco)
        return self._busca

    def nova_sessao(self, questao_id: str) -> Sessao:
        self.banco.obter(questao_id)  # garante que a questão existe
        return Sessao(questao_id=questao_id, versao_prompt=self.prompts.versao)

    # ------------------------------------------------------------ ações do aluno

    async def responder(self, sessao: Sessao, letra: str) -> ResultadoDaResposta:
        letra = letra.strip().upper()
        if letra not in LETRAS:
            raise TransicaoInvalida("alternativa_invalida", "Escolha uma alternativa de A a E.")
        if letra in sessao.tentativas:
            raise TransicaoInvalida("alternativa_repetida", f"Você já tentou a alternativa {letra}.")
        questao = self.banco.obter(sessao.questao_id)
        acertou = letra == questao.gabarito
        novo_estado = apos_resposta(sessao.estado, acertou)

        sessao.registrar(Mensagem("aluno", f"Marquei a alternativa {letra}.", sessao.estado))
        sessao.tentativas.append(letra)
        sessao.estado = novo_estado
        logger.info("resposta", extra={"sessao": sessao.id, "acertou": acertou, "estado": novo_estado.value})

        if acertou:
            momento = "acerto"
        elif novo_estado == Estado.EXPLICACAO:
            momento = "explicacao"
        else:
            momento = novo_estado.value  # pista_1 ou pista_2
        mensagem = await self._falar(sessao, questao, momento)
        return ResultadoDaResposta(acertou, novo_estado, mensagem)

    async def explicar(self, sessao: Sessao, confirmado: bool) -> Mensagem:
        questao = self.banco.obter(sessao.questao_id)
        sessao.estado = apos_pedido_de_explicacao(sessao.estado, confirmado)
        sessao.registrar(Mensagem("aluno", "Quero ver a explicação.", sessao.estado))
        return await self._falar(sessao, questao, "explicacao")

    async def conversar(self, sessao: Sessao, texto: str) -> Mensagem:
        """Mesmo que `conversar_em_trechos`, mas devolve a mensagem inteira."""
        async for _ in self.conversar_em_trechos(sessao, texto):
            pass
        return sessao.mensagens[-1]

    async def conversar_em_trechos(self, sessao: Sessao, texto: str) -> AsyncIterator[str]:
        """Responde a uma mensagem do aluno, em trechos (para streaming).

        Com a resposta protegida, a mensagem é gerada inteira, verificada e só depois
        enviada em trechos. Com a resposta revelada, os trechos vêm direto da IA.
        """
        questao = self.banco.obter(sessao.questao_id)
        verificacao = guardrails.verificar_entrada(texto)
        if not verificacao.permitida:
            # o texto bloqueado não é guardado: pode ser longo ou conter manipulação
            sessao.registrar(Mensagem("aluno", "[mensagem bloqueada]", sessao.estado, protecao="entrada"))
            logger.info("entrada bloqueada", extra={"sessao": sessao.id, "motivo": verificacao.motivo})
            fixa = {"vazia": MENSAGEM_VAZIA, "longa": MENSAGEM_LONGA, "manipulacao": MENSAGEM_DE_MANIPULACAO}
            mensagem = sessao.registrar(Mensagem("tutor", fixa[verificacao.motivo], sessao.estado, protecao="entrada"))
            for trecho in _em_trechos(mensagem.texto):
                yield trecho
            return

        sessao.registrar(Mensagem("aluno", texto.strip(), sessao.estado))
        protegido = sessao.estado in ESTADOS_PROTEGIDOS
        if protegido and guardrails.pede_a_resposta(texto):
            fixa = PEDIDO_ANTES_DE_TENTAR if sessao.estado == Estado.RESPONDENDO else PEDIDO_DEPOIS_DE_TENTAR
            mensagem = sessao.registrar(Mensagem("tutor", fixa, sessao.estado, protecao="pedido_de_resposta"))
            for trecho in _em_trechos(mensagem.texto):
                yield trecho
            return

        if protegido or self.ia is None:
            mensagem = await self._falar(sessao, questao, "conversa")
            for trecho in _em_trechos(mensagem.texto):
                yield trecho
            return

        # resposta já revelada: streaming direto da IA
        sistema = self.prompts.sistema(questao, sessao, "conversa")
        recebido: list[str] = []
        try:
            async for trecho in self.ia.gerar_em_trechos(sistema, _conversa(sessao), self.banco.imagens(questao)):
                recebido.append(trecho)
                yield trecho
            sessao.registrar(Mensagem("tutor", "".join(recebido).strip(), sessao.estado))
        except ErroDaIA:
            texto_final = "".join(recebido).strip()
            if texto_final:
                sessao.registrar(Mensagem("tutor", texto_final, sessao.estado, protecao="plano_b"))
            else:
                mensagem = sessao.registrar(Mensagem("tutor", CONVERSA_LIVRE_PADRAO, sessao.estado, protecao="plano_b"))
                for trecho in _em_trechos(mensagem.texto):
                    yield trecho

    # ------------------------------------------------------------ geração

    async def _falar(self, sessao: Sessao, questao: Questao, momento: str) -> Mensagem:
        protegido = sessao.estado in ESTADOS_PROTEGIDOS
        if self.ia is None:
            return sessao.registrar(self._plano_b(sessao, questao, momento, "plano_b"))

        vazamentos = 0
        for tentativa in range(TENTATIVAS_CONTRA_VAZAMENTO):
            sistema = self.prompts.sistema(questao, sessao, momento, reforco=tentativa > 0)
            try:
                resposta = await self.ia.gerar(sistema, _conversa(sessao), self.banco.imagens(questao))
            except ErroDaIA:
                logger.warning("plano B", extra={"sessao": sessao.id, "momento": momento})
                mensagem = self._plano_b(sessao, questao, momento, "plano_b")
                mensagem.vazamentos_bloqueados = vazamentos
                return sessao.registrar(mensagem)
            if protegido and guardrails.revela_a_resposta(resposta.texto, questao):
                vazamentos += 1
                logger.warning("vazamento bloqueado", extra={"sessao": sessao.id, "momento": momento})
                continue
            return sessao.registrar(
                Mensagem(
                    "tutor",
                    resposta.texto,
                    sessao.estado,
                    vazamentos_bloqueados=vazamentos,
                    modelo=resposta.modelo,
                    tokens=resposta.tokens,
                )
            )

        mensagem = self._plano_b(sessao, questao, momento, "saida")
        mensagem.vazamentos_bloqueados = vazamentos
        return sessao.registrar(mensagem)

    def _plano_b(self, sessao: Sessao, questao: Questao, momento: str, protecao: Protecao) -> Mensagem:
        """Mensagem escrita à mão para quando a IA falha ou vaza a resposta duas vezes."""
        if momento == "acerto":
            texto = ACERTO_PADRAO.format(letra=questao.gabarito)
        elif momento == "explicacao":
            texto = EXPLICACAO_PADRAO.format(letra=questao.gabarito, resolucao=questao.resolucao)
        elif momento == "pista_1":
            texto = PISTA_PADRAO_1
        elif momento == "pista_2":
            texto = self._pista_padrao_2(sessao, questao)
        elif sessao.estado in ESTADOS_PROTEGIDOS:
            texto = CONVERSA_PADRAO
        else:
            texto = CONVERSA_LIVRE_PADRAO
        return Mensagem("tutor", texto, sessao.estado, protecao=protecao)

    @staticmethod
    def _pista_padrao_2(sessao: Sessao, questao: Questao) -> str:
        """Usa o engano anotado da última alternativa marcada, se ele não entregar a resposta."""
        engano = questao.alternativa(sessao.tentativas[-1]).engano_provavel if sessao.tentativas else None
        if engano and not guardrails.revela_a_resposta(engano, questao):
            return PISTA_PADRAO_2.format(engano=_em_segunda_pessoa(engano))
        return PISTA_PADRAO_2_GENERICA


def _conversa(sessao: Sessao) -> list[Turno]:
    """Histórico no formato da IA. A IA precisa terminar respondendo a uma fala do aluno."""
    turnos: list[Turno] = [(m.papel, m.texto) for m in sessao.mensagens]
    if not turnos or turnos[-1][0] != "aluno":
        turnos.append(("aluno", "Continue."))
    return turnos


def _em_trechos(texto: str) -> list[str]:
    palavras = texto.split(" ")
    return [
        " ".join(palavras[i : i + PALAVRAS_POR_TRECHO]) + (" " if i + PALAVRAS_POR_TRECHO < len(palavras) else "")
        for i in range(0, len(palavras), PALAVRAS_POR_TRECHO)
    ]


def _em_segunda_pessoa(engano: str) -> str:
    """As anotações descrevem o engano no passado ("Somou..."); aqui viram uma suspeita."""
    return f"talvez você tenha feito isto: {engano[0].lower()}{engano[1:]}"
