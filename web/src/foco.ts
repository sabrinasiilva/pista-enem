// Estado do modo foco, guardado na aba. Fica separado da página para que outras telas
// (como a de revisão) possam começar um foco sem carregar o KaTeX e o Markdown.
import { daAba } from './armazenamento'
import type { Estado } from './tipos'

const CHAVE = 'pista:foco'

export interface ResultadoNoFoco {
  estado: Estado
  tentativas: number
}

export interface EstadoDoFoco {
  ids: string[]
  indice: number
  inicio: number
  fim: number | null
  minutos: number | null
  resultados: Record<string, ResultadoNoFoco>
}

export function lerFoco(): EstadoDoFoco | null {
  try {
    return JSON.parse(daAba.ler(CHAVE) ?? 'null')
  } catch {
    return null
  }
}

export function gravarFoco(foco: EstadoDoFoco | null) {
  if (foco) daAba.gravar(CHAVE, JSON.stringify(foco))
  else daAba.apagar(CHAVE)
}

/** Começa um foco com estas questões. */
export function iniciarFoco({ ids, minutos }: { ids: string[]; minutos: number | null }) {
  gravarFoco({ ids, indice: 0, inicio: Date.now(), fim: null, minutos, resultados: {} })
}
