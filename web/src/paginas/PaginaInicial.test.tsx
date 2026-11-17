import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { renderizar } from '../testes/renderizar'
import { servidorFalso } from '../testes/servidorFalso'
import { PaginaInicial } from './PaginaInicial'

describe('PaginaInicial', () => {
  it('explica o Pista com um exemplo de pista', async () => {
    servidorFalso()
    renderizar(<PaginaInicial />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Aprenda com o seu erro')
    expect(screen.getByRole('figure', { name: /Exemplo de como o tutor responde/ })).toBeInTheDocument()
    expect(screen.getAllByRole('listitem').length).toBeGreaterThanOrEqual(3)
  })

  it('mostra as questões em abas por ano, começando pelo mais recente', async () => {
    servidorFalso()
    const usuario = userEvent.setup()
    renderizar(<PaginaInicial />)
    const aba2023 = await screen.findByRole('tab', { name: '2023' })
    expect(aba2023).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('link', { name: 'Questão 150 do ENEM 2023' })).toHaveAttribute('href', '#/questao/2023-150')
    expect(screen.queryByRole('link', { name: 'Questão 141 do ENEM 2022' })).not.toBeInTheDocument()

    await usuario.click(screen.getByRole('tab', { name: '2022' }))
    expect(screen.getByRole('link', { name: 'Questão 141 do ENEM 2022' })).toBeInTheDocument()
  })

  it('o botão de começar leva a uma questão', async () => {
    servidorFalso()
    const usuario = userEvent.setup()
    renderizar(<PaginaInicial />)
    await screen.findByRole('tab', { name: '2022' })
    await usuario.click(screen.getByRole('button', { name: /questão aleatória/ }))
    expect(window.location.hash).toMatch(/^#\/questao\/20\d\d-\d+$/)
  })

  it('avisa quando o tutor está no modo básico', async () => {
    servidorFalso({ iaDesativada: true })
    renderizar(<PaginaInicial />)
    expect(await screen.findByText(/modo básico/i)).toBeInTheDocument()
  })

  it('mostra erro com opção de tentar de novo', async () => {
    servidorFalso({ semConexao: true })
    renderizar(<PaginaInicial />)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Tentar de novo' })).toBeInTheDocument()
  })
})
