import { CheckCircle2, Clock, Lightbulb, BookOpen, Play, RotateCcw, Square, Target } from 'lucide-react'
import { type ReactNode, useEffect, useState } from 'react'
import { api, ErroDaApi } from '../api'
import { areasEmFoco, habilidadesDasAreas } from '../areas'
import { CaixaDeErro } from '../componentes/Avisos'
import { SeletorDeAreas } from '../componentes/SeletorDeAreas'
import { Botao, Cartao, Pagina } from '../componentes/ui'
import { useConta } from '../conta'
import { type EstadoDoFoco, gravarFoco, iniciarFoco, lerFoco } from '../foco'
import { endereco } from '../rotas'
import type { Sessao } from '../tipos'
import { PaginaQuestao } from './PaginaQuestao'

const QUANTIDADES = [5, 10, 15]
const TEMPOS: (number | null)[] = [null, 15, 25, 45]

export function formatarTempo(segundos: number): string {
  const total = Math.max(0, Math.round(segundos))
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}

function useAgora(ativo: boolean): number {
  const [agora, setAgora] = useState(Date.now)
  useEffect(() => {
    if (!ativo) return
    const relogio = setInterval(() => setAgora(Date.now()), 1000)
    return () => clearInterval(relogio)
  }, [ativo])
  return agora
}

function Opcoes<T>({ rotulo, opcoes, valor, aoEscolher, nome }: {
  rotulo: string
  opcoes: T[]
  valor: T
  aoEscolher: (valor: T) => void
  nome: (valor: T) => string
}) {
  return (
    <div role="radiogroup" aria-label={rotulo} className="grid grid-cols-3 gap-2 sm:grid-cols-4">
      {opcoes.map((opcao) => (
        <button
          key={nome(opcao)}
          type="button"
          role="radio"
          aria-checked={valor === opcao}
          onClick={() => aoEscolher(opcao)}
          className={`rounded-xl border py-2.5 text-sm font-semibold transition ${
            valor === opcao ? 'border-stone-900 bg-stone-900 text-white' : 'border-stone-200 bg-white hover:border-stone-400'
          }`}
        >
          {nome(opcao)}
        </button>
      ))}
    </div>
  )
}

function Configurar({ aoComecar }: { aoComecar: () => void }) {
  const { usuario } = useConta()
  const [quantidade, setQuantidade] = useState(5)
  const [minutos, setMinutos] = useState<number | null>(25)
  const [areas, setAreas] = useState(() => areasEmFoco(usuario?.habilidades_foco ?? []))
  const [erro, setErro] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(false)

  const comecar = async () => {
    setErro(null)
    setCarregando(true)
    try {
      const questoes = await api.recomendacoes(quantidade, habilidadesDasAreas(areas))
      iniciarFoco({ ids: questoes.map((q) => q.id), minutos })
      aoComecar()
    } catch (e) {
      setErro(e instanceof ErroDaApi ? e.message : 'Não consegui montar o foco. Tente de novo.')
      setCarregando(false)
    }
  }

  return (
    <Pagina
      titulo="Modo foco"
      subtitulo="Uma sequência de questões, com tempo, sem distração. No fim, um resumo de como foi."
    >
      <Cartao titulo="Quantas questões?">
        <Opcoes rotulo="Quantidade de questões" opcoes={QUANTIDADES} valor={quantidade} aoEscolher={setQuantidade} nome={String} />
      </Cartao>
      <Cartao titulo="Quanto tempo?">
        <Opcoes
          rotulo="Duração"
          opcoes={TEMPOS}
          valor={minutos}
          aoEscolher={setMinutos}
          nome={(m) => (m ? `${m} min` : 'Livre')}
        />
        <p className="mt-3 text-sm text-stone-500">25 minutos é um bom bloco de estudo (técnica Pomodoro).</p>
      </Cartao>
      <Cartao titulo="Em que focar?">
        <p className="mb-3 text-sm text-stone-500">
          {usuario
            ? 'Primeiro vêm as questões que você errou e ainda não refez; depois, as das áreas escolhidas.'
            : 'Deixe em branco para misturar todos os assuntos.'}
        </p>
        <SeletorDeAreas selecionadas={areas} aoMudar={setAreas} />
      </Cartao>
      {erro && <CaixaDeErro mensagem={erro} />}
      <Botao onClick={comecar} carregando={carregando} className="w-full py-3 text-lg sm:w-auto sm:px-8">
        <Play className="size-5" aria-hidden />
        Começar
      </Botao>
    </Pagina>
  )
}

