import { type FormEvent, useState } from 'react'
import { api, ErroDaApi } from '../api'
import { CaixaDeErro } from '../componentes/Avisos'
import { Botao, Campo } from '../componentes/ui'
import { useConta } from '../conta'
import { endereco, irPara } from '../rotas'

export function PaginaEntrar() {
  const { entrar } = useConta()
  const [apelido, setApelido] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      entrar(await api.entrar(apelido, senha))
      irPara({ pagina: 'inicio' })
    } catch (e) {
      setErro(e instanceof ErroDaApi ? e.message : 'Não consegui entrar. Tente de novo.')
      setEnviando(false)
    }
  }

  return (
    <main className="mx-auto flex max-w-md flex-col px-4 py-10 sm:py-16">
      <h1 className="text-3xl font-bold tracking-tight">Entrar</h1>
      <p className="mt-2 text-stone-600">Continue de onde parou: meta, progresso e questões para revisar.</p>
      <form onSubmit={enviar} className="mt-8 space-y-5 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
        <Campo rotulo="Apelido" value={apelido} onChange={(e) => setApelido(e.target.value)} autoComplete="username" required />
        <Campo
          rotulo="Senha"
          type="password"
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
          autoComplete="current-password"
          required
        />
        {erro && <CaixaDeErro mensagem={erro} />}
        <Botao type="submit" carregando={enviando} className="w-full">
          Entrar
        </Botao>
        <a href={endereco({ pagina: 'recuperar' })} className="block text-center text-sm text-stone-600 underline-offset-4 hover:underline">
          Esqueci minha senha
        </a>
      </form>
      <p className="mt-6 text-center text-sm text-stone-600">
        Ainda não tem conta?{' '}
        <a href={endereco({ pagina: 'criar-conta' })} className="font-semibold text-stone-900 underline-offset-4 hover:underline">
          Criar conta
        </a>
      </p>
    </main>
  )
}
