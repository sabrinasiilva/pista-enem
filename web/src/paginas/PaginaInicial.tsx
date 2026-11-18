import {
  ArrowRight,
  Flame,
  Lightbulb,
  MessageCircleQuestion,
  MousePointerClick,
  RotateCcw,
  Shuffle,
  Target,
  X,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { api, ErroDaApi } from '../api'
import { MATERIAS, type Materia } from '../areas'
import { AvisoModoBasico, CaixaDeErro, Carregando } from '../componentes/Avisos'
import { BarraDeProgresso } from '../componentes/ui'
import { useConta } from '../conta'
import { endereco, irPara } from '../rotas'
import type { Progresso, QuestaoResumo, Saude, Usuario } from '../tipos'

const PASSOS = [
  { icone: MousePointerClick, titulo: 'Tente', texto: 'Escolha uma questão oficial do ENEM e marque a alternativa que achar certa.' },
  { icone: MessageCircleQuestion, titulo: 'Repense', texto: 'Errou? O tutor faz uma pergunta que leva você a achar o próprio erro.' },
  { icone: Lightbulb, titulo: 'Entenda', texto: 'Se travar de novo, vem uma dica. A resolução completa só aparece se você pedir.' },
]

const rolarParaQuestoes = () => document.getElementById('questoes')?.scrollIntoView?.({ behavior: 'smooth' })

export function PaginaInicial() {
  const { usuario } = useConta()
  const [questoes, setQuestoes] = useState<QuestaoResumo[] | null>(null)
  const [saude, setSaude] = useState<Saude | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [ano, setAno] = useState<number | null>(null)
  const [materia, setMateria] = useState<Materia | null>(null)

  const carregar = useCallback(async () => {
    setErro(null)
    try {
      const [lista, estado] = await Promise.all([api.listarQuestoes(), api.saude()])
      setQuestoes(lista)
      setSaude(estado)
    } catch (e) {
      setErro(e instanceof ErroDaApi ? e.message : 'Não consegui carregar as questões.')
    }
  }, [])

  useEffect(() => {
    void carregar()
  }, [carregar])

  const sortear = () => {
    if (!questoes?.length) return
    irPara({ pagina: 'questao', id: questoes[Math.floor(Math.random() * questoes.length)].id })
  }

  const materias = MATERIAS.filter((m) => (questoes ?? []).some((q) => q.area === m.id))
  const materiaAtual = materias.find((m) => m.id === materia) ?? materias[0]
  const daMateria = (questoes ?? []).filter((q) => q.area === materiaAtual?.id)
  const anos = [...new Set(daMateria.map((q) => q.ano))].sort((a, b) => b - a)
  const anoAtual = ano !== null && anos.includes(ano) ? ano : anos[0]
  const doAno = daMateria.filter((q) => q.ano === anoAtual)

  return (
    <main>
      {usuario ? (
        <PainelDoAluno usuario={usuario} aoSortear={sortear} />
      ) : (
        <>
      <section className="border-b border-stone-200 bg-white">
        <div className="mx-auto grid max-w-5xl items-center gap-10 px-4 py-10 sm:py-16 lg:grid-cols-[1.1fr_1fr]">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-amber-600">
              Matemática e Ciências da Natureza do ENEM
            </p>
            <h1 className="mt-3 text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
              Aprenda com o seu erro, não com o gabarito.
            </h1>
            <p className="mt-5 text-lg text-stone-600">
              O Pista é um tutor que não entrega a resposta. Quando você erra, ele faz perguntas e dá pistas até você
              encontrar o caminho sozinho.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <button
                type="button"
                onClick={sortear}
                disabled={!questoes?.length}
                className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-5 py-3 font-semibold text-white shadow-sm transition hover:bg-stone-700 disabled:opacity-50"
              >
                <Shuffle className="size-5" aria-hidden />
                Começar com uma questão aleatória
              </button>
              <button
                type="button"
                onClick={rolarParaQuestoes}
                className="text-sm font-medium text-stone-600 underline-offset-4 hover:underline"
              >
                ou escolha uma questão
              </button>
            </div>
          </div>
          <Demonstracao />
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 py-12" aria-labelledby="titulo-como-funciona">
        <h2 id="titulo-como-funciona" className="sr-only">
          Como funciona
        </h2>
        <ol className="grid gap-4 sm:grid-cols-3">
          {PASSOS.map(({ icone: Icone, titulo, texto }, indice) => (
            <li key={titulo} className="rounded-2xl border border-stone-200 bg-white p-5">
              <div className="flex items-center gap-3">
                <span className="flex size-9 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
                  <Icone className="size-5" aria-hidden />
                </span>
                <span className="text-sm font-semibold text-stone-400">{indice + 1}</span>
              </div>
              <h3 className="mt-4 font-semibold">{titulo}</h3>
              <p className="mt-1 text-sm text-stone-600">{texto}</p>
            </li>
          ))}
        </ol>
      </section>

        </>
      )}

      <section id="questoes" className="mx-auto max-w-5xl scroll-mt-4 px-4 pb-16" aria-labelledby="titulo-questoes">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 id="titulo-questoes" className="text-2xl font-bold tracking-tight">
              Questões
            </h2>
            <p className="mt-1 text-sm text-stone-500">Provas oficiais do Inep, sem questões com figura por enquanto.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
          {materias.length > 1 && (
            <div role="tablist" aria-label="Matéria" className="inline-flex rounded-xl bg-stone-200/70 p-1">
              {materias.map((cada) => (
                <button
                  key={cada.id}
                  type="button"
                  role="tab"
                  aria-selected={cada.id === materiaAtual?.id}
                  onClick={() => setMateria(cada.id)}
                  className={`rounded-lg px-4 py-1.5 text-sm font-medium transition ${
                    cada.id === materiaAtual?.id ? 'bg-white text-stone-900 shadow-sm' : 'text-stone-600 hover:text-stone-900'
                  }`}
                >
                  {cada.nomeCurto}
                </button>
              ))}
            </div>
          )}
          {anos.length > 0 && (
            <div role="tablist" aria-label="Ano da prova" className="inline-flex rounded-xl bg-stone-200/70 p-1">
              {anos.map((cada) => (
                <button
                  key={cada}
                  type="button"
                  role="tab"
                  aria-selected={cada === anoAtual}
                  onClick={() => setAno(cada)}
                  className={`rounded-lg px-4 py-1.5 text-sm font-medium transition ${
                    cada === anoAtual ? 'bg-white text-stone-900 shadow-sm' : 'text-stone-600 hover:text-stone-900'
                  }`}
                >
                  {cada}
                </button>
              ))}
            </div>
          )}
          </div>
        </div>

        <div className="mt-6 space-y-4">
          {saude && saude.ia !== 'gemini' && <AvisoModoBasico />}
          {erro && <CaixaDeErro mensagem={erro} aoTentarDeNovo={carregar} />}
          {!erro && !questoes && <Carregando texto="Carregando as questões…" />}
        </div>

        {doAno.length > 0 && (
          <ul
            role="tabpanel"
            aria-label={`Questões de ${materiaAtual?.nome} do ENEM ${anoAtual}`}
            className="mt-2 grid gap-3 sm:grid-cols-2"
          >
            {doAno.map((questao) => (
              <li key={questao.id}>
                <a
                  href={`#/questao/${questao.id}`}
                  aria-label={`Questão ${questao.numero} do ENEM ${questao.ano}, ${materiaAtual?.nome}`}
                  className="group flex h-full flex-col rounded-2xl border border-stone-200 bg-white p-4 transition hover:-translate-y-0.5 hover:border-stone-300 hover:shadow-md"
                >
                  <span className="flex items-center justify-between">
                    <span className="font-semibold">Questão {questao.numero}</span>
                    <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs font-medium text-stone-500">
                      {questao.habilidade}
                    </span>
                  </span>
                  <span className="mt-2 line-clamp-2 flex-1 text-sm text-stone-600">{questao.inicio_do_enunciado}</span>
                  <span className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-stone-900">
                    Resolver
                    <ArrowRight className="size-4 transition group-hover:translate-x-0.5" aria-hidden />
                  </span>
                </a>
              </li>
            ))}
          </ul>
        )}
      </section>

      <footer className="border-t border-stone-200 bg-white">
        <div className="mx-auto max-w-5xl px-4 py-6 text-sm text-stone-500">
          Questões oficiais do ENEM, publicadas pelo Inep. Projeto de código aberto:{' '}
          <a href="https://github.com/sabrinasiilva/pista-enem" className="underline" target="_blank" rel="noreferrer">
            github.com/sabrinasiilva/pista-enem
          </a>
          .
        </div>
      </footer>
    </main>
  )
}

/** Exemplo estático de como uma pista aparece: mostra a ideia antes de o aluno começar. */
function Demonstracao() {
  return (
    <figure aria-label="Exemplo de como o tutor responde a um erro" className="relative">
      <div className="rounded-3xl border border-stone-200 bg-stone-50 p-5 shadow-sm">
        <p className="text-xs font-semibold text-stone-500">ENEM 2022 · Questão 141</p>
        <p className="mt-2 text-sm text-stone-700">
          Cada docinho tinha 2 cm de diâmetro e agora terá 4 cm. Quantas porções de massa ela deve preparar?
        </p>
        <div className="mt-4 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-stone-500">
          <span className="flex size-6 items-center justify-center rounded-full border border-red-200 bg-white">
            <X className="size-3.5 text-red-500" aria-hidden />
          </span>
          <span className="line-through decoration-red-300">D) 12</span>
        </div>
        <div className="mt-3 flex gap-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm">
          <Lightbulb className="mt-0.5 size-4 shrink-0 text-amber-600" aria-hidden />
          <p>
            Quando o diâmetro dobra, a massa de cada docinho ocupa uma <strong>área</strong> ou um{' '}
            <strong>volume</strong>? Isso muda quantas vezes ela cresce?
          </p>
        </div>
      </div>
      <figcaption className="mt-3 text-center text-xs text-stone-500">
        A pista responde ao erro específico da alternativa marcada.
      </figcaption>
    </figure>
  )
}

