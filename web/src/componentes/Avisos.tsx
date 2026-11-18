import { AlertTriangle, Loader2, RotateCw } from 'lucide-react'
import { useEffect, useState } from 'react'

/** Depois deste tempo, avisa que o servidor gratuito pode estar acordando. */
export const ESPERA_ANTES_DO_AVISO = 4000

export function Carregando({ texto = 'Carregando…' }: { texto?: string }) {
  const [demorando, setDemorando] = useState(false)
  useEffect(() => {
    const relogio = setTimeout(() => setDemorando(true), ESPERA_ANTES_DO_AVISO)
    return () => clearTimeout(relogio)
  }, [])

  return (
    <div role="status" className="flex flex-col items-center justify-center gap-2 px-4 py-16 text-center text-stone-500">
      <span className="inline-flex items-center gap-2">
        <Loader2 className="size-5 animate-spin" aria-hidden />
        <span>{texto}</span>
      </span>
      {demorando && (
        <span className="max-w-sm text-sm">
          O servidor gratuito dorme quando ninguém usa e leva até 1 minuto para acordar. Já já carrega.
        </span>
      )}
    </div>
  )
}

export function CaixaDeErro({ mensagem, aoTentarDeNovo }: { mensagem: string; aoTentarDeNovo?: () => void }) {
  return (
    <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-900">
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 size-5 shrink-0" aria-hidden />
        <p>{mensagem}</p>
      </div>
      {aoTentarDeNovo && (
        <button
          type="button"
          onClick={aoTentarDeNovo}
          className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-red-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-800"
        >
          <RotateCw className="size-4" aria-hidden />
          Tentar de novo
        </button>
      )}
    </div>
  )
}

export function AvisoModoBasico({ compacto = false }: { compacto?: boolean }) {
  if (compacto) {
    return (
      <p className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-900">
        <span className="size-1.5 rounded-full bg-amber-500" aria-hidden />
        Modo básico: pistas prontas, sem conversa com a IA
      </p>
    )
  }
  return (
    <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      O tutor está no modo básico agora: as pistas são prontas, sem conversa com a IA. Dá para resolver as questões
      normalmente.
    </p>
  )
}
