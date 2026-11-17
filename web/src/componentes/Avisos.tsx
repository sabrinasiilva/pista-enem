import { AlertTriangle, Loader2, RotateCw } from 'lucide-react'

export function Carregando({ texto = 'Carregando…' }: { texto?: string }) {
  return (
    <div role="status" className="flex items-center justify-center gap-2 py-16 text-stone-500">
      <Loader2 className="size-5 animate-spin" aria-hidden />
      <span>{texto}</span>
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

export function AvisoModoBasico() {
  return (
    <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      O tutor está no modo básico agora: as pistas são prontas, sem conversa com a IA. Dá para resolver as questões
      normalmente.
    </p>
  )
}
