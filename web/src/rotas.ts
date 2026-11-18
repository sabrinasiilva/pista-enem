import { useEffect, useState } from 'react'

const PAGINAS_SIMPLES = [
  'inicio',
  'entrar',
  'criar-conta',
  'recuperar',
  'foco',
  'revisar',
  'progresso',
  'perfil',
  'configuracoes',
] as const

export type PaginaSimples = (typeof PAGINAS_SIMPLES)[number]
export type Rota = { pagina: PaginaSimples } | { pagina: 'questao'; id: string }

/** Rotas por hash (#/questao/2022-141), que funcionam no GitHub Pages sem configuração extra. */
export function lerRota(hash: string): Rota {
  const questao = hash.match(/^#\/questao\/([\w-]+)$/)
  if (questao) return { pagina: 'questao', id: questao[1] }
  const nome = hash.replace(/^#\/?/, '')
  return (PAGINAS_SIMPLES as readonly string[]).includes(nome) ? { pagina: nome as PaginaSimples } : { pagina: 'inicio' }
}

export function endereco(rota: Rota): string {
  if (rota.pagina === 'questao') return `#/questao/${rota.id}`
  return rota.pagina === 'inicio' ? '#/' : `#/${rota.pagina}`
}

export function irPara(rota: Rota) {
  window.location.hash = endereco(rota)
}

export function useRota(): Rota {
  const [rota, setRota] = useState(() => lerRota(window.location.hash))
  useEffect(() => {
    const atualizar = () => {
      setRota(lerRota(window.location.hash))
      window.scrollTo?.({ top: 0 })
    }
    window.addEventListener('hashchange', atualizar)
    return () => window.removeEventListener('hashchange', atualizar)
  }, [])
  return rota
}
