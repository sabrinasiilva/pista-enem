import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { App } from './App'
import { servidorFalso } from './testes/servidorFalso'

function abrirEm(hash: string) {
  window.location.hash = hash
  const usuario = userEvent.setup()
  render(<App />)
  return usuario
}

function contaPronta(servidor: ReturnType<typeof servidorFalso>, extras = {}) {
  servidor.contas.set('estudante_1', {
    usuario: { id: 'u1', apelido: 'estudante_1', meta_semanal: 5, habilidades_foco: [], tema: 'sistema', criado_em: '2026-11-01T00:00:00Z' },
    senha: 'girassol-azul-42',
    codigo: 'X',
    resultados: [],
    ...extras,
  })
}

async function entrar(usuario: ReturnType<typeof userEvent.setup>) {
  window.location.hash = '#/entrar'
  await usuario.type(await screen.findByLabelText('Apelido'), 'estudante_1')
  await usuario.type(screen.getByLabelText('Senha'), 'girassol-azul-42')
  await usuario.click(screen.getByRole('button', { name: 'Entrar' }))
  await screen.findByRole('heading', { name: 'Oi, estudante_1!' })
}

describe('menu', () => {
  it('marca a página atual e abre e fecha no celular', async () => {
    servidorFalso()
    const usuario = abrirEm('#/progresso')
    const [menuDoComputador] = screen.getAllByRole('navigation', { name: 'Menu principal' })
    expect(within(menuDoComputador).getByRole('link', { name: 'Meu progresso' })).toHaveAttribute('aria-current', 'page')

    await usuario.click(screen.getByRole('button', { name: 'Abrir menu' }))
    expect(screen.getByRole('dialog', { name: 'Menu' })).toBeInTheDocument()
    await usuario.keyboard('{Escape}')
    expect(screen.queryByRole('dialog', { name: 'Menu' })).not.toBeInTheDocument()
  })

  it('sem conta, progresso e revisão convidam a criar conta', async () => {
    servidorFalso()
    abrirEm('#/revisar')
    expect((await screen.findAllByRole('link', { name: 'Criar conta' })).length).toBeGreaterThan(1)
    expect(screen.getByText(/questões que você errou ficam guardadas/)).toBeInTheDocument()
  })
})

describe('tema', () => {
  it('troca entre claro, escuro e automático e guarda a escolha', async () => {
    servidorFalso()
    const usuario = abrirEm('#/configuracoes')
    await usuario.click(await screen.findByRole('radio', { name: 'Escuro' }))
    expect(document.documentElement).toHaveClass('dark')
    expect(localStorage.getItem('pista:tema')).toBe('escuro')
    await usuario.click(screen.getByRole('radio', { name: 'Claro' }))
    expect(document.documentElement).not.toHaveClass('dark')
    expect(screen.getByRole('radio', { name: 'Claro' })).toHaveAttribute('aria-checked', 'true')
  })

  it('com conta, o tema vai para o perfil', async () => {
    const servidor = servidorFalso()
    contaPronta(servidor)
    const usuario = abrirEm('#/')
    await entrar(usuario)
    window.location.hash = '#/configuracoes'
    await usuario.click(await screen.findByRole('radio', { name: 'Escuro' }))
    await waitFor(() => expect(servidor.contas.get('estudante_1')!.usuario.tema).toBe('escuro'))
  })
})

describe('modo foco', () => {
  it('monta a fila, passa pelas questões e mostra o resumo', async () => {
    servidorFalso()
    const usuario = abrirEm('#/foco')
    await usuario.click(await screen.findByRole('radio', { name: '5' }))
    await usuario.click(screen.getByRole('radio', { name: 'Livre' }))
    await usuario.click(screen.getByRole('button', { name: 'Começar' }))

    expect(await screen.findByText('Questão 1 de 2')).toBeInTheDocument()
    expect(screen.getByRole('timer')).toBeInTheDocument()
    await usuario.click(await screen.findByRole('radio', { name: /^E\)/ }))
    await usuario.click(screen.getByRole('button', { name: 'Responder' }))
    await usuario.click(await screen.findByRole('button', { name: 'Próxima questão' }))

    expect(await screen.findByText('Questão 2 de 2')).toBeInTheDocument()
    await usuario.click(await screen.findByRole('radio', { name: /^A\)/ }))
    await usuario.click(screen.getByRole('button', { name: 'Responder' }))
    await screen.findByText(/Pista 1 de 2/)
    await usuario.click(screen.getByRole('button', { name: 'Encerrar' }))

    expect(await screen.findByRole('heading', { name: 'Foco concluído' })).toBeInTheDocument()
    expect(screen.getByText(/resolveu 1 de 2 questões/)).toBeInTheDocument()
    expect(screen.getByText('Acertou de primeira')).toBeInTheDocument()
    expect(screen.getByText('Não feita')).toBeInTheDocument()

    await usuario.click(screen.getByRole('button', { name: 'Novo foco' }))
    expect(screen.getByRole('heading', { name: 'Modo foco' })).toBeInTheDocument()
  })
})

describe('progresso, revisão e perfil', () => {
  it('depois de errar, a questão aparece no progresso e na revisão', async () => {
    const servidor = servidorFalso()
    contaPronta(servidor)
    const usuario = abrirEm('#/')
    await entrar(usuario)

    window.location.hash = '#/questao/2022-141'
    await usuario.click(await screen.findByRole('radio', { name: /^A\)/ }))
    await usuario.click(screen.getByRole('button', { name: 'Responder' }))
    await usuario.click(await screen.findByRole('radio', { name: /^E\)/ }))
    await usuario.click(screen.getByRole('button', { name: 'Responder' }))
    await screen.findByText(/Você acertou! A resposta/)

    window.location.hash = '#/progresso'
    expect(await screen.findByText('1 de 5 questões')).toBeInTheDocument()
    expect(screen.getByText('Acertou na 2ª tentativa')).toBeInTheDocument()

    window.location.hash = '#/revisar'
    expect(await screen.findByRole('link', { name: /Refazer a questão 141/ })).toBeInTheDocument()
  })

  it('apagar a conta pede a senha e sai', async () => {
    const servidor = servidorFalso()
    contaPronta(servidor)
    const usuario = abrirEm('#/')
    await entrar(usuario)
    window.location.hash = '#/perfil'
    await usuario.click(await screen.findByRole('button', { name: 'Quero apagar minha conta' }))
    await usuario.type(screen.getByLabelText('Digite sua senha para confirmar'), 'errada!!')
    await usuario.click(screen.getByRole('button', { name: 'Apagar para sempre' }))
    expect(await screen.findByText('A senha está incorreta.')).toBeInTheDocument()

    await usuario.clear(screen.getByLabelText('Digite sua senha para confirmar'))
    await usuario.type(screen.getByLabelText('Digite sua senha para confirmar'), 'girassol-azul-42')
    await usuario.click(screen.getByRole('button', { name: 'Apagar para sempre' }))
    await waitFor(() => expect(servidor.contas.has('estudante_1')).toBe(false))
    expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent('Aprenda com o seu erro')
  })
})
