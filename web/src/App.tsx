import { lazy, Suspense } from 'react'
import { Carregando } from './componentes/Avisos'
import { Cabecalho } from './componentes/Cabecalho'
import { PaginaInicial } from './paginas/PaginaInicial'
import { useRota } from './rotas'

// a tela da questão traz o KaTeX e o Markdown; a página inicial não precisa deles
const PaginaQuestao = lazy(() => import('./paginas/PaginaQuestao').then((m) => ({ default: m.PaginaQuestao })))

export function App() {
  const rota = useRota()
  return (
    <>
      <Cabecalho />
      {rota.pagina === 'questao' ? (
        <Suspense fallback={<Carregando texto="Carregando a questão…" />}>
          <PaginaQuestao key={rota.id} id={rota.id} />
        </Suspense>
      ) : (
        <PaginaInicial />
      )}
    </>
  )
}
