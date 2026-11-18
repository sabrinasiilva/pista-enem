import { lazy, Suspense } from 'react'
import { Carregando } from './componentes/Avisos'
import { Moldura } from './componentes/Moldura'
import { ProvedorDaConta } from './conta'
import { PaginaConfiguracoes } from './paginas/PaginaConfiguracoes'
import { PaginaCriarConta } from './paginas/PaginaCriarConta'
import { PaginaEntrar } from './paginas/PaginaEntrar'
import { PaginaInicial } from './paginas/PaginaInicial'
import { PaginaPerfil } from './paginas/PaginaPerfil'
import { PaginaProgresso } from './paginas/PaginaProgresso'
import { PaginaRecuperar } from './paginas/PaginaRecuperar'
import { PaginaRevisar } from './paginas/PaginaRevisar'
import { type Rota, useRota } from './rotas'
import { ProvedorDoTema } from './tema'

// as telas que mostram questões trazem o KaTeX e o Markdown; as outras não precisam deles
const PaginaQuestao = lazy(() => import('./paginas/PaginaQuestao').then((m) => ({ default: m.PaginaQuestao })))
const PaginaFoco = lazy(() => import('./paginas/PaginaFoco').then((m) => ({ default: m.PaginaFoco })))

function Conteudo({ rota }: { rota: Rota }) {
  switch (rota.pagina) {
    case 'questao':
      return <PaginaQuestao key={rota.id} id={rota.id} />
    case 'foco':
      return <PaginaFoco />
    case 'entrar':
      return <PaginaEntrar />
    case 'criar-conta':
      return <PaginaCriarConta />
    case 'recuperar':
      return <PaginaRecuperar />
    case 'revisar':
      return <PaginaRevisar />
    case 'progresso':
      return <PaginaProgresso />
    case 'perfil':
      return <PaginaPerfil />
    case 'configuracoes':
      return <PaginaConfiguracoes />
    default:
      return <PaginaInicial />
  }
}

export function App() {
  const rota = useRota()
  return (
    <ProvedorDoTema>
      <ProvedorDaConta>
        <Moldura rota={rota}>
          <Suspense fallback={<Carregando />}>
            <Conteudo rota={rota} />
          </Suspense>
        </Moldura>
      </ProvedorDaConta>
    </ProvedorDoTema>
  )
}
