import { ArrowRight, PartyPopper, Target } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { api, ErroDaApi } from '../api'
import { CaixaDeErro, Carregando } from '../componentes/Avisos'
import { Botao, Cartao, ExigeConta, Pagina } from '../componentes/ui'
import { useConta } from '../conta'
import { iniciarFoco } from '../foco'
import { endereco, irPara } from '../rotas'
import type { ParaRevisar } from '../tipos'
import { descreverResultado } from './PaginaProgresso'

export function PaginaRevisar() {
  const { usuario, carregando } = useConta()
  const [lista, setLista] = useState<ParaRevisar[] | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  const carregar = useCallback(async () => {
    setErro(null)
    try {
      setLista(await api.revisar())
    } catch (e) {
      setErro(e instanceof ErroDaApi ? e.message : 'Não consegui carregar a lista.')
    }
  }, [])

  useEffect(() => {
    if (usuario) void carregar()
  }, [usuario, carregar])

  if (carregando) return <Carregando />
  if (!usuario) {
    return (
      <Pagina titulo="Revisar erros">
        <ExigeConta motivo="Com uma conta, as questões que você errou ficam guardadas aqui para refazer depois." />
      </Pagina>
    )
  }

  const revisarTodas = () => {
    if (!lista?.length) return
    iniciarFoco({ ids: lista.slice(0, 15).map((item) => item.questao.id), minutos: null })
    irPara({ pagina: 'foco' })
  }

  return (
    <Pagina
      titulo="Revisar erros"
      subtitulo="Questões em que você não acertou de primeira. Refazer é o jeito mais rápido de fixar."
      largura="max-w-4xl"
    >
      {erro && <CaixaDeErro mensagem={erro} aoTentarDeNovo={carregar} />}
      {!erro && !lista && <Carregando />}
      {lista && lista.length === 0 && (
        <Cartao>
          <div className="flex items-start gap-3">
            <PartyPopper className="mt-0.5 size-6 shrink-0 text-emerald-500" aria-hidden />
            <div>
              <p className="font-semibold">Nada para revisar agora.</p>
              <p className="mt-1 text-stone-600">
                Quando você errar uma questão ou precisar da explicação, ela aparece aqui.{' '}
                <a href={endereco({ pagina: 'foco' })} className="font-semibold text-stone-900 underline-offset-4 hover:underline">
                  Fazer um foco
                </a>
              </p>
            </div>
          </div>
        </Cartao>
      )}
      {lista && lista.length > 0 && (
        <>
          <Botao onClick={revisarTodas}>
            <Target className="size-4" aria-hidden />
            Revisar {Math.min(lista.length, 15)} no modo foco
          </Botao>
          <ul className="grid gap-3 sm:grid-cols-2">
            {lista.map(({ questao, ultima_tentativa }) => (
              <li key={questao.id}>
                <a
                  href={endereco({ pagina: 'questao', id: questao.id })}
                  aria-label={`Refazer a questão ${questao.numero} do ENEM ${questao.ano}`}
                  className="group flex h-full flex-col rounded-2xl border border-stone-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
                >
                  <span className="flex items-center justify-between gap-2">
                    <span className="font-semibold">
                      ENEM {questao.ano} · Questão {questao.numero}
                    </span>
                    <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                      {descreverResultado(ultima_tentativa)}
                    </span>
                  </span>
                  <span className="mt-2 line-clamp-2 flex-1 text-sm text-stone-600">{questao.inicio_do_enunciado}</span>
                  <span className="mt-3 inline-flex items-center gap-1 text-sm font-medium">
                    Refazer
                    <ArrowRight className="size-4 transition group-hover:translate-x-0.5" aria-hidden />
                  </span>
                </a>
              </li>
            ))}
          </ul>
        </>
      )}
    </Pagina>
  )
}
