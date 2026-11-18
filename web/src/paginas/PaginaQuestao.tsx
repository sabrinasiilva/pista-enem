import { ArrowLeft, BookOpen, ExternalLink, Lightbulb, PartyPopper, Shuffle } from 'lucide-react'
import { type ReactNode, useCallback, useEffect, useRef, useState } from 'react'
import { api, ErroDaApi } from '../api'
import { daAba } from '../armazenamento'
import { Alternativas } from '../componentes/Alternativas'
import { AvisoModoBasico, CaixaDeErro, Carregando } from '../componentes/Avisos'
import { Conversa } from '../componentes/Conversa'
import { Progresso } from '../componentes/Progresso'
import { TextoRico } from '../componentes/TextoRico'
import { useConta } from '../conta'
import { irPara } from '../rotas'
import { ESTADOS_FINAIS, type Letra, type Questao, type Sessao } from '../tipos'

type Acao = 'resposta' | 'mensagem' | 'explicacao'

// a sessão guardada na aba é separada por conta: ao entrar, a questão começa numa sessão da conta
const chaveDaSessao = (questaoId: string, conta: string) => `pista:sessao:${conta}:${questaoId}`

function mensagemDe(erro: unknown): string {
  return erro instanceof ErroDaApi ? erro.message : 'Algo deu errado. Tente de novo.'
}

/** Retoma a sessão desta aba, se ainda existir; senão abre uma nova. */
async function abrirSessao(questaoId: string, conta: string): Promise<Sessao> {
  const guardada = daAba.ler(chaveDaSessao(questaoId, conta))
  if (guardada) {
    try {
      const sessao = await api.obterSessao(guardada)
      // uma questão já terminada recomeça: voltar a ela é para refazer (revisão, modo foco)
      if (!ESTADOS_FINAIS.includes(sessao.estado)) return sessao
    } catch (erro) {
      if (!(erro instanceof ErroDaApi && erro.status === 404)) throw erro
    }
  }
  const nova = await api.criarSessao(questaoId)
  daAba.gravar(chaveDaSessao(questaoId, conta), nova.id)
  return nova
}

interface Props {
  id: string
  /** chamado uma vez quando a resposta é revelada (usado pelo modo foco) */
  aoTerminar?: (sessao: Sessao) => void
  /** botão mostrado no fim, no lugar de "Outra questão" */
  acaoFinal?: ReactNode
  semVoltar?: boolean
}

