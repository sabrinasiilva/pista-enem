import { Check } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { api, ErroDaApi } from '../api'
import { habilidadesDasAreas } from '../areas'
import { CaixaDeErro } from '../componentes/Avisos'
import { CodigoDeRecuperacao } from '../componentes/CodigoDeRecuperacao'
import { SeletorDeAreas } from '../componentes/SeletorDeAreas'
import { Botao, Campo } from '../componentes/ui'
import { useConta } from '../conta'
import { endereco, irPara } from '../rotas'
import type { Acesso } from '../tipos'

const PASSOS = ['Acesso', 'Seu foco', 'Código de recuperação']
const METAS = [5, 10, 20, 30]
const APELIDO = /^[a-z0-9_.]{3,20}$/

/** Mesmas regras da API, para avisar antes de enviar. */
export function problemaNoApelido(apelido: string): string | null {
  if (!apelido) return null
  if (apelido.includes('@')) return 'Não use e-mail: o Pista não guarda dados pessoais.'
  if (!APELIDO.test(apelido.toLowerCase())) return 'Use de 3 a 20 caracteres: letras sem acento, números, ponto ou sublinhado.'
  return null
}

export function problemaNaSenha(senha: string, apelido: string): string | null {
  if (!senha) return null
  if (senha.length < 8) return 'Use pelo menos 8 caracteres.'
  if (apelido && senha.toLowerCase().includes(apelido.toLowerCase())) return 'A senha não pode conter o apelido.'
  return null
}

function Etapas({ atual }: { atual: number }) {
  return (
    <ol className="flex items-center gap-2" aria-label="Etapas do cadastro">
      {PASSOS.map((passo, indice) => {
        const feito = indice < atual
        const agora = indice === atual
        return (
          <li key={passo} aria-current={agora ? 'step' : undefined} className="flex flex-1 items-center gap-2">
            <span
              className={`flex size-7 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${
                agora ? 'bg-stone-900 text-white' : feito ? 'bg-emerald-500 text-white' : 'bg-stone-200 text-stone-500'
              }`}
            >
              {feito ? <Check className="size-4" aria-hidden /> : indice + 1}
            </span>
            <span className={`hidden text-sm sm:inline ${agora ? 'font-semibold' : 'text-stone-500'}`}>{passo}</span>
            {indice < PASSOS.length - 1 && <span aria-hidden className="h-px flex-1 bg-stone-200" />}
          </li>
        )
      })}
    </ol>
  )
}

export function PaginaCriarConta() {
  const { entrar } = useConta()
  const [passo, setPasso] = useState(0)
  const [apelido, setApelido] = useState('')
  const [senha, setSenha] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [meta, setMeta] = useState(10)
  const [areas, setAreas] = useState<string[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [acesso, setAcesso] = useState<Acesso | null>(null)

  const erroApelido = problemaNoApelido(apelido)
  const erroSenha = problemaNaSenha(senha, apelido)
  const erroConfirmacao = confirmacao && confirmacao !== senha ? 'As senhas não são iguais.' : null
  const passoUmPronto = apelido && senha && confirmacao && !erroApelido && !erroSenha && !erroConfirmacao

  const avancar = (evento: FormEvent) => {
    evento.preventDefault()
    if (passoUmPronto) setPasso(1)
  }

  const criar = async (evento: FormEvent) => {
    evento.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      const novo = await api.cadastrar({
        apelido: apelido.toLowerCase(),
        senha,
        meta_semanal: meta,
        habilidades_foco: habilidadesDasAreas(areas),
      })
      setAcesso(novo)
      setPasso(2)
    } catch (e) {
      if (e instanceof ErroDaApi && (e.codigo === 'apelido_em_uso' || e.codigo === 'senha_fraca' || e.codigo === 'apelido_invalido')) {
        setPasso(0) // o problema está no primeiro passo
      }
      setErro(e instanceof ErroDaApi ? e.message : 'Não consegui criar a conta. Tente de novo.')
    } finally {
      setEnviando(false)
    }
  }

  const concluir = () => {
    if (!acesso) return
    entrar(acesso) // só entra depois de confirmar que guardou o código
    irPara({ pagina: 'inicio' })
  }

  return (
    <main className="mx-auto max-w-xl px-4 py-10 sm:py-14">
      <h1 className="text-3xl font-bold tracking-tight">Criar conta</h1>
      <p className="mt-2 text-stone-600">Sem e-mail, sem nome: só um apelido e uma senha.</p>
      <div className="mt-8">
        <Etapas atual={passo} />
      </div>

      <div className="mt-6 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
        {passo === 0 && (
          <form onSubmit={avancar} className="space-y-5">
            <Campo
              rotulo="Apelido"
              value={apelido}
              onChange={(e) => setApelido(e.target.value)}
              autoComplete="username"
              ajuda="Não use seu nome verdadeiro. Ex.: estudante_2026"
              erro={erroApelido}
              required
            />
            <Campo
              rotulo="Senha"
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              autoComplete="new-password"
              ajuda="Pelo menos 8 caracteres. Uma frase curta é fácil de lembrar e difícil de adivinhar."
              erro={erroSenha}
              required
            />
            <Campo
              rotulo="Confirme a senha"
              type="password"
              value={confirmacao}
              onChange={(e) => setConfirmacao(e.target.value)}
              autoComplete="new-password"
              erro={erroConfirmacao}
              required
            />
            {erro && <CaixaDeErro mensagem={erro} />}
            <Botao type="submit" disabled={!passoUmPronto} className="w-full">
              Continuar
            </Botao>
          </form>
        )}

        {passo === 1 && (
          <form onSubmit={criar} className="space-y-6">
            <div>
              <h2 className="font-semibold">Quantas questões por semana?</h2>
              <p className="mt-1 text-sm text-stone-500">Dá para mudar depois no perfil.</p>
              <div role="radiogroup" aria-label="Meta semanal" className="mt-3 grid grid-cols-4 gap-2">
                {METAS.map((valor) => (
                  <button
                    key={valor}
                    type="button"
                    role="radio"
                    aria-checked={meta === valor}
                    onClick={() => setMeta(valor)}
                    className={`rounded-xl border py-3 font-semibold transition ${
                      meta === valor ? 'border-stone-900 bg-stone-900 text-white' : 'border-stone-200 hover:border-stone-400'
                    }`}
                  >
                    {valor}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <h2 className="font-semibold">Em que você quer focar?</h2>
              <p className="mt-1 text-sm text-stone-500">
                O modo foco começa pelas questões dessas áreas. Pode deixar em branco para ver de tudo.
              </p>
              <div className="mt-3">
                <SeletorDeAreas selecionadas={areas} aoMudar={setAreas} />
              </div>
            </div>
            {erro && <CaixaDeErro mensagem={erro} />}
            <div className="flex gap-3">
              <Botao variante="secundario" onClick={() => setPasso(0)}>
                Voltar
              </Botao>
              <Botao type="submit" carregando={enviando} className="flex-1">
                Criar conta
              </Botao>
            </div>
          </form>
        )}

        {passo === 2 && acesso?.codigo_de_recuperacao && (
          <CodigoDeRecuperacao apelido={acesso.usuario.apelido} codigo={acesso.codigo_de_recuperacao} aoConcluir={concluir} />
        )}
      </div>

      {passo < 2 && (
        <p className="mt-6 text-center text-sm text-stone-600">
          Já tem conta?{' '}
          <a href={endereco({ pagina: 'entrar' })} className="font-semibold text-stone-900 underline-offset-4 hover:underline">
            Entrar
          </a>
        </p>
      )}
    </main>
  )
}
