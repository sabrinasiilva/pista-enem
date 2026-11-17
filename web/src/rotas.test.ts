import { describe, expect, it } from 'vitest'
import { lerRota } from './rotas'

describe('lerRota', () => {
  it('reconhece a página da questão', () => {
    expect(lerRota('#/questao/2022-141')).toEqual({ pagina: 'questao', id: '2022-141' })
  })

  it('qualquer outro endereço vai para o início', () => {
    expect(lerRota('')).toEqual({ pagina: 'inicio' })
    expect(lerRota('#/')).toEqual({ pagina: 'inicio' })
    expect(lerRota('#/questao/<script>')).toEqual({ pagina: 'inicio' })
  })
})
