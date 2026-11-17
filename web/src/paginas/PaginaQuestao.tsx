import { ArrowLeft, BookOpen, ExternalLink, Lightbulb, Shuffle } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { api, ErroDaApi } from '../api'
import { Alternativas } from '../componentes/Alternativas'
import { AvisoModoBasico, CaixaDeErro, Carregando } from '../componentes/Avisos'
import { Conversa } from '../componentes/Conversa'
import { Progresso } from '../componentes/Progresso'
import { TextoRico } from '../componentes/TextoRico'
import { irPara } from '../rotas'
import { ESTADOS_FINAIS, type Letra, type Questao, type Sessao } from '../tipos'

type Acao = 'resposta' | 'mensagem' | 'explicacao'

const chaveDaSessao = (questaoId: string) => `pista:sessao:${questaoId}`

function lerSessaoGuardada(questaoId: string): string | null {
  try {
    return sessionStorage.getItem(chaveDaSessao(questaoId))
  } catch {
    return null
  }
}

function guardarSessao(questaoId: string, sessaoId: string) {
  try {
    sessionStorage.setItem(chaveDaSessao(questaoId), sessaoId)
  } catch {
    // sem armazenamento (modo privado): a sessão só não é retomada ao recarregar
  }
}

function mensagemDe(erro: unknown): string {
  return erro instanceof ErroDaApi ? erro.message : 'Algo deu errado. Tente de novo.'
}

/** Retoma a sessão desta aba, se ainda existir; senão abre uma nova. */
async function abrirSessao(questaoId: string): Promise<Sessao> {
  const guardada = lerSessaoGuardada(questaoId)
  if (guardada) {
    try {
      return await api.obterSessao(guardada)
    } catch (erro) {
      if (!(erro instanceof ErroDaApi && erro.status === 404)) throw erro
    }
  }
  const nova = await api.criarSessao(questaoId)
  guardarSessao(questaoId, nova.id)
  return nova
}

export function PaginaQuestao({ id }: { id: string }) {
  const [questao, setQuestao] = useState<Questao | null>(null)
  const [sessao, setSessao] = useState<Sessao | null>(null)
  const [modoBasico, setModoBasico] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [erroDaAcao, setErroDaAcao] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState<Acao | null>(null)
  const [selecionada, setSelecionada] = useState<Letra | null>(null)
  const [confirmando, setConfirmando] = useState(false)
  const [emAndamento, setEmAndamento] = useState<{ aluno: string; tutor: string } | null>(null)

  const carregar = useCallback(async () => {
    setErro(null)
    setQuestao(null)
    setSessao(null)
    try {
      const [dadosDaQuestao, dadosDaSessao] = await Promise.all([api.obterQuestao(id), abrirSessao(id)])
      setQuestao(dadosDaQuestao)
      setSessao(dadosDaSessao)
      api
        .saude()
        .then((saude) => setModoBasico(saude.ia === 'desativada'))
        .catch(() => {})
    } catch (e) {
      setErro(
        e instanceof ErroDaApi && e.codigo === 'questao_nao_encontrada'
          ? 'Essa questão não existe ou saiu do banco.'
          : mensagemDe(e),
      )
    }
  }, [id])

  useEffect(() => {
    void carregar()
  }, [carregar])

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
      await api.responder(sessaoId, selecionada)
      setSelecionada(null)
    })

  const explicar = () =>
    executar('explicacao', async (sessaoId) => {
      setConfirmando(false)
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

  if (erro) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-8">
        <CaixaDeErro mensagem={erro} aoTentarDeNovo={carregar} />
        <VoltarParaInicio />
      </main>
    )
  }
  if (!questao || !sessao) return <Carregando texto="Carregando a questão…" />

  const encerrada = ESTADOS_FINAIS.includes(sessao.estado)
  const podeExplicar = sessao.estado === 'pista_1' || sessao.estado === 'pista_2'
  // a última fala do tutor fica em destaque perto das alternativas, onde o aluno vai tentar de novo
  const ultimaDoTutor = emAndamento ? null : sessao.mensagens.findLast((m) => m.papel === 'tutor')

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-4 py-6">
      <VoltarParaInicio />

      <article className="rounded-2xl border border-stone-200 bg-white p-4 sm:p-6">
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
        <TextoRico texto={questao.enunciado} className="leading-relaxed" />
        <p className="mt-4 text-xs text-stone-500">
          Fonte: Inep, {questao.fonte.prova}.{' '}
          <a href={questao.fonte.url} target="_blank" rel="noreferrer noopener" className="inline-flex items-center gap-0.5 underline">
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
        {ultimaDoTutor && (
          <aside
            aria-label="Última mensagem do tutor"
            className="flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-stone-900"
          >
            <Lightbulb className="mt-0.5 size-5 shrink-0 text-amber-600" aria-hidden />
            <TextoRico texto={ultimaDoTutor.texto} className="flex-1" />
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
              className="rounded-xl bg-stone-900 px-5 py-3 font-semibold text-white hover:bg-stone-800 disabled:opacity-40"
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
          <div role="alertdialog" aria-labelledby="titulo-confirmacao" className="rounded-xl border border-amber-300 bg-amber-50 p-4">
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
                className="rounded-lg border border-amber-300 px-3 py-2 text-sm font-medium text-amber-900 hover:bg-amber-100"
              >
                Vou tentar mais uma vez
              </button>
            </div>
          </div>
        )}

        {encerrada && (
          <div
            className={`rounded-xl p-4 ${sessao.estado === 'concluida' ? 'bg-emerald-50 text-emerald-900' : 'bg-stone-100 text-stone-800'}`}
          >
            <p className="font-semibold">
              {sessao.estado === 'concluida'
                ? `Você acertou! A resposta é a alternativa ${sessao.gabarito}.`
                : `A resposta é a alternativa ${sessao.gabarito}.`}
            </p>
            <button
              type="button"
              onClick={outraQuestao}
              className="mt-3 inline-flex items-center gap-2 rounded-lg bg-stone-900 px-3 py-2 text-sm font-medium text-white hover:bg-stone-800"
            >
              <Shuffle className="size-4" aria-hidden />
              Outra questão
            </button>
          </div>
        )}
      </section>

      {modoBasico && <AvisoModoBasico />}

      <Conversa
        mensagens={sessao.mensagens}
        emAndamento={emAndamento}
        ocupado={ocupado !== null}
        aoEnviar={conversar}
      />
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
