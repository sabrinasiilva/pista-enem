import { ArrowRight, Shuffle } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { api, ErroDaApi } from '../api'
import { AvisoModoBasico, CaixaDeErro, Carregando } from '../componentes/Avisos'
import { irPara } from '../rotas'
import type { QuestaoResumo, Saude } from '../tipos'

const PASSOS = [
  'Escolha uma questão oficial do ENEM.',
  'Marque a alternativa que achar certa.',
  'Errou? O tutor faz uma pergunta para você achar o erro. Depois, uma dica. A resposta só aparece se você pedir.',
]

export function PaginaInicial() {
  const [questoes, setQuestoes] = useState<QuestaoResumo[] | null>(null)
  const [saude, setSaude] = useState<Saude | null>(null)
  const [erro, setErro] = useState<string | null>(null)

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
    const questao = questoes[Math.floor(Math.random() * questoes.length)]
    irPara({ pagina: 'questao', id: questao.id })
  }

  const porAno = new Map<number, QuestaoResumo[]>()
  for (const questao of questoes ?? []) porAno.set(questao.ano, [...(porAno.get(questao.ano) ?? []), questao])

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 sm:py-12">
      <section>
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Aprenda com o seu erro, não com o gabarito.</h1>
        <p className="mt-4 text-lg text-stone-600">
          O Pista é um tutor de Matemática para o ENEM. Quando você erra, ele não entrega a resposta: faz perguntas e
          dá pistas até você encontrar o caminho.
        </p>
        <ol className="mt-6 space-y-3">
          {PASSOS.map((passo, indice) => (
            <li key={passo} className="flex gap-3">
              <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-stone-900 text-sm font-semibold text-white">
                {indice + 1}
              </span>
              <span className="pt-0.5 text-stone-700">{passo}</span>
            </li>
          ))}
        </ol>
        <button
          type="button"
          onClick={sortear}
          disabled={!questoes?.length}
          className="mt-8 inline-flex items-center gap-2 rounded-xl bg-stone-900 px-5 py-3 font-semibold text-white hover:bg-stone-800 disabled:opacity-50"
        >
          <Shuffle className="size-5" aria-hidden />
          Começar com uma questão aleatória
        </button>
      </section>

      <section className="mt-12" aria-labelledby="titulo-questoes">
        <h2 id="titulo-questoes" className="text-xl font-semibold">
          Ou escolha uma questão
        </h2>
        <div className="mt-4 space-y-4">
          {saude?.ia === 'desativada' && <AvisoModoBasico />}
          {erro && <CaixaDeErro mensagem={erro} aoTentarDeNovo={carregar} />}
          {!erro && !questoes && <Carregando texto="Carregando as questões…" />}
        </div>
        {[...porAno.entries()].map(([ano, lista]) => (
          <div key={ano} className="mt-6">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-stone-500">ENEM {ano}</h3>
            <ul className="mt-2 divide-y divide-stone-200 overflow-hidden rounded-xl border border-stone-200 bg-white">
              {lista.map((questao) => (
                <li key={questao.id}>
                  <a
                    href={`#/questao/${questao.id}`}
                    className="flex items-center gap-3 px-4 py-3 hover:bg-stone-50"
                    aria-label={`Questão ${questao.numero} do ENEM ${questao.ano}`}
                  >
                    <span className="w-12 shrink-0 font-semibold">Q{questao.numero}</span>
                    <span className="line-clamp-2 flex-1 text-sm text-stone-600">{questao.inicio_do_enunciado}</span>
                    <ArrowRight className="size-4 shrink-0 text-stone-400" aria-hidden />
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      <footer className="mt-16 border-t border-stone-200 pt-6 text-sm text-stone-500">
        Questões oficiais do ENEM, publicadas pelo Inep. Projeto de código aberto:{' '}
        <a href="https://github.com/sabrinasiilva/pista-enem" className="underline" target="_blank" rel="noreferrer">
          github.com/sabrinasiilva/pista-enem
        </a>
        .
      </footer>
    </main>
  )
}
