import { describe, expect, it, vi } from 'vitest'
import { aoExpirarASessao, api, definirToken, ErroDaApi, lerEventos } from './api'

function fluxoDe(...pedacos: Uint8Array[]): ReadableStream<Uint8Array> {
  return new ReadableStream({
    start(controle) {
      for (const pedaco of pedacos) controle.enqueue(pedaco)
      controle.close()
    },
  })
}

describe('lerEventos', () => {
  it('junta eventos que chegam cortados em qualquer ponto', async () => {
    const texto = 'event: trecho\ndata: {"texto": "Olá "}\n\nevent: fim\ndata: {"estado": "pista_1"}\n\n'
    const bytes = new TextEncoder().encode(texto)
    // corta no meio do "á" (2 bytes em UTF-8) e no meio de um evento
    const corte = texto.indexOf('á') + 1
    const fluxo = fluxoDe(bytes.slice(0, corte), bytes.slice(corte, 40), bytes.slice(40))
    const eventos = []
    for await (const evento of lerEventos(fluxo)) eventos.push(evento)
    expect(eventos).toEqual([
      { evento: 'trecho', dados: { texto: 'Olá ' } },
      { evento: 'fim', dados: { estado: 'pista_1' } },
    ])
  })
})

describe('erros da API', () => {
  it('lê o código e a mensagem do erro padronizado', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify({ erro: { codigo: 'tente_antes', mensagem: 'Tente antes.' } }), { status: 409 })),
    )
    await expect(api.explicar('s1')).rejects.toMatchObject({ status: 409, codigo: 'tente_antes', message: 'Tente antes.' })
  })

  it('transforma falha de rede em erro de conexão', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))))
    const erro = await api.saude().catch((e) => e)
    expect(erro).toBeInstanceOf(ErroDaApi)
    expect(erro.codigo).toBe('sem_conexao')
  })

  it('aguenta resposta de erro que não é JSON', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('Bad Gateway', { status: 502 })))
    await expect(api.saude()).rejects.toMatchObject({ status: 502, codigo: 'erro_http' })
  })
})

describe('token vencido', () => {
  it('esquece o token e repete a chamada sem ele', async () => {
    const chamadas: (string | undefined)[] = []
    vi.stubGlobal(
      'fetch',
      vi.fn(async (_: string, init?: RequestInit) => {
        const autorizacao = (init?.headers as Record<string, string>).Authorization
        chamadas.push(autorizacao)
        return autorizacao
          ? new Response(JSON.stringify({ erro: { codigo: 'sessao_expirada', mensagem: 'expirou' } }), { status: 401 })
          : new Response(JSON.stringify([]), { status: 200 })
      }),
    )
    let avisado = false
    aoExpirarASessao(() => {
      avisado = true
    })
    definirToken('velho')
    await expect(api.listarQuestoes()).resolves.toEqual([])
    expect(chamadas).toEqual(['Bearer velho', undefined])
    expect(avisado).toBe(true)
  })
})
