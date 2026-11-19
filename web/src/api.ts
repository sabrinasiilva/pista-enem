import type {
  Acesso,
  Estado,
  Letra,
  ParaRevisar,
  Progresso,
  Questao,
  QuestaoResumo,
  ResultadoDaResposta,
  Saude,
  Sessao,
  Tema,
  Usuario,
} from './tipos'

const BASE = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')

/** Endereço completo de um caminho da API, como o das figuras das questões. */
export const urlDaApi = (caminho: string) => `${BASE}${caminho}`

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

// token da conta (se houver) e o que fazer quando ele expira
let tokenAtual: string | null = null
let aoExpirar: (() => void) | null = null

export function definirToken(token: string | null) {
  tokenAtual = token
}

export function aoExpirarASessao(funcao: (() => void) | null) {
  aoExpirar = funcao
}

async function requisitar(caminho: string, init?: RequestInit): Promise<Response> {
  let resposta: Response
  try {
    resposta = await fetch(BASE + caminho, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(tokenAtual ? { Authorization: `Bearer ${tokenAtual}` } : {}),
        ...init?.headers,
      },
    })
  } catch {
    throw new ErroDaApi(0, 'sem_conexao', SEM_CONEXAO)
  }
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => null)
    if (resposta.status === 401 && corpo?.erro?.codigo === 'sessao_expirada' && tokenAtual) {
      // o token venceu: esquece a conta e repete a chamada sem ele, uma única vez
      // (quem só queria ver uma questão não deve ver erro por causa de um login antigo)
      tokenAtual = null
      aoExpirar?.()
      return requisitar(caminho, init)
    }
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

function com(metodo: string, corpo: unknown): RequestInit {
  return { method: metodo, body: JSON.stringify(corpo) }
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
  parecidas: (id: string, quantidade = 3) =>
    json<QuestaoResumo[]>(`/questoes/${encodeURIComponent(id)}/parecidas?quantidade=${quantidade}`),
  criarSessao: (questaoId: string) => json<Sessao>('/sessoes', post({ questao_id: questaoId })),
  obterSessao: (id: string) => json<Sessao>(`/sessoes/${encodeURIComponent(id)}`),
  responder: (sessaoId: string, alternativa: Letra) =>
    json<ResultadoDaResposta>(`/sessoes/${encodeURIComponent(sessaoId)}/respostas`, post({ alternativa })),
  explicar: (sessaoId: string) =>
    json<unknown>(`/sessoes/${encodeURIComponent(sessaoId)}/explicacao`, post({ confirmar: true })),

  // contas
  cadastrar: (dados: { apelido: string; senha: string; meta_semanal: number; habilidades_foco: string[] }) =>
    json<Acesso>('/contas', post(dados)),
  entrar: (apelido: string, senha: string) => json<Acesso>('/contas/entrar', post({ apelido, senha })),
  recuperar: (apelido: string, codigo: string, novaSenha: string) =>
    json<Acesso>('/contas/recuperar', post({ apelido, codigo_de_recuperacao: codigo, nova_senha: novaSenha })),
  sair: async () => {
    await requisitar('/contas/sair', { method: 'POST' })
  },
  eu: () => json<Usuario>('/eu'),
  atualizarPerfil: (dados: { meta_semanal?: number; habilidades_foco?: string[]; tema?: Tema }) =>
    json<Usuario>('/eu', com('PATCH', dados)),
  trocarSenha: async (senhaAtual: string, novaSenha: string) => {
    await requisitar('/eu/senha', com('PUT', { senha_atual: senhaAtual, nova_senha: novaSenha }))
  },
  apagarConta: async (senha: string) => {
    await requisitar('/eu', com('DELETE', { senha }))
  },
  progresso: () => json<Progresso>('/eu/progresso'),
  revisar: () => json<ParaRevisar[]>('/eu/revisar'),
  recomendacoes: (quantidade: number, habilidades: string[] = []) => {
    const parametros = new URLSearchParams({ quantidade: String(quantidade) })
    if (habilidades.length) parametros.set('habilidades', habilidades.join(','))
    return json<QuestaoResumo[]>(`/recomendacoes?${parametros}`)
  },

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
