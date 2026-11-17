import { type FormEvent, useState } from 'react'
import { api, ErroDaApi } from '../api'
import { areasEmFoco, habilidadesDasAreas } from '../areas'
import { CaixaDeErro, Carregando } from '../componentes/Avisos'
import { SeletorDeAreas } from '../componentes/SeletorDeAreas'
import { Botao, Campo, Cartao, ExigeConta, Pagina } from '../componentes/ui'
import { useConta } from '../conta'
import { irPara } from '../rotas'
import { problemaNaSenha } from './PaginaCriarConta'

function mensagemDe(erro: unknown, padrao: string) {
  return erro instanceof ErroDaApi ? erro.message : padrao
}

function Foco() {
  const { usuario, atualizar } = useConta()
  const [meta, setMeta] = useState(usuario?.meta_semanal ?? 10)
  const [areas, setAreas] = useState(() => areasEmFoco(usuario?.habilidades_foco ?? []))
  const [estado, setEstado] = useState<'parado' | 'salvando' | 'salvo'>('parado')
  const [erro, setErro] = useState<string | null>(null)

  const salvar = async (evento: FormEvent) => {
    evento.preventDefault()
    setEstado('salvando')
    setErro(null)
    try {
      atualizar(await api.atualizarPerfil({ meta_semanal: meta, habilidades_foco: habilidadesDasAreas(areas) }))
      setEstado('salvo')
    } catch (e) {
      setErro(mensagemDe(e, 'Não consegui salvar.'))
      setEstado('parado')
    }
  }

  return (
    <Cartao titulo="Meta e foco">
      <form onSubmit={salvar} className="space-y-5">
        <Campo
          rotulo="Questões por semana"
          type="number"
          min={1}
          max={200}
          value={meta}
          onChange={(e) => {
            setMeta(Number(e.target.value))
            setEstado('parado')
          }}
        />
        <div>
          <p className="text-sm font-medium">Áreas em foco</p>
          <div className="mt-2">
            <SeletorDeAreas
              selecionadas={areas}
              aoMudar={(novas) => {
                setAreas(novas)
                setEstado('parado')
              }}
            />
          </div>
        </div>
        {erro && <CaixaDeErro mensagem={erro} />}
        <div className="flex items-center gap-3">
          <Botao type="submit" carregando={estado === 'salvando'}>
            Salvar
          </Botao>
          {estado === 'salvo' && <span role="status" className="text-sm text-emerald-600">Salvo.</span>}
        </div>
      </form>
    </Cartao>
  )
}

function TrocarSenha() {
  const { usuario } = useConta()
  const [atual, setAtual] = useState('')
  const [nova, setNova] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [estado, setEstado] = useState<'parado' | 'salvando' | 'salvo'>('parado')
  const erroNova = problemaNaSenha(nova, usuario?.apelido ?? '')

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault()
    setErro(null)
    setEstado('salvando')
    try {
      await api.trocarSenha(atual, nova)
      setAtual('')
      setNova('')
      setEstado('salvo')
    } catch (e) {
      setErro(mensagemDe(e, 'Não consegui trocar a senha.'))
      setEstado('parado')
    }
  }

  return (
    <Cartao titulo="Trocar senha">
      <form onSubmit={enviar} className="space-y-4">
        <Campo rotulo="Senha atual" type="password" value={atual} onChange={(e) => setAtual(e.target.value)} autoComplete="current-password" required />
        <Campo
          rotulo="Nova senha"
          type="password"
          value={nova}
          onChange={(e) => setNova(e.target.value)}
          autoComplete="new-password"
          ajuda="Os outros aparelhos em que você entrou serão desconectados."
          erro={erroNova}
          required
        />
        {erro && <CaixaDeErro mensagem={erro} />}
        <div className="flex items-center gap-3">
          <Botao type="submit" variante="secundario" carregando={estado === 'salvando'} disabled={Boolean(erroNova)}>
            Trocar senha
          </Botao>
          {estado === 'salvo' && <span role="status" className="text-sm text-emerald-600">Senha trocada.</span>}
        </div>
      </form>
    </Cartao>
  )
}

function ApagarConta() {
  const { sair } = useConta()
  const [abrir, setAbrir] = useState(false)
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [apagando, setApagando] = useState(false)

  const apagar = async (evento: FormEvent) => {
    evento.preventDefault()
    setErro(null)
    setApagando(true)
    try {
      await api.apagarConta(senha)
      await sair()
      irPara({ pagina: 'inicio' })
    } catch (e) {
      setErro(mensagemDe(e, 'Não consegui apagar a conta.'))
      setApagando(false)
    }
  }

  return (
    <section className="rounded-2xl border border-red-200 bg-white p-5 sm:p-6">
      <h2 className="text-lg font-semibold text-red-700">Apagar conta</h2>
      <p className="mt-2 text-sm text-stone-600">
        Apaga a conta e todo o histórico de questões. Não dá para desfazer.
      </p>
      {!abrir ? (
        <Botao variante="secundario" onClick={() => setAbrir(true)} className="mt-4">
          Quero apagar minha conta
        </Botao>
      ) : (
        <form onSubmit={apagar} className="mt-4 space-y-4">
          <Campo
            rotulo="Digite sua senha para confirmar"
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            autoComplete="current-password"
            required
          />
          {erro && <CaixaDeErro mensagem={erro} />}
          <div className="flex flex-wrap gap-3">
            <Botao type="submit" variante="perigo" carregando={apagando}>
              Apagar para sempre
            </Botao>
            <Botao variante="fantasma" onClick={() => setAbrir(false)}>
              Cancelar
            </Botao>
          </div>
        </form>
      )}
    </section>
  )
}

export function PaginaPerfil() {
  const { usuario, carregando } = useConta()
  if (carregando) return <Carregando />
  if (!usuario) {
    return (
      <Pagina titulo="Perfil">
        <ExigeConta motivo="Entre ou crie uma conta para ver seu perfil." />
      </Pagina>
    )
  }

  const desde = new Date(usuario.criado_em).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })
  return (
    <Pagina titulo="Perfil">
      <div className="flex items-center gap-4">
        <span aria-hidden className="flex size-14 items-center justify-center rounded-full bg-amber-500 text-2xl font-bold uppercase text-white">
          {usuario.apelido[0]}
        </span>
        <div>
          <p className="text-xl font-semibold">{usuario.apelido}</p>
          <p className="text-sm text-stone-500">Estudando com o Pista desde {desde}</p>
        </div>
      </div>
      <Foco />
      <TrocarSenha />
      <ApagarConta />
    </Pagina>
  )
}
