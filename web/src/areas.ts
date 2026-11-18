// As 7 competências de Matemática da matriz do ENEM, com nomes curtos para o aluno escolher o foco.

export interface Area {
  competencia: string
  nome: string
  descricao: string
  habilidades: string[]
}

const intervalo = (de: number, ate: number) => Array.from({ length: ate - de + 1 }, (_, i) => `H${de + i}`)

export const AREAS: Area[] = [
  { competencia: 'C1', nome: 'Números e operações', descricao: 'Frações, porcentagem, potências, contagem', habilidades: intervalo(1, 5) },
  { competencia: 'C2', nome: 'Geometria', descricao: 'Figuras planas e espaciais, posição e forma', habilidades: intervalo(6, 9) },
  { competencia: 'C3', nome: 'Grandezas e medidas', descricao: 'Unidades, escalas, áreas e volumes', habilidades: intervalo(10, 14) },
  { competencia: 'C4', nome: 'Proporcionalidade', descricao: 'Regra de três, grandezas direta e inversamente proporcionais', habilidades: intervalo(15, 18) },
  { competencia: 'C5', nome: 'Álgebra e funções', descricao: 'Equações, funções, gráficos cartesianos', habilidades: intervalo(19, 23) },
  { competencia: 'C6', nome: 'Gráficos e tabelas', descricao: 'Leitura e interpretação de dados', habilidades: intervalo(24, 26) },
  { competencia: 'C7', nome: 'Estatística e probabilidade', descricao: 'Média, mediana, moda e chances', habilidades: intervalo(27, 30) },
]

export function areaDaHabilidade(codigo: string): Area | undefined {
  return AREAS.find((area) => area.habilidades.includes(codigo))
}

/** Áreas cujas habilidades estão todas em foco. */
export function areasEmFoco(habilidades: string[]): string[] {
  return AREAS.filter((area) => area.habilidades.every((h) => habilidades.includes(h))).map((a) => a.competencia)
}

export function habilidadesDasAreas(competencias: string[]): string[] {
  return AREAS.filter((area) => competencias.includes(area.competencia)).flatMap((area) => area.habilidades)
}
