import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { servidorFalso } from '../testes/servidorFalso'
import { PaginaInicial } from './PaginaInicial'

describe('PaginaInicial', () => {
  it('explica o Pista e lista as questões agrupadas por ano', async () => {
    servidorFalso()
    render(<PaginaInicial />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Aprenda com o seu erro')
    expect(await screen.findByRole('heading', { name: 'ENEM 2022' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'ENEM 2023' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Questão 141 do ENEM 2022' })).toHaveAttribute('href', '#/questao/2022-141')
  })

  it('o botão de começar leva a uma questão', async () => {
    servidorFalso()
    const usuario = userEvent.setup()
    render(<PaginaInicial />)
    const botao = await screen.findByRole('button', { name: /questão aleatória/ })
    await screen.findByRole('heading', { name: 'ENEM 2022' })
    await usuario.click(botao)
    expect(window.location.hash).toMatch(/^#\/questao\/20\d\d-\d+$/)
  })

  it('avisa quando o tutor está no modo básico', async () => {
    servidorFalso({ iaDesativada: true })
    render(<PaginaInicial />)
    expect(await screen.findByText(/modo básico/)).toBeInTheDocument()
  })

  it('mostra erro com opção de tentar de novo', async () => {
    servidorFalso({ semConexao: true })
    render(<PaginaInicial />)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Tentar de novo' })).toBeInTheDocument()
  })
})
