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

const menu = () => screen.getAllByRole('navigation', { name: 'Menu principal' })[0]

async function preencherPassoUm(usuario: ReturnType<typeof userEvent.setup>, apelido = 'estudante_1') {
  await usuario.type(screen.getByLabelText('Apelido'), apelido)
  await usuario.type(screen.getByLabelText('Senha'), 'girassol-azul-42')
  await usuario.type(screen.getByLabelText('Confirme a senha'), 'girassol-azul-42')
  await usuario.click(screen.getByRole('button', { name: 'Continuar' }))
}

describe('criar conta', () => {
  it('passa pelos três passos e só entra depois de guardar o código', async () => {
    const servidor = servidorFalso()
    const usuario = abrirEm('#/criar-conta')

    await preencherPassoUm(usuario)
    expect(screen.getByText('Quantas questões por semana?')).toBeInTheDocument()
    await usuario.click(screen.getByRole('radio', { name: '20' }))
    await usuario.click(screen.getByRole('checkbox', { name: /Geometria/ }))
    await usuario.click(screen.getByRole('button', { name: 'Criar conta' }))

    expect(await screen.findByLabelText('Código de recuperação')).toHaveTextContent('ABCD-EFGH-JKMN-PQRS')
    const continuar = screen.getByRole('button', { name: 'Continuar' })
    expect(continuar).toBeDisabled()
    expect(localStorage.getItem('pista:token')).toBeNull() // ainda não entrou

    await usuario.click(screen.getByRole('checkbox', { name: /Guardei meu código/ }))
    await usuario.click(continuar)

    expect(await screen.findByRole('heading', { name: 'Oi, estudante_1!' })).toBeInTheDocument()
    expect(localStorage.getItem('pista:token')).not.toBeNull()
    const conta = servidor.contas.get('estudante_1')!
    expect(conta.usuario.meta_semanal).toBe(20)
    expect(conta.usuario.habilidades_foco).toEqual(['MT-H6', 'MT-H7', 'MT-H8', 'MT-H9'])
  })

  it('avisa sobre apelido com e-mail e senhas diferentes antes de enviar', async () => {
    servidorFalso()
    const usuario = abrirEm('#/criar-conta')
    await usuario.type(screen.getByLabelText('Apelido'), 'ana@email.com')
    expect(screen.getByText(/Não use e-mail/)).toBeInTheDocument()
    await usuario.type(screen.getByLabelText('Senha'), 'girassol-azul-42')
    await usuario.type(screen.getByLabelText('Confirme a senha'), 'outra-coisa-123')
    expect(screen.getByText('As senhas não são iguais.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Continuar' })).toBeDisabled()
  })

  it('apelido em uso volta para o primeiro passo com o aviso', async () => {
    const servidor = servidorFalso()
    servidor.contas.set('estudante_1', {
      usuario: { id: 'x', apelido: 'estudante_1', meta_semanal: 10, habilidades_foco: [], tema: 'sistema', criado_em: '' },
      senha: 'qualquer-coisa',
      codigo: 'X',
      resultados: [],
    })
    const usuario = abrirEm('#/criar-conta')
    await preencherPassoUm(usuario)
    await usuario.click(screen.getByRole('button', { name: 'Criar conta' }))
    expect(await screen.findByText(/já está em uso/)).toBeInTheDocument()
    expect(screen.getByLabelText('Apelido')).toBeInTheDocument()
  })
})

describe('entrar e sair', () => {
  it('mostra erro com senha errada, entra com a certa e sai pelo menu', async () => {
    const servidor = servidorFalso()
    servidor.contas.set('estudante_1', {
      usuario: { id: 'u1', apelido: 'estudante_1', meta_semanal: 10, habilidades_foco: [], tema: 'sistema', criado_em: '2026-11-01T00:00:00Z' },
      senha: 'girassol-azul-42',
      codigo: 'X',
      resultados: [],
    })
    const usuario = abrirEm('#/entrar')
    await usuario.type(screen.getByLabelText('Apelido'), 'estudante_1')
    await usuario.type(screen.getByLabelText('Senha'), 'errada-errada')
    await usuario.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Apelido ou senha incorretos.')

    await usuario.clear(screen.getByLabelText('Senha'))
    await usuario.type(screen.getByLabelText('Senha'), 'girassol-azul-42')
    await usuario.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('heading', { name: 'Oi, estudante_1!' })).toBeInTheDocument()

    await usuario.click(screen.getAllByRole('button', { name: 'Sair' })[0])
    await waitFor(() => expect(within(menu()).queryByText('estudante_1')).not.toBeInTheDocument())
    expect(localStorage.getItem('pista:token')).toBeNull()
  })

  it('token vencido é esquecido sem quebrar a página', async () => {
    servidorFalso()
    localStorage.setItem('pista:token', 'token-que-nao-existe')
    abrirEm('#/')
    expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent('Aprenda com o seu erro')
    await waitFor(() => expect(localStorage.getItem('pista:token')).toBeNull())
  })
})

describe('recuperar a conta', () => {
  it('troca a senha com o código e mostra um código novo', async () => {
    const servidor = servidorFalso()
    servidor.contas.set('estudante_1', {
      usuario: { id: 'u1', apelido: 'estudante_1', meta_semanal: 10, habilidades_foco: [], tema: 'sistema', criado_em: '' },
      senha: 'senha-esquecida',
      codigo: 'ABCD-EFGH-JKMN-PQRS',
      resultados: [],
    })
    const usuario = abrirEm('#/recuperar')
    await usuario.type(screen.getByLabelText('Apelido'), 'estudante_1')
    await usuario.type(screen.getByLabelText('Código de recuperação'), 'ABCD-EFGH-JKMN-PQRS')
    await usuario.type(screen.getByLabelText('Nova senha'), 'nova-senha-boa')
    await usuario.click(screen.getByRole('button', { name: 'Trocar a senha' }))
    expect(await screen.findByLabelText('Código de recuperação')).toHaveTextContent('NOVO-CODI-GODE-RECU')
    expect(servidor.contas.get('estudante_1')!.senha).toBe('nova-senha-boa')
  })
})
