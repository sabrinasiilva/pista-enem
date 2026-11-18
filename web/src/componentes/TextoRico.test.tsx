import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { TextoRico } from './TextoRico'

describe('TextoRico', () => {
  it('renderiza fórmulas com KaTeX', () => {
    const { container } = render(<TextoRico texto="O volume é $\frac{4}{3}\pi r^3$." />)
    expect(container.querySelector('.katex')).not.toBeNull()
  })

  it('mostra o cifrão escapado como dinheiro, sem virar fórmula', () => {
    const { container } = render(<TextoRico texto="Custa R\$ 10,00 e o raio é $r$." />)
    expect(container.textContent).toContain('R$ 10,00')
    expect(container.querySelectorAll('.katex')).toHaveLength(1)
  })

  it('a pontuação logo depois da fórmula não vai sozinha para a linha de baixo', () => {
    const { container } = render(<TextoRico texto="As magnitudes $M_1$ e $M_2$, medidos." />)
    const juntos = container.querySelector('[data-sem-quebra]')
    expect(juntos).not.toBeNull()
    expect(juntos?.textContent?.endsWith(',')).toBe(true)
    expect(container.textContent).toContain(' medidos.')
  })

  it('quebra de linha simples vira quebra de linha (um passo por linha)', () => {
    const { container } = render(<TextoRico texto={'Passo 1.\nPasso 2.'} />)
    expect(container.querySelector('br')).not.toBeNull()
  })

  it('renderiza tabelas dentro de uma área que rola', () => {
    const { container } = render(<TextoRico texto={'| a | b |\n|---|---|\n| 1 | 2 |'} />)
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(container.querySelector('.tabela-rolavel table')).not.toBeNull()
  })

  it('abre links em outra aba sem passar a origem', () => {
    render(<TextoRico texto="[fonte](https://www.gov.br/inep)" />)
    const link = screen.getByRole('link', { name: 'fonte' })
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noreferrer noopener')
  })
})
