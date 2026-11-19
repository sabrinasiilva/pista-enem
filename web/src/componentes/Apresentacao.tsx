import { ArrowRight, Check, Flame, Lightbulb, RotateCcw, ShieldCheck, Target, X } from 'lucide-react'
import { type KeyboardEvent, type PointerEvent, type ReactNode, useEffect, useRef, useState } from 'react'
import { local } from '../armazenamento'

const CHAVE = 'pista:apresentacao'

/** A apresentação aparece uma vez só, na primeira visita. */
export const apresentacaoJaVista = () => local.ler(CHAVE) !== null
export const marcarApresentacaoComoVista = () => local.gravar(CHAVE, 'vista')
export const reverApresentacao = () => local.apagar(CHAVE)

type Tela = { titulo: string; texto: string; ilustracao: ReactNode }

const TELAS: Tela[] = [
  {
    titulo: 'Aprenda a resolver, não a decorar',
    texto:
      'O Pista é um tutor para as questões do ENEM. Em vez de entregar a resposta, ele faz as perguntas certas para você chegar lá por conta própria.',
    ilustracao: <BoasVindas />,
  },
  {
    titulo: 'Errou? É aí que a mágica acontece',
    texto:
      'Cada alternativa errada tem um engano por trás. O tutor descobre qual foi o seu e te dá uma pista sobre ele. São até duas pistas antes da explicação completa.',
    ilustracao: <ComoFunciona />,
  },
  {
    titulo: 'Questões oficiais, do jeito que caem',
    texto:
      'Provas de 2022 a 2025, de Matemática e Ciências da Natureza, com a habilidade do Inep que cada questão cobra.',
    ilustracao: <Questoes />,
  },
  {
    titulo: 'No seu ritmo, sem dados pessoais',
    texto:
      'Pratique no modo foco, revise o que errou e acompanhe sua sequência de dias. A conta é opcional e só pede um apelido.',
    ilustracao: <SeuRitmo />,
  },
]

