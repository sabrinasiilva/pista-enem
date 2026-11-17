import { Check, X } from 'lucide-react'
import type { Letra, Questao } from '../tipos'
import { TextoRico } from './TextoRico'

interface Props {
  alternativas: Questao['alternativas']
  tentativas: Letra[]
  gabarito: Letra | null
  selecionada: Letra | null
  bloqueadas: boolean
  aoSelecionar: (letra: Letra) => void
}

export function Alternativas({ alternativas, tentativas, gabarito, selecionada, bloqueadas, aoSelecionar }: Props) {
  return (
    <fieldset className="space-y-2">
      <legend className="sr-only">Alternativas</legend>
      {alternativas.map(({ letra, texto }) => {
        const tentada = tentativas.includes(letra)
        const correta = gabarito === letra
        const marcada = selecionada === letra
        const desativada = bloqueadas || tentada || gabarito !== null

        let estilo = 'border-stone-200 bg-white hover:border-stone-400'
        if (marcada) estilo = 'border-stone-900 bg-stone-50 ring-1 ring-stone-900'
        if (tentada && !correta) estilo = 'border-red-200 bg-red-50 text-stone-500'
        if (correta) estilo = 'border-emerald-500 bg-emerald-50 ring-1 ring-emerald-500'

        return (
          <label
            key={letra}
            className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition-colors has-disabled:cursor-default ${estilo}`}
          >
            <input
              type="radio"
              name="alternativa"
              value={letra}
              checked={marcada}
              disabled={desativada}
              onChange={() => aoSelecionar(letra)}
              className="sr-only"
              aria-describedby={tentada && !correta ? `tentada-${letra}` : undefined}
            />
            <span
              className={`flex size-7 shrink-0 items-center justify-center rounded-full border text-sm font-semibold ${
                marcada ? 'border-stone-900 bg-stone-900 text-white' : 'border-stone-300'
              }`}
              aria-hidden
            >
              {correta ? <Check className="size-4 text-emerald-600" /> : tentada ? <X className="size-4 text-red-500" /> : letra}
            </span>
            <span className={`flex-1 pt-0.5 ${tentada && !correta ? 'line-through decoration-red-300' : ''}`}>
              <span className="sr-only">{letra}) </span>
              <TextoRico texto={texto} className="inline-block" />
            </span>
            {tentada && !correta && (
              <span id={`tentada-${letra}`} className="sr-only">
                você já tentou esta
              </span>
            )}
            {correta && <span className="sr-only">(alternativa correta)</span>}
          </label>
        )
      })}
    </fieldset>
  )
}
