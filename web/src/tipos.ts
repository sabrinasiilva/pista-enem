// Espelha os esquemas da API (api/app/esquemas.py).

export type Letra = 'A' | 'B' | 'C' | 'D' | 'E'

export type Estado = 'respondendo' | 'pista_1' | 'pista_2' | 'explicacao' | 'concluida'

export interface Saude {
  status: 'ok'
  versao: string
  questoes: number
  ia: 'gemini' | 'desativada' | 'cota_esgotada'
  prompt: string
}

export interface QuestaoResumo {
  id: string
  ano: number
  numero: number
  area: string
  habilidade: string
  /** Habilidade com a área ("MT-H16"), a mesma usada no progresso e no foco. */
  habilidade_chave: string
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

// ---------------------------------------------------------------- contas e progresso

export type Tema = 'claro' | 'escuro' | 'sistema'

export interface Usuario {
  id: string
  apelido: string
  meta_semanal: number
  habilidades_foco: string[]
  tema: Tema
  criado_em: string
}

export interface Acesso {
  token: string
  usuario: Usuario
  codigo_de_recuperacao: string | null
}

export interface ResultadoDaQuestao {
  questao_id: string
  habilidade: string
  acertou: boolean
  acertou_de_primeira: boolean
  tentativas: number
  pediu_explicacao: boolean
  concluido_em: string
}

export interface Progresso {
  total_de_questoes: number
  acertos_de_primeira: number
  sequencia_de_dias: number
  feitas_na_semana: number
  meta_semanal: number
  por_habilidade: { codigo: string; descricao: string; feitas: number; acertos_de_primeira: number }[]
  recentes: ResultadoDaQuestao[]
}

export interface ParaRevisar {
  questao: QuestaoResumo
  ultima_tentativa: ResultadoDaQuestao
}
