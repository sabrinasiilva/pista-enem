// Espelha os esquemas da API (api/app/esquemas.py).

export type Letra = 'A' | 'B' | 'C' | 'D' | 'E'

export type Estado = 'respondendo' | 'pista_1' | 'pista_2' | 'explicacao' | 'concluida'

export interface Saude {
  status: 'ok'
  versao: string
  questoes: number
  ia: 'gemini' | 'desativada'
  prompt: string
}

export interface QuestaoResumo {
  id: string
  ano: number
  numero: number
  area: string
  habilidade: string
  inicio_do_enunciado: string
}

export interface Questao {
  id: string
  ano: number
  numero: number
  area: string
  enunciado: string
  alternativas: { letra: Letra; texto: string }[]
  habilidade: { codigo: string; descricao: string }
  fonte: { prova: string; url: string }
}

export interface Mensagem {
  papel: 'aluno' | 'tutor'
  texto: string
  estado: Estado
  criada_em: string
}

export interface Sessao {
  id: string
  questao_id: string
  estado: Estado
  tentativas: Letra[]
  gabarito: Letra | null
  mensagens: Mensagem[]
}

export interface ResultadoDaResposta {
  acertou: boolean
  estado: Estado
  tentativas: Letra[]
  gabarito: Letra | null
  mensagem: Mensagem
}

export const ESTADOS_FINAIS: Estado[] = ['explicacao', 'concluida']
