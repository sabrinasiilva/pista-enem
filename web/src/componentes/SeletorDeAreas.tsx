import { Check } from 'lucide-react'
import { AREAS, MATERIAS } from '../areas'

/** Escolha das áreas de foco (competências da matriz do ENEM). */
export function SeletorDeAreas({
  selecionadas,
  aoMudar,
}: {
  selecionadas: string[]
  aoMudar: (competencias: string[]) => void
}) {
  const alternar = (competencia: string) =>
    aoMudar(
      selecionadas.includes(competencia)
        ? selecionadas.filter((c) => c !== competencia)
        : [...selecionadas, competencia],
    )

  return (
    <div className="space-y-5">
      {MATERIAS.map((materia) => (
    <fieldset key={materia.id}>
      <legend className="mb-2 text-sm font-semibold text-stone-700">{materia.nome}</legend>
      <div className="grid gap-2 sm:grid-cols-2">
        {AREAS.filter((area) => area.materia === materia.id).map((area) => {
          const marcada = selecionadas.includes(area.competencia)
          return (
            <label
              key={area.competencia}
              className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition ${
                marcada ? 'border-amber-500 bg-amber-50 ring-1 ring-amber-500' : 'border-stone-200 bg-white hover:border-stone-400'
              }`}
            >
              <input
                type="checkbox"
                className="sr-only"
                checked={marcada}
                onChange={() => alternar(area.competencia)}
              />
              <span
                aria-hidden
                className={`mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-md border ${
                  marcada ? 'border-amber-500 bg-amber-500 text-white' : 'border-stone-300'
                }`}
              >
                {marcada && <Check className="size-3.5" />}
              </span>
              <span>
                <span className="block font-medium">{area.nome}</span>
                <span className="block text-sm text-stone-500">{area.descricao}</span>
              </span>
            </label>
          )
        })}
      </div>
    </fieldset>
      ))}
    </div>
  )
}