function EmAndamento({ foco, salvar }: { foco: EstadoDoFoco; salvar: (foco: EstadoDoFoco) => void }) {
  const agora = useAgora(true)
  const id = foco.ids[foco.indice]
  const ultima = foco.indice === foco.ids.length - 1
  const passados = (agora - foco.inicio) / 1000
  const restantes = foco.minutos ? foco.minutos * 60 - passados : null
  const esgotado = restantes !== null && restantes <= 0
  const terminada = Boolean(foco.resultados[id])

  const encerrar = () => salvar({ ...foco, fim: Date.now() })
  const proxima = () => (ultima ? encerrar() : salvar({ ...foco, indice: foco.indice + 1 }))
  const registrar = (sessao: Sessao) => {
    if (foco.resultados[id]) return
    salvar({ ...foco, resultados: { ...foco.resultados, [id]: { estado: sessao.estado, tentativas: sessao.tentativas.length } } })
  }

  return (
    <>
      <div className="sticky top-[57px] z-10 border-b border-stone-200 bg-white/95 backdrop-blur lg:top-0">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-3">
            <Target className="size-5 text-amber-500" aria-hidden />
            <span className="font-semibold">
              Questão {foco.indice + 1} de {foco.ids.length}
            </span>
            <ol aria-hidden className="hidden gap-1 sm:flex">
              {foco.ids.map((questao, indice) => (
                <li
                  key={questao}
                  className={`size-2 rounded-full ${
                    foco.resultados[questao] ? 'bg-emerald-500' : indice === foco.indice ? 'bg-amber-500' : 'bg-stone-300'
                  }`}
                />
              ))}
            </ol>
          </div>
          <div className="flex items-center gap-3">
            <span
              role="timer"
              aria-label={restantes !== null ? 'Tempo restante' : 'Tempo de estudo'}
              className={`inline-flex items-center gap-1.5 font-mono text-sm font-semibold ${esgotado ? 'text-red-600' : 'text-stone-700'}`}
            >
              <Clock className="size-4" aria-hidden />
              {restantes !== null ? formatarTempo(restantes) : formatarTempo(passados)}
            </span>
            <Botao variante="fantasma" onClick={encerrar} className="px-3 py-1.5 text-sm">
              <Square className="size-3.5" aria-hidden />
              Encerrar
            </Botao>
          </div>
        </div>
      </div>
      {esgotado && !terminada && (
        <div className="mx-auto mt-4 max-w-5xl px-4">
          <p role="status" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800">
            O tempo acabou. Termine esta questão com calma ou encerre para ver o resumo.
          </p>
        </div>
      )}
      <PaginaQuestao
        key={id}
        id={id}
        semVoltar
        aoTerminar={registrar}
        acaoFinal={
          <Botao onClick={proxima}>{ultima || esgotado ? 'Ver resumo' : 'Próxima questão'}</Botao>
        }
      />
    </>
  )
}

function Numero({ icone, valor, rotulo }: { icone: ReactNode; valor: number | string; rotulo: string }) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
      {icone}
      <p className="mt-2 text-2xl font-bold">{valor}</p>
      <p className="text-sm text-stone-500">{rotulo}</p>
    </div>
  )
}

function Resumo({ foco, aoRecomecar }: { foco: EstadoDoFoco; aoRecomecar: () => void }) {
  const { usuario } = useConta()
  const resultados = foco.ids.map((id) => ({ id, resultado: foco.resultados[id] }))
  const feitas = resultados.filter((r) => r.resultado)
  const dePrimeira = feitas.filter((r) => r.resultado.estado === 'concluida' && r.resultado.tentativas === 1).length
  const comPista = feitas.filter((r) => r.resultado.estado === 'concluida' && r.resultado.tentativas > 1).length
  const explicacao = feitas.filter((r) => r.resultado.estado === 'explicacao').length
  const duracao = ((foco.fim ?? Date.now()) - foco.inicio) / 1000

  return (
    <Pagina titulo="Foco concluído" subtitulo={`Você estudou ${formatarTempo(duracao)} e resolveu ${feitas.length} de ${foco.ids.length} questões.`}>
      <div className="grid grid-cols-3 gap-3">
        <Numero icone={<CheckCircle2 className="size-5 text-emerald-500" aria-hidden />} valor={dePrimeira} rotulo="de primeira" />
        <Numero icone={<Lightbulb className="size-5 text-amber-500" aria-hidden />} valor={comPista} rotulo="com pista" />
        <Numero icone={<BookOpen className="size-5 text-stone-400" aria-hidden />} valor={explicacao} rotulo="com explicação" />
      </div>
      <Cartao titulo="Questões">
        <ul className="divide-y divide-stone-200">
          {resultados.map(({ id, resultado }) => (
            <li key={id} className="flex items-center justify-between gap-3 py-3">
              <a href={endereco({ pagina: 'questao', id })} className="font-medium underline-offset-4 hover:underline">
                ENEM {id.replace('-', ' · Q')}
              </a>
              <span className="text-sm text-stone-500">
                {!resultado
                  ? 'Não feita'
                  : resultado.estado === 'explicacao'
                    ? 'Viu a explicação'
                    : resultado.tentativas === 1
                      ? 'Acertou de primeira'
                      : `Acertou na ${resultado.tentativas}ª`}
              </span>
            </li>
          ))}
        </ul>
      </Cartao>
      <div className="flex flex-wrap gap-3">
        <Botao onClick={aoRecomecar}>
          <RotateCcw className="size-4" aria-hidden />
          Novo foco
        </Botao>
        {usuario && (comPista > 0 || explicacao > 0) && (
          <a
            href={endereco({ pagina: 'revisar' })}
            className="inline-flex items-center rounded-xl border border-stone-300 bg-white px-4 py-2.5 font-semibold hover:bg-stone-100"
          >
            Revisar erros
          </a>
        )}
      </div>
      {!usuario && (
        <p className="text-sm text-stone-500">
          <a href={endereco({ pagina: 'criar-conta' })} className="font-semibold text-stone-900 underline-offset-4 hover:underline">
            Crie uma conta
          </a>{' '}
          para guardar este resultado e montar a lista de revisão.
        </p>
      )}
    </Pagina>
  )
}

export function PaginaFoco() {
  const [foco, setFoco] = useState(lerFoco)
  const salvar = (novo: EstadoDoFoco | null) => {
    gravarFoco(novo)
    setFoco(novo)
  }

  if (!foco) return <Configurar aoComecar={() => setFoco(lerFoco())} />
  if (foco.fim !== null || foco.indice >= foco.ids.length) return <Resumo foco={foco} aoRecomecar={() => salvar(null)} />
  return <EmAndamento foco={foco} salvar={salvar} />
}
