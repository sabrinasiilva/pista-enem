import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from 'react'
import { local } from './armazenamento'
import type { Tema } from './tipos'

const CHAVE = 'pista:tema'
const ESCURO_NO_SISTEMA = '(prefers-color-scheme: dark)'

export function lerTemaGuardado(): Tema {
  const guardado = local.ler(CHAVE)
  return guardado === 'claro' || guardado === 'escuro' ? guardado : 'sistema'
}

function sistemaEscuro(): boolean {
  return typeof window.matchMedia === 'function' && window.matchMedia(ESCURO_NO_SISTEMA).matches
}

export function aplicarTema(tema: Tema) {
  const escuro = tema === 'escuro' || (tema === 'sistema' && sistemaEscuro())
  document.documentElement.classList.toggle('dark', escuro)
}

interface ValorDoTema {
  tema: Tema
  escolherTema: (tema: Tema) => void
}

const ContextoDoTema = createContext<ValorDoTema | null>(null)

export function ProvedorDoTema({ children }: { children: ReactNode }) {
  const [tema, setTema] = useState<Tema>(lerTemaGuardado)

  useEffect(() => {
    aplicarTema(tema)
    if (tema !== 'sistema' || typeof window.matchMedia !== 'function') return
    // acompanha a troca de tema do sistema enquanto a página está aberta
    const consulta = window.matchMedia(ESCURO_NO_SISTEMA)
    const mudar = () => aplicarTema('sistema')
    consulta.addEventListener('change', mudar)
    return () => consulta.removeEventListener('change', mudar)
  }, [tema])

  const escolherTema = useCallback((novo: Tema) => {
    local.gravar(CHAVE, novo)
    setTema(novo)
  }, [])

  return <ContextoDoTema.Provider value={{ tema, escolherTema }}>{children}</ContextoDoTema.Provider>
}

export function useTema(): ValorDoTema {
  const valor = useContext(ContextoDoTema)
  if (!valor) throw new Error('useTema fora do ProvedorDoTema')
  return valor
}
