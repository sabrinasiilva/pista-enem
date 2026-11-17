import type { Estado, Letra, Questao, QuestaoResumo, ResultadoDaResposta, Saude, Sessao } from './tipos'

const BASE = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export class ErroDaApi extends Error {
  readonly status: number
  readonly codigo: string

  constructor(status: number, codigo: string, mensagem: string) {
    super(mensagem)
    this.status = status
    this.codigo = codigo
  }
}

const SEM_CONEXAO = 'Não consegui falar com o servidor. Confira sua conexão e tente de novo.'

async function requisitar(caminho: string, init?: RequestInit): Promise<Response> {
  let resposta: Response
  try {
    resposta = await fetch(BASE + caminho, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
  } catch {
    throw new ErroDaApi(0, 'sem_conexao', SEM_CONEXAO)
  }
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => null)
    throw new ErroDaApi(
      resposta.status,
      corpo?.erro?.codigo ?? 'erro_http',
      corpo?.erro?.mensagem ?? 'Algo deu errado. Tente de novo.',
    )
  }
  return resposta
}

async function json<T>(caminho: string, init?: RequestInit): Promise<T> {
  return (await requisitar(caminho, init)).json() as Promise<T>
}

function post(corpo: unknown): RequestInit {
  return { method: 'POST', body: JSON.stringify(corpo) }
}

export interface EventoDoServidor {
  evento: string
  dados: Record<string, unknown>
}

/** Lê um fluxo Server-Sent Events. Os pedaços podem chegar cortados em qualquer ponto. */
export async function* lerEventos(fluxo: ReadableStream<Uint8Array>): AsyncGenerator<EventoDoServidor> {
  const leitor = fluxo.getReader()
  const decodificador = new TextDecoder()
  let acumulado = ''
  while (true) {
    const { value, done } = await leitor.read()
    // stream: true guarda um caractere que chegou partido entre dois pedaços
    if (value) acumulado += decodificador.decode(value, { stream: true })
    let fim = acumulado.indexOf('\n\n')
    while (fim !== -1) {
      const bloco = acumulado.slice(0, fim)
      acumulado = acumulado.slice(fim + 2)
      const campos = Object.fromEntries(
        bloco.split('\n').map((linha) => {
          const separador = linha.indexOf(': ')
          return [linha.slice(0, separador), linha.slice(separador + 2)]
        }),
      )
      if (campos.event && campos.data) yield { evento: campos.event, dados: JSON.parse(campos.data) }
      fim = acumulado.indexOf('\n\n')
    }
    if (done) return
  }
}

export const api = {
  saude: () => json<Saude>('/health'),
  listarQuestoes: () => json<QuestaoResumo[]>('/questoes'),
  obterQuestao: (id: string) => json<Questao>(`/questoes/${encodeURIComponent(id)}`),
  criarSessao: (questaoId: string) => json<Sessao>('/sessoes', post({ questao_id: questaoId })),
  obterSessao: (id: string) => json<Sessao>(`/sessoes/${encodeURIComponent(id)}`),
  responder: (sessaoId: string, alternativa: Letra) =>
    json<ResultadoDaResposta>(`/sessoes/${encodeURIComponent(sessaoId)}/respostas`, post({ alternativa })),
  explicar: (sessaoId: string) =>
    json<unknown>(`/sessoes/${encodeURIComponent(sessaoId)}/explicacao`, post({ confirmar: true })),

  /** Conversa com o tutor. Chama `aoReceber` a cada trecho e devolve o estado final. */
  async conversar(sessaoId: string, texto: string, aoReceber: (trecho: string) => void): Promise<Estado> {
    const resposta = await requisitar(`/sessoes/${encodeURIComponent(sessaoId)}/mensagens`, post({ texto }))
    if (!resposta.body) throw new ErroDaApi(0, 'sem_resposta', 'O servidor não respondeu. Tente de novo.')
    let estado: Estado | null = null
    for await (const { evento, dados } of lerEventos(resposta.body)) {
      if (evento === 'trecho') aoReceber(String(dados.texto))
      if (evento === 'fim') estado = dados.estado as Estado
    }
    if (!estado) throw new ErroDaApi(0, 'resposta_incompleta', 'A resposta foi interrompida. Tente de novo.')
    return estado
  },
}
