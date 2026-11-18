import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from 'react'
import { aoExpirarASessao, api, definirToken } from './api'
import { local } from './armazenamento'
import { useTema } from './tema'
import type { Acesso, Usuario } from './tipos'

const CHAVE = 'pista:token'

interface ValorDaConta {
  usuario: Usuario | null
  /** true enquanto a conta guardada neste aparelho ainda está sendo conferida */
  carregando: boolean
  entrar: (acesso: Acesso) => void
  sair: () => Promise<void>
  atualizar: (usuario: Usuario) => void
}

const ContextoDaConta = createContext<ValorDaConta | null>(null)

export function ProvedorDaConta({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [carregando, setCarregando] = useState(() => local.ler(CHAVE) !== null)
  const { escolherTema } = useTema()

  const esquecer = useCallback(() => {
    local.apagar(CHAVE)
    definirToken(null)
    setUsuario(null)
  }, [])

  const usarConta = useCallback(
    (conta: Usuario) => {
      setUsuario(conta)
      escolherTema(conta.tema) // o tema escolhido na conta vale em todo aparelho
    },
    [escolherTema],
  )

  useEffect(() => {
    aoExpirarASessao(esquecer)
    const token = local.ler(CHAVE)
    if (!token) return
    definirToken(token)
    api
      .eu()
      .then(usarConta)
      .catch(esquecer)
      .finally(() => setCarregando(false))
    return () => aoExpirarASessao(null)
  }, [esquecer, usarConta])

  const entrar = useCallback(
    (acesso: Acesso) => {
      local.gravar(CHAVE, acesso.token)
      definirToken(acesso.token)
      usarConta(acesso.usuario)
    },
    [usarConta],
  )

  const sair = useCallback(async () => {
    await api.sair().catch(() => {})
    esquecer()
  }, [esquecer])

  return (
    <ContextoDaConta.Provider value={{ usuario, carregando, entrar, sair, atualizar: setUsuario }}>
      {children}
    </ContextoDaConta.Provider>
  )
}

export function useConta(): ValorDaConta {
  const valor = useContext(ContextoDaConta)
  if (!valor) throw new Error('useConta fora do ProvedorDaConta')
  return valor
}
