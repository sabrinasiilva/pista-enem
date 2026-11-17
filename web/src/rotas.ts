import { useEffect, useState } from 'react'

export type Rota = { pagina: 'inicio' } | { pagina: 'questao'; id: string }

/** Rotas por hash (#/questao/2022-141), que funcionam no GitHub Pages sem configuração extra. */
export function lerRota(hash: string): Rota {
  const questao = hash.match(/^#\/questao\/([\w-]+)$/)
  return questao ? { pagina: 'questao', id: questao[1] } : { pagina: 'inicio' }
}

export function irPara(rota: Rota) {
  window.location.hash = rota.pagina === 'questao' ? `#/questao/${rota.id}` : '#/'
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