export function Apresentacao({ aoTerminar }: { aoTerminar: (destino?: string) => void }) {
  const [atual, setAtual] = useState(0)
  const inicioDoArraste = useRef<number | null>(null)
  const principal = useRef<HTMLButtonElement>(null)
  const ultima = atual === TELAS.length - 1
  const [abrindo, setAbrindo] = useState(true)

  useEffect(() => {
    if (!abrindo) return
    const poucoMovimento = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    const espera = setTimeout(() => setAbrindo(false), poucoMovimento ? 700 : DURACAO_DA_ABERTURA)
    return () => clearTimeout(espera)
  }, [abrindo])
  useEffect(() => {
    if (!abrindo) principal.current?.focus()
  }, [abrindo])

  const terminar = (destino?: string) => {
    marcarApresentacaoComoVista()
    aoTerminar(destino)
  }
  const irPara = (indice: number) => setAtual(Math.max(0, Math.min(TELAS.length - 1, indice)))
  const avancar = () => (ultima ? terminar() : irPara(atual + 1))

  const teclas = (evento: KeyboardEvent) => {
    if (evento.key === 'ArrowRight') irPara(atual + 1)
    else if (evento.key === 'ArrowLeft') irPara(atual - 1)
    else if (evento.key === 'Escape') terminar()
  }
  const comecarArraste = (evento: PointerEvent) => {
    inicioDoArraste.current = evento.clientX
  }
  const terminarArraste = (evento: PointerEvent) => {
    if (inicioDoArraste.current === null) return
    const distancia = evento.clientX - inicioDoArraste.current
    inicioDoArraste.current = null
    if (Math.abs(distancia) > 50) irPara(atual + (distancia < 0 ? 1 : -1))
  }

  if (abrindo) return <Abertura aoTocar={() => setAbrindo(false)} />

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={`apresentacao-titulo-${atual}`}
      aria-roledescription="apresentação"
      onKeyDown={teclas}
      className="fixed inset-0 z-50 flex flex-col overflow-y-auto bg-stone-50 motion-safe:animate-[aparecer_0.4s_ease-out]"
    >
      <div className="mx-auto flex w-full max-w-md flex-1 flex-col px-5 pt-[max(1rem,env(safe-area-inset-top))] pb-[max(1.25rem,env(safe-area-inset-bottom))]">
        <div className="flex items-center gap-3">
          <div className="flex flex-1 gap-1.5" aria-hidden>
            {TELAS.map((tela, indice) => (
              <span key={tela.titulo} className="h-1 flex-1 overflow-hidden rounded-full bg-stone-200">
                <span
                  className={`block h-full rounded-full bg-amber-500 transition-[width] duration-500 ease-out motion-reduce:transition-none ${
                    indice <= atual ? 'w-full' : 'w-0'
                  }`}
                />
              </span>
            ))}
          </div>
          {!ultima && (
            <button
              type="button"
              onClick={() => terminar()}
              className="rounded-lg px-2 py-1 text-sm font-medium text-stone-600 hover:text-stone-900"
            >
              Pular
            </button>
          )}
        </div>
        <p className="sr-only" aria-live="polite">
          Tela {atual + 1} de {TELAS.length}
        </p>

        <div
          className="relative -mx-5 flex-1 touch-pan-y overflow-hidden"
          onPointerDown={comecarArraste}
          onPointerUp={terminarArraste}
          onPointerCancel={() => (inicioDoArraste.current = null)}
        >
          <div
            className="flex h-full transition-transform duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] motion-reduce:transition-none"
            style={{ transform: `translateX(-${atual * 100}%)` }}
          >
            {TELAS.map((tela, indice) => (
              <section
                key={tela.titulo}
                aria-hidden={indice !== atual}
                inert={indice !== atual}
                className="flex w-full shrink-0 flex-col px-5"
              >
                <div className="relative mt-6 flex min-h-64 flex-1 items-center justify-center overflow-hidden rounded-[2rem] bg-gradient-to-br from-amber-100 via-amber-50 to-stone-100 p-6">
                  <div className="pointer-events-none absolute -top-16 -right-16 size-48 rounded-full bg-amber-200/60" />
                  <div className="pointer-events-none absolute -bottom-20 -left-10 size-44 rounded-full bg-white/70" />
                  <div className="relative w-full">{tela.ilustracao}</div>
                </div>
                <h2
                  id={`apresentacao-titulo-${indice}`}
                  className="mt-8 text-[1.75rem] leading-tight font-extrabold tracking-tight text-balance text-stone-900"
                >
                  {tela.titulo}
                </h2>
                <p className="mt-3 text-base leading-relaxed text-pretty text-stone-600">{tela.texto}</p>
              </section>
            ))}
          </div>
        </div>

        <div className="mt-8 space-y-3">
          <button
            ref={principal}
            type="button"
            onClick={avancar}
            className="flex w-full items-center justify-center gap-2 rounded-2xl bg-stone-900 px-6 py-4 text-base font-semibold text-white shadow-lg shadow-stone-900/10 transition hover:bg-stone-800 active:scale-[0.98] motion-reduce:active:scale-100"
          >
            {ultima ? 'Começar a praticar' : 'Continuar'}
            <ArrowRight className="size-5" aria-hidden />
          </button>
          {ultima ? (
            <button
              type="button"
              onClick={() => terminar('#/criar-conta')}
              className="w-full rounded-2xl px-6 py-3 text-sm font-semibold text-stone-700 hover:bg-stone-100"
            >
              Criar uma conta (opcional)
            </button>
          ) : (
            <button
              type="button"
              onClick={() => irPara(atual - 1)}
              disabled={atual === 0}
              className="w-full rounded-2xl px-6 py-3 text-sm font-semibold text-stone-700 hover:bg-stone-100 disabled:invisible"
            >
              Voltar
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ abertura */

export const DURACAO_DA_ABERTURA = 1800

/** Tela de abertura: a marca entra animada e some sozinha (ou com um toque). */
function Abertura({ aoTocar }: { aoTocar: () => void }) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Pista, tutor para o ENEM"
      onClick={aoTocar}
      onKeyDown={aoTocar}
      tabIndex={-1}
      // cores fixas: a abertura é escura nos dois temas
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#1c1917] text-[#fafaf9]"
    >
      <div className="pointer-events-none absolute size-[28rem] rounded-full bg-[radial-gradient(circle,rgba(245,158,11,0.22),transparent_65%)] motion-safe:animate-[pulsar_1.8s_ease-out_both]" />
      <p className="relative text-7xl font-black tracking-tighter motion-safe:animate-[surgir_0.7s_cubic-bezier(0.22,1,0.36,1)_both]">
        pista
        <span className="inline-block text-[#f59e0b] motion-safe:animate-[pingar_0.6s_cubic-bezier(0.34,1.56,0.64,1)_0.45s_both]">
          .
        </span>
      </p>
      <p className="relative mt-3 text-sm font-medium tracking-wide text-[#d6d3d1] motion-safe:animate-[surgir_0.7s_ease-out_0.7s_both]">
        Seu tutor para o ENEM
      </p>
    </div>
  )
}

/* ------------------------------------------------------------------ ilustrações */
// Montadas com os próprios elementos da interface, para mostrar o app de verdade.

function Etiqueta({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-stone-800 shadow-md shadow-stone-900/5 ${className}`}
    >
      {children}
    </span>
  )
}

function BoasVindas() {
  return (
    <div className="flex flex-col items-center py-6">
      <Etiqueta className="motion-safe:animate-[flutuar_6s_ease-in-out_infinite] -rotate-3 self-start">
        <Lightbulb className="size-3.5 text-amber-600" aria-hidden />
        Pista 1 de 2
      </Etiqueta>
      <p className="my-5 text-6xl font-black tracking-tighter text-stone-900">
        pista<span className="text-amber-500">.</span>
      </p>
      <div className="flex w-full justify-between">
        <Etiqueta className="motion-safe:animate-[flutuar_7s_ease-in-out_infinite_1s] rotate-2">MT-H16</Etiqueta>
        <Etiqueta className="motion-safe:animate-[flutuar_5s_ease-in-out_infinite_0.5s] -rotate-2 text-emerald-700">
          <Check className="size-3.5" aria-hidden />
          Você acertou!
        </Etiqueta>
      </div>
    </div>
  )
}

function ComoFunciona() {
  return (
    <div className="space-y-3">
      <div className="rounded-2xl bg-white p-4 shadow-lg shadow-stone-900/5">
        <p className="text-xs font-semibold text-stone-500">Questão de exemplo</p>
        <p className="mt-1 text-sm font-medium text-stone-800">Quanto ele recebe em um dia?</p>
        <div className="mt-3 space-y-1.5 text-sm">
          <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-2.5 py-1.5 text-stone-600">
            <X className="size-3.5 text-red-500" aria-hidden />
            <span className="line-through decoration-red-300">B) R$ 128,00</span>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-stone-200 px-2.5 py-1.5 text-stone-700">
            <span className="flex size-3.5 items-center justify-center text-[10px] font-bold">C</span>
            R$ 960,00
          </div>
        </div>
      </div>
      <div className="ml-6 flex gap-2 rounded-2xl rounded-tl-md bg-stone-900 p-3.5 text-sm text-white shadow-lg motion-safe:animate-[surgir_0.6s_ease-out_both]">
        <Lightbulb className="mt-0.5 size-4 shrink-0 text-amber-300" aria-hidden />
        <p>Você somou o preço e as horas. Se ele trabalha 8 horas, quantas vezes recebe os R$ 120?</p>
      </div>
    </div>
  )
}

function Questoes() {
  const numeros = [
    ['179', 'questões oficiais'],
    ['4', 'anos de prova'],
    ['2', 'áreas do ENEM'],
    ['0', 'respostas entregues de bandeja'],
  ]
  return (
    <div className="grid grid-cols-2 gap-3">
      {numeros.map(([valor, rotulo], indice) => (
        <div
          key={rotulo}
          className={`rounded-2xl bg-white p-4 shadow-lg shadow-stone-900/5 ${indice % 2 ? 'translate-y-4' : ''}`}
        >
          <p className="text-3xl font-black tracking-tight text-stone-900">{valor}</p>
          <p className="mt-1 text-xs font-medium text-stone-600">{rotulo}</p>
        </div>
      ))}
    </div>
  )
}

function SeuRitmo() {
  const itens = [
    { icone: Target, titulo: 'Modo foco', detalhe: 'questões das suas áreas, em sequência' },
    { icone: RotateCcw, titulo: 'Revisar erros', detalhe: 'as que você errou, de novo' },
    { icone: Flame, titulo: 'Meu progresso', detalhe: 'meta da semana e dias seguidos' },
  ]
  return (
    <div className="space-y-2.5">
      {itens.map(({ icone: Icone, titulo, detalhe }) => (
        <div key={titulo} className="flex items-center gap-3 rounded-2xl bg-white p-3 shadow-lg shadow-stone-900/5">
          <span className="flex size-10 items-center justify-center rounded-xl bg-amber-100">
            <Icone className="size-5 text-amber-700" aria-hidden />
          </span>
          <span>
            <span className="block text-sm font-semibold text-stone-900">{titulo}</span>
            <span className="block text-xs text-stone-600">{detalhe}</span>
          </span>
        </div>
      ))}
      <p className="flex items-center justify-center gap-1.5 pt-1 text-xs font-medium text-stone-700">
        <ShieldCheck className="size-4 text-emerald-600" aria-hidden />
        Sem nome, sem e-mail
      </p>
    </div>
  )
}
