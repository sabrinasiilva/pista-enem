import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { renderizar } from '../testes/renderizar'
import { servidorFalso } from '../testes/servidorFalso'
import { PaginaQuestao } from './PaginaQuestao'

async function abrir(id = '2022-141') {
  const usuario = userEvent.setup()
  const tela = renderizar(<PaginaQuestao id={id} />)
  return { usuario, tela }
}

const destaque = () => screen.getByRole('complementary', { name: 'Última mensagem do tutor' })

async function responder(usuario: ReturnType<typeof userEvent.setup>, letra: string) {
  await usuario.click(screen.getByRole('radio', { name: new RegExp(`^${letra}\\)`) }))
  await usuario.click(screen.getByRole('button', { name: 'Responder' }))
}

describe('PaginaQuestao', () => {
  it('mostra enunciado com fórmulas, tabela, fonte e as cinco alternativas', async () => {
    servidorFalso()
    const { tela } = await abrir()
    expect(await screen.findByText(/ENEM 2022 · Questão 141/)).toBeInTheDocument()
    expect(tela.container.querySelector('.katex')).not.toBeNull()
    expect(screen.getByRole('table')).toBeInTheDocument()
    const figura = screen.getByRole('img', { name: /Dois docinhos lado a lado/ })
    expect(screen.queryByText(/\[\[figura/)).not.toBeInTheDocument()
    expect(figura).toHaveAttribute('src', expect.stringMatching(/\/questoes\/2022-141\/figuras\/1$/))
    expect(screen.getByRole('link', { name: /Prova oficial/ })).toHaveAttribute('href', expect.stringContaining('inep.gov.br'))
    expect(screen.getAllByRole('radio')).toHaveLength(5)
    expect(screen.getByText('Marque a alternativa que achar certa.')).toBeInTheDocument()
  })

  it('o botão Responder só funciona com uma alternativa marcada', async () => {
    servidorFalso()
    await abrir()
    expect(await screen.findByRole('button', { name: 'Responder' })).toBeDisabled()
  })

  it('ao errar, mostra a pista, avança o nível e bloqueia a alternativa tentada', async () => {
    servidorFalso()
    const { usuario } = await abrir()
    await screen.findAllByRole('radio')
    await responder(usuario, 'B')

    expect(await screen.findByText(/Pista 1 de 2/)).toBeInTheDocument()
    // a pista aparece em destaque perto das alternativas (e também no histórico da conversa)
    expect(destaque()).toHaveTextContent(/Pista para o estado pista_1/)
    expect(screen.getByRole('radio', { name: /^B\)/ })).toBeDisabled()
    expect(screen.getByRole('radio', { name: /^C\)/ })).toBeEnabled()
    expect(screen.queryByText(/alternativa correta/)).not.toBeInTheDocument()

    await responder(usuario, 'C')
    expect(await screen.findByText(/Pista 2 de 2/)).toBeInTheDocument()
  })

  it('mostra que o tutor está pensando enquanto a pista é gerada', async () => {
    servidorFalso({ atrasoDaResposta: 300 })
    const { usuario } = await abrir()
    await screen.findAllByRole('radio')
    await responder(usuario, 'B')
    expect(await screen.findByText('O tutor está pensando na sua pista…')).toBeInTheDocument()
    expect(await screen.findByText(/Pista 1 de 2/)).toBeInTheDocument()
    expect(screen.queryByText('O tutor está pensando na sua pista…')).not.toBeInTheDocument()
  })

  it('a explicação completa pede confirmação e revela a resposta', async () => {
    servidorFalso()
    const { usuario } = await abrir()
    await screen.findAllByRole('radio')
    expect(screen.queryByRole('button', { name: /explicação completa/ })).not.toBeInTheDocument()

    await responder(usuario, 'A')
    await usuario.click(await screen.findByRole('button', { name: /explicação completa/ }))
    const confirmacao = screen.getByRole('alertdialog')
    await usuario.click(within(confirmacao).getByRole('button', { name: 'Vou tentar mais uma vez' }))
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()

    await usuario.click(screen.getByRole('button', { name: /explicação completa/ }))
    await usuario.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Ver a explicação' }))

    expect(await screen.findByText(/A resposta é a alternativa E/)).toBeInTheDocument()
    expect(destaque()).toHaveTextContent(/24 porções/)
    expect(screen.getByRole('radio', { name: /^E\).*alternativa correta/ })).toBeDisabled()
    expect(screen.queryByRole('button', { name: 'Responder' })).not.toBeInTheDocument()
  })

  it('ao acertar, parabeniza e oferece outra questão', async () => {
    servidorFalso()
    const { usuario } = await abrir()
    await screen.findAllByRole('radio')
    await responder(usuario, 'E')
    expect(await screen.findByText(/Você acertou! A resposta é a alternativa E/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Outra questão' })).toBeInTheDocument()
    const parecidas = await screen.findByRole('navigation', { name: 'Praticar o mesmo assunto' })
    expect(parecidas).toHaveTextContent('ENEM 2023 · Questão 150')
    expect(parecidas).not.toHaveTextContent('Questão 105')
  })

  it('a conversa mostra a resposta do tutor chegando em trechos', async () => {
    servidorFalso({ respostaDoTutor: 'O que acontece com o volume quando o diâmetro dobra?' })
    const { usuario } = await abrir()
    await usuario.type(await screen.findByLabelText('Sua mensagem para o tutor'), 'não sei começar{Enter}')
    const conversa = screen.getByRole('region', { name: 'Conversa com o tutor' })
    expect(await within(conversa).findByText('O que acontece com o volume quando o diâmetro dobra?')).toBeInTheDocument()
    expect(within(conversa).getByText('não sei começar')).toBeInTheDocument()
    expect(destaque()).toHaveTextContent('O que acontece com o volume quando o diâmetro dobra?')
    expect(screen.getByLabelText('Sua mensagem para o tutor')).toHaveValue('')
  })

  it('avisa para não escrever dados pessoais', async () => {
    servidorFalso()
    await abrir()
    expect(await screen.findByText(/Não escreva dados pessoais/)).toBeInTheDocument()
  })

  it('sem conexão, mostra o erro e deixa tentar de novo', async () => {
    const servidor = servidorFalso({ semConexao: true })
    const { usuario } = await abrir()
    expect(await screen.findByRole('alert')).toHaveTextContent(/Não consegui falar com o servidor/)
    servidor.religar()
    await usuario.click(screen.getByRole('button', { name: 'Tentar de novo' }))
    expect(await screen.findByText(/ENEM 2022 · Questão 141/)).toBeInTheDocument()
  })

  it('questão inexistente mostra uma mensagem clara', async () => {
    servidorFalso()
    await abrir('1999-999')
    expect(await screen.findByRole('alert')).toHaveTextContent('Essa questão não existe ou saiu do banco.')
  })

  it('retoma a sessão da aba ao recarregar a página', async () => {
    const servidor = servidorFalso()
    const { usuario, tela } = await abrir()
    await screen.findAllByRole('radio')
    await responder(usuario, 'B')
    await screen.findByText(/Pista 1 de 2/)
    tela.unmount()

    servidor.fetch.mockClear()
    await abrir()
    expect(await screen.findByText(/Pista 1 de 2/)).toBeInTheDocument()
    const criouOutra = servidor.fetch.mock.calls.some(([, init]) => init?.method === 'POST')
    expect(criouOutra).toBe(false)
  })

  it('voltar a uma questão já terminada começa uma tentativa nova', async () => {
    const servidor = servidorFalso()
    const { usuario, tela } = await abrir()
    await screen.findAllByRole('radio')
    await responder(usuario, 'E')
    await screen.findByText(/Você acertou! A resposta/)
    tela.unmount()

    servidor.fetch.mockClear()
    await abrir()
    expect(await screen.findByText('Marque a alternativa que achar certa.')).toBeInTheDocument()
    expect(servidor.fetch.mock.calls.some(([endereco, init]) => endereco.endsWith('/sessoes') && init?.method === 'POST')).toBe(true)
  })

  it('mostra o aviso de modo básico quando a IA está desativada', async () => {
    servidorFalso({ iaDesativada: true })
    await abrir()
    await waitFor(() => expect(screen.getByText(/modo básico/i)).toBeInTheDocument())
  })
})
