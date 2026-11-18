import { type FormEvent, useState } from 'react'
import { api, ErroDaApi } from '../api'
import { CaixaDeErro } from '../componentes/Avisos'
import { CodigoDeRecuperacao } from '../componentes/CodigoDeRecuperacao'
import { Botao, Campo } from '../componentes/ui'
import { useConta } from '../conta'
import { endereco, irPara } from '../rotas'
import type { Acesso } from '../tipos'
import { problemaNaSenha } from './PaginaCriarConta'

export function PaginaRecuperar() {
  const { entrar } = useConta()
  const [apelido, setApelido] = useState('')
  const [codigo, setCodigo] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [acesso, setAcesso] = useState<Acesso | null>(null)

  const erroSenha = problemaNaSenha(senha, apelido)

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      setAcesso(await api.recuperar(apelido, codigo, senha))
    } catch (e) {
      setErro(e instanceof ErroDaApi ? e.message : 'Não consegui recuperar a conta. Tente de novo.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="mx-auto max-w-md px-4 py-10 sm:py-16">
      <h1 className="text-3xl font-bold tracking-tight">Recuperar a conta</h1>
      {acesso?.codigo_de_recuperacao ? (
        <>
          <p className="mt-2 text-stone-600">Senha trocada. O código antigo deixou de valer; este é o novo.</p>
          <div className="mt-8 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
            <CodigoDeRecuperacao
              apelido={acesso.usuario.apelido}
              codigo={acesso.codigo_de_recuperacao}
              aoConcluir={() => {
                entrar(acesso)
                irPara({ pagina: 'inicio' })
              }}
            />
          </div>
        </>
      ) : (
        <>
          <p className="mt-2 text-stone-600">Use o código de recuperação que apareceu quando você criou a conta.</p>
          <form onSubmit={enviar} className="mt-8 space-y-5 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
            <Campo rotulo="Apelido" value={apelido} onChange={(e) => setApelido(e.target.value)} autoComplete="username" required />
            <Campo
              rotulo="Código de recuperação"
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              placeholder="XXXX-XXXX-XXXX-XXXX"
              autoComplete="off"
              spellCheck={false}
              required
            />
            <Campo
              rotulo="Nova senha"
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              autoComplete="new-password"
              erro={erroSenha}
              required
            />
            {erro && <CaixaDeErro mensagem={erro} />}
            <Botao type="submit" carregando={enviando} disabled={Boolean(erroSenha)} className="w-full">
              Trocar a senha
            </Botao>
          </form>
          <p className="mt-6 text-sm text-stone-500">
            Perdeu também o código? Sem e-mail, não há como provar que a conta é sua. Você pode{' '}
            <a href={endereco({ pagina: 'criar-conta' })} className="font-semibold text-stone-900 underline-offset-4 hover:underline">
              criar outra conta
            </a>
            .
          </p>
        </>
      )}
    </main>
  )
}
