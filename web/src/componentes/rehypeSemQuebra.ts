// Impede que a pontuação logo depois de uma fórmula vá sozinha para a linha de baixo
// ("magnitudes M₁ e M₂" + quebra + ", medidos"). Junta a fórmula e a pontuação num
// span que não quebra. Roda depois do rehype-katex.

interface No {
  type: string
  value?: string
  tagName?: string
  properties?: Record<string, unknown>
  children?: No[]
}

const PONTUACAO = /^[,.;:!?)\]]+/

function ehFormula(no: No): boolean {
  const classes = no.properties?.className
  return no.type === 'element' && Array.isArray(classes) && classes.includes('katex')
}

function percorrer(no: No) {
  const filhos = no.children
  if (!filhos) return
  for (let i = 0; i < filhos.length - 1; i++) {
    const seguinte = filhos[i + 1]
    if (!ehFormula(filhos[i]) || seguinte.type !== 'text') continue
    const pontuacao = seguinte.value?.match(PONTUACAO)?.[0]
    if (!pontuacao) continue
    seguinte.value = seguinte.value!.slice(pontuacao.length)
    filhos[i] = {
      type: 'element',
      tagName: 'span',
      properties: { style: 'white-space: nowrap', dataSemQuebra: true },
      children: [filhos[i], { type: 'text', value: pontuacao }],
    }
  }
  // não entra nas fórmulas (o KaTeX já cuida delas) nem nos embrulhos criados aqui
  for (const filho of filhos) {
    if (!ehFormula(filho) && !filho.properties?.dataSemQuebra) percorrer(filho)
  }
}

export function rehypeSemQuebra() {
  return (arvore: No) => percorrer(arvore)
}