function PainelDoAluno({ usuario, aoSortear }: { usuario: Usuario; aoSortear: () => void }) {
  const [progresso, setProgresso] = useState<Progresso | null>(null)
  useEffect(() => {
    api.progresso().then(setProgresso).catch(() => {})
  }, [])

  const faltam = progresso ? Math.max(0, progresso.meta_semanal - progresso.feitas_na_semana) : null
  return (
    <section className="border-b border-stone-200 bg-white">
      <div className="mx-auto max-w-5xl px-4 py-10">
        <h1 className="text-3xl font-bold tracking-tight">Oi, {usuario.apelido}!</h1>
        <p className="mt-2 text-stone-600">
          {faltam === null
            ? 'Bom te ver de volta.'
            : faltam === 0
              ? 'Meta da semana cumprida. O que vier agora é bônus.'
              : `Faltam ${faltam} questões para a meta da semana.`}
        </p>
        <div className="mt-6 grid gap-4 md:grid-cols-[1.4fr_1fr]">
          <div className="rounded-2xl border border-stone-200 bg-stone-50 p-5">
            <div className="flex items-baseline justify-between gap-3">
              <span className="font-semibold">Meta da semana</span>
              <span className="text-sm text-stone-500">
                {progresso ? `${progresso.feitas_na_semana} de ${progresso.meta_semanal}` : '…'}
              </span>
            </div>
            <div className="mt-3">
              <BarraDeProgresso
                valor={progresso?.feitas_na_semana ?? 0}
                maximo={progresso?.meta_semanal ?? usuario.meta_semanal}
                rotulo="Meta da semana"
              />
            </div>
            <p className="mt-4 inline-flex items-center gap-1.5 text-sm text-stone-600">
              <Flame className="size-4 text-amber-500" aria-hidden />
              {progresso?.sequencia_de_dias ?? 0} {progresso?.sequencia_de_dias === 1 ? 'dia seguido' : 'dias seguidos'}
            </p>
          </div>
          <div className="flex flex-col gap-3">
            <a
              href={endereco({ pagina: 'foco' })}
              className="flex flex-1 items-center gap-3 rounded-2xl bg-stone-900 p-4 font-semibold text-white transition hover:bg-stone-700"
            >
              <Target className="size-6 text-amber-400" aria-hidden />
              <span>
                Modo foco
                <span className="block text-sm font-normal opacity-80">Questões escolhidas para você, com tempo</span>
              </span>
            </a>
            <div className="grid grid-cols-2 gap-3">
              <a
                href={endereco({ pagina: 'revisar' })}
                className="flex items-center justify-center gap-2 rounded-2xl border border-stone-200 bg-white p-3 text-sm font-semibold hover:bg-stone-100"
              >
                <RotateCcw className="size-4" aria-hidden />
                Revisar erros
              </a>
              <button
                type="button"
                onClick={aoSortear}
                className="flex items-center justify-center gap-2 rounded-2xl border border-stone-200 bg-white p-3 text-sm font-semibold hover:bg-stone-100"
              >
                <Shuffle className="size-4" aria-hidden />
                Aleatória
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
