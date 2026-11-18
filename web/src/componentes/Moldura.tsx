import {
  BarChart3,
  Home,
  LogIn,
  LogOut,
  Menu,
  RotateCcw,
  Settings,
  Target,
  User,
  UserPlus,
  X,
} from 'lucide-react'
import { type ReactNode, useEffect, useState } from 'react'
import { useConta } from '../conta'
import { endereco, irPara, type PaginaSimples, type Rota } from '../rotas'

const ITENS: { pagina: PaginaSimples; rotulo: string; icone: typeof Home }[] = [
  { pagina: 'inicio', rotulo: 'Início', icone: Home },
  { pagina: 'foco', rotulo: 'Modo foco', icone: Target },
  { pagina: 'revisar', rotulo: 'Revisar erros', icone: RotateCcw },
  { pagina: 'progresso', rotulo: 'Meu progresso', icone: BarChart3 },
  { pagina: 'configuracoes', rotulo: 'Configurações', icone: Settings },
]

function Logo() {
  return (
    <a href="#/" className="text-xl font-bold tracking-tight" aria-label="Pista, página inicial">
      pista<span className="text-amber-500">.</span>
    </a>
  )
}

function MenuPrincipal({ rota }: { rota: Rota }) {
  const { usuario, sair } = useConta()
  const ativa = rota.pagina === 'questao' ? 'inicio' : rota.pagina

  return (
    <div className="flex h-full flex-col">
      <nav aria-label="Menu principal" className="flex-1 space-y-1 px-3 py-4">
        {ITENS.map(({ pagina, rotulo, icone: Icone }) => (
          <a
            key={pagina}
            href={endereco({ pagina })}
            aria-current={ativa === pagina ? 'page' : undefined}
            className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
              ativa === pagina ? 'bg-stone-900 text-white' : 'text-stone-600 hover:bg-stone-100 hover:text-stone-900'
            }`}
          >
            <Icone className="size-5" aria-hidden />
            {rotulo}
          </a>
        ))}
      </nav>

      <div className="border-t border-stone-200 p-3">
        {usuario ? (
          <div className="space-y-1">
            <a
              href={endereco({ pagina: 'perfil' })}
              aria-current={ativa === 'perfil' ? 'page' : undefined}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 transition ${
                ativa === 'perfil' ? 'bg-stone-100' : 'hover:bg-stone-100'
              }`}
            >
              <span
                aria-hidden
                className="flex size-9 items-center justify-center rounded-full bg-amber-500 font-bold uppercase text-white"
              >
                {usuario.apelido[0]}
              </span>
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold">{usuario.apelido}</span>
                <span className="block text-xs text-stone-500">Ver perfil</span>
              </span>
            </a>
            <button
              type="button"
              onClick={async () => {
                await sair()
                irPara({ pagina: 'inicio' })
              }}
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-stone-600 hover:bg-stone-100 hover:text-stone-900"
            >
              <LogOut className="size-5" aria-hidden />
              Sair
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <a
              href={endereco({ pagina: 'entrar' })}
              className="flex items-center justify-center gap-2 rounded-xl bg-stone-900 px-3 py-2.5 text-sm font-semibold text-white hover:bg-stone-700"
            >
              <LogIn className="size-4" aria-hidden />
              Entrar
            </a>
            <a
              href={endereco({ pagina: 'criar-conta' })}
              className="flex items-center justify-center gap-2 rounded-xl border border-stone-300 px-3 py-2.5 text-sm font-semibold hover:bg-stone-100"
            >
              <UserPlus className="size-4" aria-hidden />
              Criar conta
            </a>
            <p className="px-1 pt-1 text-xs text-stone-500">Conta opcional: só apelido e senha, para salvar seu progresso.</p>
          </div>
        )}
      </div>
    </div>
  )
}

/** Moldura do site: menu lateral fixo no computador e menu que abre por cima no celular. */
export function Moldura({ rota, children }: { rota: Rota; children: ReactNode }) {
  const [aberto, setAberto] = useState(false)
  const { usuario } = useConta()

  // fecha o menu do celular ao navegar
  useEffect(() => setAberto(false), [rota])

  useEffect(() => {
    if (!aberto) return
    const fecharComEsc = (evento: KeyboardEvent) => evento.key === 'Escape' && setAberto(false)
    window.addEventListener('keydown', fecharComEsc)
    return () => window.removeEventListener('keydown', fecharComEsc)
  }, [aberto])

  return (
    <div className="min-h-svh lg:flex">
      <a
        href="#conteudo"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-white focus:px-3 focus:py-2"
      >
        Pular para o conteúdo
      </a>

      {/* computador */}
      <aside className="hidden w-64 shrink-0 border-r border-stone-200 bg-white lg:block">
        <div className="sticky top-0 flex h-svh flex-col">
          <div className="px-6 pt-5">
            <Logo />
          </div>
          <MenuPrincipal rota={rota} />
        </div>
      </aside>

      {/* celular */}
      <header className="sticky top-0 z-20 flex items-center justify-between border-b border-stone-200 bg-white/90 px-4 py-3 backdrop-blur lg:hidden">
        <button
          type="button"
          onClick={() => setAberto(true)}
          aria-label="Abrir menu"
          aria-expanded={aberto}
          className="-ml-2 rounded-lg p-2 hover:bg-stone-100"
        >
          <Menu className="size-6" aria-hidden />
        </button>
        <Logo />
        <a
          href={endereco({ pagina: usuario ? 'perfil' : 'entrar' })}
          aria-label={usuario ? 'Perfil' : 'Entrar'}
          className="-mr-2 rounded-lg p-2 hover:bg-stone-100"
        >
          {usuario ? (
            <span className="flex size-7 items-center justify-center rounded-full bg-amber-500 text-sm font-bold uppercase text-white">
              {usuario.apelido[0]}
            </span>
          ) : (
            <User className="size-6" aria-hidden />
          )}
        </a>
      </header>

      {aberto && (
        <div className="fixed inset-0 z-30 lg:hidden">
          <button
            type="button"
            aria-label="Fechar menu"
            onClick={() => setAberto(false)}
            className="absolute inset-0 bg-stone-950/40"
          />
          <div role="dialog" aria-modal="true" aria-label="Menu" className="absolute inset-y-0 left-0 flex w-72 max-w-[85%] flex-col bg-white shadow-xl">
            <div className="flex items-center justify-between px-5 pt-4">
              <Logo />
              <button
                type="button"
                onClick={() => setAberto(false)}
                aria-label="Fechar menu"
                className="-mr-2 rounded-lg p-2 hover:bg-stone-100"
              >
                <X className="size-5" aria-hidden />
              </button>
            </div>
            <MenuPrincipal rota={rota} />
          </div>
        </div>
      )}

      <div id="conteudo" className="min-w-0 flex-1">
        {children}
      </div>
    </div>
  )
}
