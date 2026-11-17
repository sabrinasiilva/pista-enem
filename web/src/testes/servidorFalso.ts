import { vi } from 'vitest'
import type { Estado, Letra, Mensagem, Questao, QuestaoResumo, Sessao } from '../tipos'

export const QUESTAO: Questao = {
  id: '2022-141',
  ano: 2022,
  numero: 141,
  area: 'matematica',
  enunciado:
    'Uma cozinheira faz docinhos com $2$ cm de diâmetro e cada porção custa R\\$ 10,00.\n\n| Tamanho | Porções |\n|---|---|\n| pequeno | 1 |\n\nO volume cresce com $d^3$. Quantas porções ela deve preparar?',
  alternativas: [
    { letra: 'A', texto: '2' },
    { letra: 'B', texto: '3' },
    { letra: 'C', texto: '6' },
    { letra: 'D', texto: '12' },
    { letra: 'E', texto: '24' },
  ],
  habilidade: { codigo: 'H16', descricao: 'Resolver situação-problema envolvendo a variação de grandezas.' },
  fonte: {
    prova: 'ENEM 2022, 2º dia, caderno 6 (cinza), questão 141',
    url: 'https://download.inep.gov.br/enem/provas_e_gabaritos/2022_PV_impresso_D2_CD6.pdf',
  },
}

const GABARITO: Letra = 'E'
const PROXIMO: Partial<Record<Estado, Estado>> = { respondendo: 'pista_1', pista_1: 'pista_2', pista_2: 'explicacao' }

export const RESUMOS: QuestaoResumo[] = [
  { id: '2022-141', ano: 2022, numero: 141, area: 'matematica', habilidade: 'H16', inicio_do_enunciado: 'Uma cozinheira…' },
  { id: '2023-150', ano: 2023, numero: 150, area: 'matematica', habilidade: 'H8', inicio_do_enunciado: 'Uma escultura…' },
]

interface Opcoes {
  iaDesativada?: boolean
  semConexao?: boolean
  respostaDoTutor?: string
}

function json(dados: unknown, status = 200): Response {
  return new Response(JSON.stringify(dados), { status, headers: { 'Content-Type': 'application/json' } })
}

function erro(status: number, codigo: string, mensagem: string): Response {
  return json({ erro: { codigo, mensagem } }, status)
}

/** Substitui o fetch por um servidor em memória que imita a API do Pista. */
export function servidorFalso(opcoes: Opcoes = {}) {
  const sessoes = new Map<string, Sessao>()
  let contador = 0
  const estado = { semConexao: opcoes.semConexao ?? false }

  const falar = (sessao: Sessao, papel: Mensagem['papel'], texto: string) =>
    sessao.mensagens.push({ papel, texto, estado: sessao.estado, criada_em: new Date().toISOString() })

  const visivel = (sessao: Sessao): Sessao => ({
    ...structuredClone(sessao),
    gabarito: sessao.estado === 'explicacao' || sessao.estado === 'concluida' ? GABARITO : null,
  })

  const fetchFalso = vi.fn(async (endereco: string, init?: RequestInit): Promise<Response> => {
    if (estado.semConexao) throw new TypeError('Failed to fetch')
    const { pathname } = new URL(endereco)
    const corpo = init?.body ? JSON.parse(String(init.body)) : null
    const metodo = init?.method ?? 'GET'

    if (pathname === '/health')
      return json({ status: 'ok', versao: '0.1.0', questoes: 1, ia: opcoes.iaDesativada ? 'desativada' : 'gemini', prompt: 'tutor_v1' })
    if (pathname === '/questoes') return json(RESUMOS)
    if (pathname.startsWith('/questoes/')) {
      return pathname === '/questoes/2022-141' ? json(QUESTAO) : erro(404, 'questao_nao_encontrada', 'Questão não encontrada.')
    }
    if (pathname === '/sessoes' && metodo === 'POST') {
      const sessao: Sessao = {
        id: `sessao-${++contador}`,
        questao_id: corpo.questao_id,
        estado: 'respondendo',
        tentativas: [],
        gabarito: null,
        mensagens: [],
      }
      sessoes.set(sessao.id, sessao)
      return json(visivel(sessao), 201)
    }

    const rota = pathname.match(/^\/sessoes\/([^/]+)(?:\/(\w+))?$/)
    const sessao = rota && sessoes.get(rota[1])
    if (!rota || !sessao) return erro(404, 'sessao_nao_encontrada', 'Sessão não encontrada ou expirada.')
    const acao = rota[2]

    if (!acao) return json(visivel(sessao))
    if (acao === 'respostas') {
      const letra = corpo.alternativa as Letra
      if (sessao.tentativas.includes(letra)) return erro(409, 'alternativa_repetida', `Você já tentou a alternativa ${letra}.`)
      falar(sessao, 'aluno', `Marquei a alternativa ${letra}.`)
      sessao.tentativas.push(letra)
      const acertou = letra === GABARITO
      sessao.estado = acertou ? 'concluida' : (PROXIMO[sessao.estado] ?? sessao.estado)
      falar(sessao, 'tutor', acertou ? 'Isso! Como você pensou?' : `Pista para o estado ${sessao.estado}: o que acontece com o volume?`)
      return json({ acertou, estado: sessao.estado, tentativas: sessao.tentativas, gabarito: visivel(sessao).gabarito, mensagem: sessao.mensagens.at(-1) })
    }
    if (acao === 'explicacao') {
      if (sessao.estado === 'respondendo') return erro(409, 'tente_antes', 'Marque uma alternativa antes.')
      sessao.estado = 'explicacao'
      falar(sessao, 'aluno', 'Quero ver a explicação.')
      falar(sessao, 'tutor', 'O volume é multiplicado por 8, então são 24 porções. Alternativa E.')
      return json({ estado: sessao.estado, gabarito: GABARITO, mensagem: sessao.mensagens.at(-1) })
    }
    if (acao === 'mensagens') {
      const resposta = opcoes.respostaDoTutor ?? 'Que medida da esfera muda quando o diâmetro dobra?'
      falar(sessao, 'aluno', corpo.texto)
      falar(sessao, 'tutor', resposta)
      const blocos = resposta.split(' ').map((palavra) => `event: trecho\ndata: ${JSON.stringify({ texto: `${palavra} ` })}\n\n`)
      blocos.push(`event: fim\ndata: ${JSON.stringify({ estado: sessao.estado })}\n\n`)
      const codificador = new TextEncoder()
      const fluxo = new ReadableStream<Uint8Array>({
        start(controle) {
          for (const bloco of blocos) controle.enqueue(codificador.encode(bloco))
          controle.close()
        },
      })
      return new Response(fluxo, { headers: { 'Content-Type': 'text/event-stream' } })
    }
    return erro(404, 'rota_nao_encontrada', 'Rota não encontrada.')
  })

  vi.stubGlobal('fetch', fetchFalso)
  return {
    fetch: fetchFalso,
    sessoes,
    religar: () => {
      estado.semConexao = false
    },
  }
}
