// Matérias e competências da matriz do ENEM, com nomes curtos para o aluno escolher o foco.
// A matriz numera as habilidades de 1 a 30 em cada área, então o código leva a sigla: "MT-H16", "CN-H16".

export type Materia = 'matematica' | 'natureza'

export const MATERIAS: { id: Materia; nome: string; nomeCurto: string; sigla: string }[] = [
  { id: 'matematica', nome: 'Matemática', nomeCurto: 'Matemática', sigla: 'MT' },
  { id: 'natureza', nome: 'Ciências da Natureza', nomeCurto: 'Natureza', sigla: 'CN' },
]

export interface Area {
  materia: Materia
  competencia: string
  nome: string
  descricao: string
  habilidades: string[]
}

const intervalo = (sigla: string, de: number, ate: number) =>
  Array.from({ length: ate - de + 1 }, (_, i) => `${sigla}-H${de + i}`)

const mt = (numero: number, nome: string, descricao: string, de: number, ate: number): Area => ({
  materia: 'matematica',
  competencia: `MT-C${numero}`,
  nome,
  descricao,
  habilidades: intervalo('MT', de, ate),
})

const cn = (numero: number, nome: string, descricao: string, de: number, ate: number): Area => ({
  materia: 'natureza',
  competencia: `CN-C${numero}`,
  nome,
  descricao,
  habilidades: intervalo('CN', de, ate),
})

export const AREAS: Area[] = [
  mt(1, 'Números e operações', 'Frações, porcentagem, potências, contagem', 1, 5),
  mt(2, 'Geometria', 'Figuras planas e espaciais, posição e forma', 6, 9),
  mt(3, 'Grandezas e medidas', 'Unidades, escalas, áreas e volumes', 10, 14),
  mt(4, 'Proporcionalidade', 'Regra de três, grandezas direta e inversamente proporcionais', 15, 18),
  mt(5, 'Álgebra e funções', 'Equações, funções, gráficos cartesianos', 19, 23),
  mt(6, 'Gráficos e tabelas', 'Leitura e interpretação de dados', 24, 26),
  mt(7, 'Estatística e probabilidade', 'Média, mediana, moda e chances', 27, 30),
  cn(1, 'Ciência e sociedade', 'Ciência como construção humana, história e impactos', 1, 4),
  cn(2, 'Tecnologias no dia a dia', 'Aparelhos, materiais e processos tecnológicos', 5, 7),
  cn(3, 'Meio ambiente', 'Degradação, conservação e recursos naturais', 8, 12),
  cn(4, 'Saúde e ecologia', 'Seres vivos, ambiente e saúde humana', 13, 16),
  cn(5, 'Método científico', 'Experimentos, medidas e procedimentos', 17, 19),
  cn(6, 'Física', 'Energia, movimento, eletricidade, ondas e calor', 20, 23),
  cn(7, 'Química', 'Reações, soluções, substâncias e cálculos químicos', 24, 27),
  cn(8, 'Biologia', 'Genética, evolução, células e fisiologia', 28, 30),
]

export function nomeDaMateria(materia: string): string {
  return MATERIAS.find((m) => m.id === materia)?.nome ?? materia
}

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
