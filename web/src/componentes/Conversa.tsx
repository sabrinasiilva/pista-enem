import { Send } from 'lucide-react'
import { type FormEvent, useEffect, useRef, useState } from 'react'
import type { Mensagem } from '../tipos'
import { TextoRico } from './TextoRico'

const LIMITE = 1000

interface Props {
  mensagens: Mensagem[]
  emAndamento: { aluno: string; tutor: string } | null
  ocupado: boolean
  aoEnviar: (texto: string) => void
}

export function Conversa({ mensagens, emAndamento, ocupado, aoEnviar }: Props) {
  const [texto, setTexto] = useState('')
  const fim = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fim.current?.scrollIntoView?.({ behavior: 'smooth', block: 'nearest' })
  }, [mensagens.length, emAndamento?.tutor])

  const enviar = (evento: FormEvent) => {
    evento.preventDefault()
    const limpo = texto.trim()
    if (!limpo || ocupado) return
    aoEnviar(limpo)
    setTexto('')
  }

  return (
    <section aria-labelledby="titulo-conversa" className="rounded-2xl border border-stone-200 bg-white shadow-sm">
      <h2 id="titulo-conversa" className="border-b border-stone-200 px-4 py-3 font-semibold">
        Conversa com o tutor
      </h2>
      <div
        className="max-h-[28rem] min-h-32 space-y-3 overflow-y-auto px-4 py-4 lg:max-h-[calc(100vh-17rem)]"
        aria-live="polite"
      >
        {mensagens.length === 0 && !emAndamento && (
          <p className="text-sm text-stone-500">
            Travou antes de responder? Pergunte aqui. O tutor ajuda sem entregar a resposta.
          </p>
        )}
        {mensagens.map((mensagem, indice) => (
          // as mensagens só são acrescentadas no fim, então o índice é uma chave estável
          <Balao key={indice} papel={mensagem.papel} texto={mensagem.texto} />
        ))}
        {emAndamento && (
          <>
            <Balao papel="aluno" texto={emAndamento.aluno} />
            <Balao papel="tutor" texto={emAndamento.tutor || '…'} digitando={!emAndamento.tutor} />
          </>
        )}
        <div ref={fim} />
      </div>
      <form onSubmit={enviar} className="border-t border-stone-200 p-3">
        <label htmlFor="mensagem" className="sr-only">
          Sua mensagem para o tutor
        </label>
        <div className="flex items-end gap-2">
          <textarea
            id="mensagem"
            value={texto}
            onChange={(evento) => setTexto(evento.target.value)}
            onKeyDown={(evento) => {
              if (evento.key === 'Enter' && !evento.shiftKey) enviar(evento)
            }}
            maxLength={LIMITE}
            rows={2}
            placeholder="Escreva sua dúvida…"
            className="min-h-11 flex-1 resize-none rounded-xl border border-stone-300 px-3 py-2 focus:border-stone-900 focus:outline-none"
          />
          <button
            type="submit"
            disabled={ocupado || !texto.trim()}
            aria-label="Enviar mensagem"
            className="flex size-11 items-center justify-center rounded-xl bg-stone-900 text-white hover:bg-stone-800 disabled:opacity-40"
          >
            <Send className="size-5" aria-hidden />
          </button>
        </div>
        <p className="mt-2 text-xs text-stone-500">
          Não escreva dados pessoais (nome, telefone, escola). As mensagens são processadas por uma IA do Google.
        </p>
      </form>
    </section>
  )
}

function Balao({ papel, texto, digitando = false }: { papel: Mensagem['papel']; texto: string; digitando?: boolean }) {
  const doAluno = papel === 'aluno'
  return (
    <div className={`flex ${doAluno ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
          doAluno ? 'rounded-br-md bg-stone-900 text-white' : 'rounded-bl-md bg-stone-100 text-stone-900'
        } ${digitando ? 'animate-pulse' : ''}`}
      >
        <span className="sr-only">{doAluno ? 'Você: ' : 'Tutor: '}</span>
        {doAluno ? <p className="whitespace-pre-wrap">{texto}</p> : <TextoRico texto={texto} />}
      </div>
    </div>
  )
}
