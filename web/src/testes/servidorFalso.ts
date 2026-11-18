import { vi } from 'vitest'
import type { Estado, Letra, Mensagem, Questao, QuestaoResumo, ResultadoDaQuestao, Sessao, Usuario } from '../tipos'

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
  /** atraso, em ms, para responder às alternativas (simula a IA pensando) */
  atrasoDaResposta?: number
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

  // contas: apelido -> dados; token -> apelido
  const contas = new Map<string, { usuario: Usuario; senha: string; codigo: string; resultados: ResultadoDaQuestao[] }>()
  const tokens = new Map<string, string>()
  const donoDaSessao = new Map<string, string>()

  const acesso = (apelido: string, codigo: string | null) => {
    const token = `token-${++contador}`
    tokens.set(token, apelido)
    return { token, usuario: contas.get(apelido)!.usuario, codigo_de_recuperacao: codigo }
  }

  const gravarResultado = (sessao: Sessao) => {
    const apelido = donoDaSessao.get(sessao.id)
    if (!apelido || (sessao.estado !== 'concluida' && sessao.estado !== 'explicacao')) return
    contas.get(apelido)!.resultados.push({
      questao_id: sessao.questao_id,
      habilidade: 'H16',
      acertou: sessao.estado === 'concluida',
      acertou_de_primeira: sessao.estado === 'concluida' && sessao.tentativas.length === 1,
      tentativas: sessao.tentativas.length,
      pediu_explicacao: sessao.estado === 'explicacao',
      concluido_em: new Date().toISOString(),
    })
  }

  const fetchFalso = vi.fn(async (endereco: string, init?: RequestInit): Promise<Response> => {
    if (estado.semConexao) throw new TypeError('Failed to fetch')
    const { pathname, searchParams } = new URL(endereco)
    const corpo = init?.body ? JSON.parse(String(init.body)) : null
    const metodo = init?.method ?? 'GET'
    const cabecalhos = (init?.headers ?? {}) as Record<string, string>
    const token = cabecalhos.Authorization?.replace('Bearer ', '')
    const apelidoDoToken = token ? tokens.get(token) : undefined
    if (token && !apelidoDoToken) return erro(401, 'sessao_expirada', 'Sua sessão expirou. Entre de novo.')
    const conta = apelidoDoToken ? contas.get(apelidoDoToken) : undefined

    // ------------------------------------------------ contas
    if (pathname === '/contas' && metodo === 'POST') {
      if (contas.has(corpo.apelido)) return erro(409, 'apelido_em_uso', 'Esse apelido já está em uso. Escolha outro.')
      const usuario: Usuario = {
        id: `u-${corpo.apelido}`,
        apelido: corpo.apelido,
        meta_semanal: corpo.meta_semanal,
        habilidades_foco: corpo.habilidades_foco,
        tema: 'sistema',
        criado_em: '2026-11-17T12:00:00Z',
      }
      contas.set(corpo.apelido, { usuario, senha: corpo.senha, codigo: 'ABCD-EFGH-JKMN-PQRS', resultados: [] })
      return json(acesso(corpo.apelido, 'ABCD-EFGH-JKMN-PQRS'), 201)
    }
    if (pathname === '/contas/entrar') {
      const dados = contas.get(corpo.apelido.toLowerCase())
      if (!dados || dados.senha !== corpo.senha) return erro(401, 'credenciais_invalidas', 'Apelido ou senha incorretos.')
      return json(acesso(dados.usuario.apelido, null))
    }
    if (pathname === '/contas/recuperar') {
      const dados = contas.get(corpo.apelido)
      if (!dados || dados.codigo !== corpo.codigo_de_recuperacao) return erro(401, 'codigo_invalido', 'Apelido ou código de recuperação incorretos.')
      dados.senha = corpo.nova_senha
      dados.codigo = 'NOVO-CODI-GODE-RECU'
      return json(acesso(dados.usuario.apelido, dados.codigo))
    }
    if (pathname === '/contas/sair') {
      if (token) tokens.delete(token)
      return new Response(null, { status: 204 })
    }
    if (pathname === '/recomendacoes') return json(RESUMOS.slice(0, Number(searchParams.get('quantidade') ?? 5)))
    if (pathname.startsWith('/eu')) {
      if (!conta) return erro(401, 'login_necessario', 'Entre na sua conta para continuar.')
      if (pathname === '/eu' && metodo === 'GET') return json(conta.usuario)
      if (pathname === '/eu' && metodo === 'PATCH') {
        conta.usuario = { ...conta.usuario, ...corpo }
        return json(conta.usuario)
      }
      if (pathname === '/eu' && metodo === 'DELETE') {
        if (corpo.senha !== conta.senha) return erro(401, 'senha_incorreta', 'A senha está incorreta.')
        contas.delete(conta.usuario.apelido)
        return new Response(null, { status: 204 })
      }
      if (pathname === '/eu/senha') {
        if (corpo.senha_atual !== conta.senha) return erro(401, 'senha_incorreta', 'A senha atual está incorreta.')
        conta.senha = corpo.nova_senha
        return new Response(null, { status: 204 })
      }
      if (pathname === '/eu/progresso') {
        const r = conta.resultados
        return json({
          total_de_questoes: r.length,
          acertos_de_primeira: r.filter((x) => x.acertou_de_primeira).length,
          sequencia_de_dias: r.length ? 1 : 0,
          feitas_na_semana: r.length,
          meta_semanal: conta.usuario.meta_semanal,
          por_habilidade: r.length
            ? [{ codigo: 'H16', descricao: 'Variação de grandezas', feitas: r.length, acertos_de_primeira: r.filter((x) => x.acertou_de_primeira).length }]
            : [],
          recentes: r,
        })
      }
      if (pathname === '/eu/revisar') {
        return json(
          conta.resultados
            .filter((x) => !x.acertou_de_primeira)
            .map((x) => ({ questao: RESUMOS.find((q) => q.id === x.questao_id) ?? RESUMOS[0], ultima_tentativa: x })),
        )
      }
    }

    if (pathname === '/health')
      return json({ status: 'ok', versao: '0.1.0', questoes: 1, ia: opcoes.iaDesativada ? 'desativada' : 'gemini', prompt: 'tutor_v1' })
    if (pathname === '/questoes') return json(RESUMOS)
    if (pathname.startsWith('/questoes/')) {
      const resumo = RESUMOS.find((q) => pathname === `/questoes/${q.id}`)
      return resumo
        ? json({ ...QUESTAO, id: resumo.id, ano: resumo.ano, numero: resumo.numero })
        : erro(404, 'questao_nao_encontrada', 'Questão não encontrada.')
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
      if (conta) donoDaSessao.set(sessao.id, conta.usuario.apelido)
      return json(visivel(sessao), 201)
    }

    const rota = pathname.match(/^\/sessoes\/([^/]+)(?:\/(\w+))?$/)
    const sessao = rota && sessoes.get(rota[1])
    if (!rota || !sessao) return erro(404, 'sessao_nao_encontrada', 'Sessão não encontrada ou expirada.')
    const acao = rota[2]

    if (!acao) return json(visivel(sessao))
    if (acao === 'respostas') {
      if (opcoes.atrasoDaResposta) await new Promise((r) => setTimeout(r, opcoes.atrasoDaResposta))
      const letra = corpo.alternativa as Letra
      if (sessao.tentativas.includes(letra)) return erro(409, 'alternativa_repetida', `Você já tentou a alternativa ${letra}.`)
      falar(sessao, 'aluno', `Marquei a alternativa ${letra}.`)
      sessao.tentativas.push(letra)
      const acertou = letra === GABARITO
      sessao.estado = acertou ? 'concluida' : (PROXIMO[sessao.estado] ?? sessao.estado)
      falar(sessao, 'tutor', acertou ? 'Isso! Como você pensou?' : `Pista para o estado ${sessao.estado}: o que acontece com o volume?`)
      gravarResultado(sessao)
      return json({ acertou, estado: sessao.estado, tentativas: sessao.tentativas, gabarito: visivel(sessao).gabarito, mensagem: sessao.mensagens.at(-1) })
    }
    if (acao === 'explicacao') {
      if (sessao.estado === 'respondendo') return erro(409, 'tente_antes', 'Marque uma alternativa antes.')
      sessao.estado = 'explicacao'
      falar(sessao, 'aluno', 'Quero ver a explicação.')
      falar(sessao, 'tutor', 'O volume é multiplicado por 8, então são 24 porções. Alternativa E.')
      gravarResultado(sessao)
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
    contas,
    religar: () => {
      estado.semConexao = false
    },
  }
}
