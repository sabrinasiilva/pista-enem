import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import { App } from '../App'
import { servidorFalso } from '../testes/servidorFalso'
import { apresentacaoJaVista, reverApresentacao } from './Apresentacao'

function abrirEm(hash: string) {
  window.location.hash = hash
  servidorFalso()
  const usuario = userEvent.setup()
  render(<App />)
  return usuario
}

/** Abre na página inicial e pula a tela de abertura com um toque. */
async function abrirNaApresentacao() {
  const usuario = abrirEm('')
  await usuario.click(screen.getByRole('dialog', { name: 'Pista, tutor para o ENEM' }))
  return usuario
}

describe('Apresentacao', () => {
  beforeEach(() => reverApresentacao())

  it('aparece na primeira visita e passa pelas quatro telas', async () => {
    const usuario = await abrirNaApresentacao()
    const dialogo = screen.getByRole('dialog', { name: 'Aprenda a resolver, não a decorar' })
    expect(dialogo).toBeInTheDocument()
    expect(screen.getByText('Tela 1 de 4')).toBeInTheDocument()

    for (let i = 0; i < 3; i++) await usuario.click(screen.getByRole('button', { name: 'Continuar' }))
    expect(screen.getByRole('dialog', { name: 'No seu ritmo, sem dados pessoais' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Pular' })).not.toBeInTheDocument()

    await usuario.click(screen.getByRole('button', { name: 'Começar a praticar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(apresentacaoJaVista()).toBe(true)
  })

  it('pode ser pulada e não volta na próxima visita', async () => {
    const usuario = await abrirNaApresentacao()
    await usuario.click(screen.getByRole('button', { name: 'Pular' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(apresentacaoJaVista()).toBe(true)
  })

  it('anda com as setas do teclado e fecha com Esc', async () => {
    const usuario = await abrirNaApresentacao()
    await usuario.keyboard('{ArrowRight}')
    expect(screen.getByRole('dialog', { name: 'Errou? É aí que a mágica acontece' })).toBeInTheDocument()
    await usuario.keyboard('{ArrowLeft}')
    expect(screen.getByRole('dialog', { name: 'Aprenda a resolver, não a decorar' })).toBeInTheDocument()
    await usuario.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('na última tela, leva para criar conta', async () => {
    const usuario = await abrirNaApresentacao()
    for (let i = 0; i < 3; i++) await usuario.click(screen.getByRole('button', { name: 'Continuar' }))
    await usuario.click(screen.getByRole('button', { name: 'Criar uma conta (opcional)' }))
    expect(window.location.hash).toBe('#/criar-conta')
  })

  it('a tela de abertura some sozinha e leva para a apresentação', async () => {
    abrirEm('')
    expect(screen.getByText('Seu tutor para o ENEM')).toBeInTheDocument()
    expect(await screen.findByRole('dialog', { name: 'Aprenda a resolver, não a decorar' })).toBeInTheDocument()
  })

  it('não aparece para quem chega por um link direto de questão', () => {
    abrirEm('#/questao/2099-140')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
