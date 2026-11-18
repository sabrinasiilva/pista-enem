import type { Estado } from '../tipos'

const ETAPAS: { estado: Estado; rotulo: string }[] = [
  { estado: 'respondendo', rotulo: 'Tentativa' },
  { estado: 'pista_1', rotulo: 'Pista 1' },
  { estado: 'pista_2', rotulo: 'Pista 2' },
  { estado: 'explicacao', rotulo: 'Explicação' },
]

export const DESCRICAO_DO_ESTADO: Record<Estado, string> = {
  respondendo: 'Marque a alternativa que achar certa.',
  pista_1: 'Pista 1 de 2: o tutor fez uma pergunta para você achar o erro. Tente de novo.',
  pista_2: 'Pista 2 de 2: agora com uma dica mais direta. Tente mais uma vez.',
  explicacao: 'Explicação completa liberada.',
  concluida: 'Você acertou!',
}

export function Progresso({ estado }: { estado: Estado }) {
  const atual = estado === 'concluida' ? -1 : ETAPAS.findIndex((etapa) => etapa.estado === estado)
  return (
    <div>
      <ol className="flex gap-1.5" aria-label="Etapas da questão">
        {ETAPAS.map((etapa, indice) => {
          const feita = atual > indice
          const agora = atual === indice
          return (
            <li
              key={etapa.estado}
              aria-current={agora ? 'step' : undefined}
              className={`flex-1 rounded-full py-1 text-center text-xs font-medium ${
                agora
                  ? 'bg-amber-500 text-white'
                  : feita
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-stone-100 text-stone-400'
              } ${estado === 'concluida' ? '!bg-emerald-100 !text-emerald-800' : ''}`}
            >
              {etapa.rotulo}
            </li>
          )
        })}
      </ol>
      <p className="mt-2 text-sm text-stone-600" aria-live="polite">
        {DESCRICAO_DO_ESTADO[estado]}
      </p>
    </div>
  )
}