export function PaginaQuestao({ id, aoTerminar, acaoFinal, semVoltar = false }: Props) {
  const { usuario, carregando: contaCarregando } = useConta()
  const conta = usuario?.id ?? 'anonimo'
  const [questao, setQuestao] = useState<Questao | null>(null)
  const [sessao, setSessao] = useState<Sessao | null>(null)
  const [modoBasico, setModoBasico] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [erroDaAcao, setErroDaAcao] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState<Acao | null>(null)
  const [selecionada, setSelecionada] = useState<Letra | null>(null)
  const [confirmando, setConfirmando] = useState(false)
  const [emAndamento, setEmAndamento] = useState<{ aluno: string; tutor: string } | null>(null)
  const destaque = useRef<HTMLElement>(null)
  const rolarParaPista = useRef(false)

  const carregar = useCallback(async () => {
    setErro(null)
    setQuestao(null)
    setSessao(null)
    try {
      const [dadosDaQuestao, dadosDaSessao] = await Promise.all([api.obterQuestao(id), abrirSessao(id, conta)])
      setQuestao(dadosDaQuestao)
      setSessao(dadosDaSessao)
      api
        .saude()
        .then((saude) => setModoBasico(saude.ia !== 'gemini'))
        .catch(() => {})
    } catch (e) {
      setErro(
        e instanceof ErroDaApi && e.codigo === 'questao_nao_encontrada'
          ? 'Essa questão não existe ou saiu do banco.'
          : mensagemDe(e),
      )
    }
  }, [id, conta])

  useEffect(() => {
    // espera saber se há conta, para a sessão já nascer ligada a ela
    if (!contaCarregando) void carregar()
  }, [carregar, contaCarregando])

  const terminou = sessao !== null && ESTADOS_FINAIS.includes(sessao.estado)
  useEffect(() => {
    // avisa uma única vez, quando a resposta é revelada
    if (terminou && sessao) aoTerminar?.(sessao)
  }, [terminou])

  /** Executa uma ação e depois sincroniza a sessão com o servidor, mesmo se a ação falhar. */
  const executar = async (acao: Acao, tarefa: (sessaoId: string) => Promise<unknown>) => {
    if (!sessao || ocupado) return
    setOcupado(acao)
    setErroDaAcao(null)
    try {
      await tarefa(sessao.id)
    } catch (e) {
      setErroDaAcao(mensagemDe(e))
    }
    try {
      setSessao(await api.obterSessao(sessao.id))
    } catch (e) {
      setErroDaAcao(mensagemDe(e))
    }
    setOcupado(null)
  }

  const responder = () =>
    selecionada &&
    executar('resposta', async (sessaoId) => {
      rolarParaPista.current = true
      await api.responder(sessaoId, selecionada)
      setSelecionada(null)
    })

  const explicar = () =>
    executar('explicacao', async (sessaoId) => {
      setConfirmando(false)
      rolarParaPista.current = true
      await api.explicar(sessaoId)
    })

  const conversar = (texto: string) =>
    executar('mensagem', async (sessaoId) => {
      setEmAndamento({ aluno: texto, tutor: '' })
      try {
        await api.conversar(sessaoId, texto, (trecho) =>
          setEmAndamento((atual) => (atual ? { ...atual, tutor: atual.tutor + trecho } : atual)),
        )
      } finally {
        setEmAndamento(null)
      }
    })

  const outraQuestao = async () => {
    try {
      const outras = (await api.listarQuestoes()).filter((q) => q.id !== id)
      irPara({ pagina: 'questao', id: outras[Math.floor(Math.random() * outras.length)].id })
    } catch (e) {
      setErroDaAcao(mensagemDe(e))
    }
  }

  // a última fala do tutor fica em destaque perto das alternativas, onde o aluno vai tentar de novo
  const ultimaDoTutor = sessao && !emAndamento ? sessao.mensagens.findLast((m) => m.papel === 'tutor') : undefined

  // depois de responder ou pedir a explicação, rola até a pista (no celular ela fica fora da tela)
  useEffect(() => {
    if (!rolarParaPista.current || !ultimaDoTutor) return
    rolarParaPista.current = false
    destaque.current?.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
  }, [ultimaDoTutor])

  if (erro) {
    return (
      <main className="mx-auto max-w-5xl space-y-4 px-4 py-8">
        <CaixaDeErro mensagem={erro} aoTentarDeNovo={carregar} />
        <VoltarParaInicio />
      </main>
    )
  }
  if (!questao || !sessao) return <Carregando texto="Carregando a questão…" />

  const encerrada = ESTADOS_FINAIS.includes(sessao.estado)
  const podeExplicar = sessao.estado === 'pista_1' || sessao.estado === 'pista_2'

  return (
    <main className="mx-auto max-w-5xl px-4 py-6">
      {(!semVoltar || modoBasico) && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          {!semVoltar && <VoltarParaInicio />}
          {modoBasico && <AvisoModoBasico compacto />}
        </div>
      )}

      <div className="mt-4 grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem] lg:items-start">
        <div className="min-w-0 space-y-6">
          <article className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm sm:p-6">
            <header className="mb-4 flex flex-wrap items-center gap-2 text-sm text-stone-500">
              <span className="font-semibold text-stone-900">
                ENEM {questao.ano} · Questão {questao.numero}
              </span>
              <span
                className="rounded-full bg-stone-100 px-2 py-0.5 text-xs font-medium text-stone-600"
                title={questao.habilidade.descricao}
              >
                Habilidade {questao.habilidade.codigo}
              </span>
            </header>
            <TextoRico texto={questao.enunciado} className="text-[1.05rem] leading-relaxed" />
            <p className="mt-5 border-t border-stone-100 pt-3 text-xs text-stone-500">
              Fonte: Inep, {questao.fonte.prova}.{' '}
              <a
                href={questao.fonte.url}
                target="_blank"
                rel="noreferrer noopener"
                className="inline-flex items-center gap-0.5 underline"
              >
                Prova oficial
                <ExternalLink className="size-3" aria-hidden />
              </a>
            </p>
          </article>

          <section aria-labelledby="titulo-resposta" className="space-y-4">
            <h2 id="titulo-resposta" className="sr-only">
              Sua resposta
            </h2>
            <Progresso estado={sessao.estado} />
            {(ocupado === 'resposta' || ocupado === 'explicacao') && (
              <div
                role="status"
                className="flex items-center gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-900"
              >
                <span aria-hidden className="flex gap-1">
                  <span className="size-2 animate-bounce rounded-full bg-amber-500 [animation-delay:-0.3s]" />
                  <span className="size-2 animate-bounce rounded-full bg-amber-500 [animation-delay:-0.15s]" />
                  <span className="size-2 animate-bounce rounded-full bg-amber-500" />
                </span>
                {ocupado === 'resposta' ? 'O tutor está pensando na sua pista…' : 'O tutor está preparando a explicação…'}
              </div>
            )}
            {ultimaDoTutor && ocupado !== 'resposta' && ocupado !== 'explicacao' && (
              <aside
                ref={destaque}
                aria-label="Última mensagem do tutor"
                className={`flex scroll-mt-20 gap-3 rounded-2xl border p-4 text-stone-900 ${
                  sessao.estado === 'concluida' ? 'border-emerald-200 bg-emerald-50' : 'border-amber-200 bg-amber-50'
                }`}
              >
                {sessao.estado === 'concluida' ? (
                  <PartyPopper className="mt-0.5 size-5 shrink-0 text-emerald-600" aria-hidden />
                ) : (
                  <Lightbulb className="mt-0.5 size-5 shrink-0 text-amber-600" aria-hidden />
                )}
                <TextoRico texto={ultimaDoTutor.texto} className="min-w-0 flex-1" />
              </aside>
            )}
            <Alternativas
              alternativas={questao.alternativas}
              tentativas={sessao.tentativas}
              gabarito={sessao.gabarito}
              selecionada={selecionada}
              bloqueadas={ocupado !== null || encerrada}
              aoSelecionar={setSelecionada}
            />

            {erroDaAcao && <CaixaDeErro mensagem={erroDaAcao} />}

            {!encerrada && (
              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={responder}
                  disabled={!selecionada || ocupado !== null}
                  className="rounded-xl bg-stone-900 px-6 py-3 font-semibold text-white shadow-sm transition hover:bg-stone-700 disabled:bg-stone-300 disabled:shadow-none"
                >
                  {ocupado === 'resposta' ? 'Conferindo…' : 'Responder'}
                </button>
                {podeExplicar && !confirmando && (
                  <button
                    type="button"
                    onClick={() => setConfirmando(true)}
                    disabled={ocupado !== null}
                    className="inline-flex items-center gap-1.5 rounded-xl px-3 py-3 text-sm font-medium text-stone-600 underline-offset-4 hover:underline disabled:opacity-40"
                  >
                    <BookOpen className="size-4" aria-hidden />
                    Quero a explicação completa
                  </button>
                )}
              </div>
            )}

            {confirmando && (
              <div
                role="alertdialog"
                aria-labelledby="titulo-confirmacao"
                className="rounded-2xl border border-amber-300 bg-amber-50 p-4"
              >
                <p id="titulo-confirmacao" className="font-medium text-amber-900">
                  Você vai ver a resposta e a resolução completa. Prefere tentar mais uma vez?
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={explicar}
                    className="rounded-lg bg-amber-900 px-3 py-2 text-sm font-medium text-white hover:bg-amber-800"
                  >
                    Ver a explicação
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmando(false)}
                    className="rounded-lg border border-amber-300 bg-white px-3 py-2 text-sm font-medium text-amber-900 hover:bg-amber-100"
                  >
                    Vou tentar mais uma vez
                  </button>
                </div>
              </div>
            )}

            {encerrada && (
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-stone-200 bg-white p-4">
                <p className="font-semibold">
                  {sessao.estado === 'concluida'
                    ? `Você acertou! A resposta é a alternativa ${sessao.gabarito}.`
                    : `A resposta é a alternativa ${sessao.gabarito}.`}
                </p>
                {acaoFinal ?? (
                  <button
                    type="button"
                    onClick={outraQuestao}
                    className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-stone-700"
                  >
                    <Shuffle className="size-4" aria-hidden />
                    Outra questão
                  </button>
                )}
              </div>
            )}
          </section>
        </div>

        <div className="lg:sticky lg:top-20">
          <Conversa
            mensagens={sessao.mensagens}
            emAndamento={emAndamento}
            ocupado={ocupado !== null}
            aoEnviar={conversar}
          />
        </div>
      </div>
    </main>
  )
}

function VoltarParaInicio() {
  return (
    <a href="#/" className="inline-flex items-center gap-1 text-sm text-stone-600 hover:text-stone-900">
      <ArrowLeft className="size-4" aria-hidden />
      Todas as questões
    </a>
  )
}
