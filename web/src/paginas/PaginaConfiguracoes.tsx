import { Monitor, Moon, Sun } from 'lucide-react'
import { api } from '../api'
import { Cartao, Pagina } from '../componentes/ui'
import { useConta } from '../conta'
import { endereco } from '../rotas'
import { useTema } from '../tema'
import type { Tema } from '../tipos'

const TEMAS: { valor: Tema; rotulo: string; icone: typeof Sun }[] = [
  { valor: 'claro', rotulo: 'Claro', icone: Sun },
  { valor: 'escuro', rotulo: 'Escuro', icone: Moon },
  { valor: 'sistema', rotulo: 'Automático', icone: Monitor },
]

export function PaginaConfiguracoes() {
  const { tema, escolherTema } = useTema()
  const { usuario, atualizar } = useConta()

  const trocar = (novo: Tema) => {
    escolherTema(novo)
    // com conta, o tema vai junto para os outros aparelhos
    if (usuario) api.atualizarPerfil({ tema: novo }).then(atualizar).catch(() => {})
  }

  return (
    <Pagina titulo="Configurações">
      <Cartao titulo="Tema">
        <div role="radiogroup" aria-label="Tema" className="grid grid-cols-3 gap-3">
          {TEMAS.map(({ valor, rotulo, icone: Icone }) => (
            <button
              key={valor}
              type="button"
              role="radio"
              aria-checked={tema === valor}
              onClick={() => trocar(valor)}
              className={`flex flex-col items-center gap-2 rounded-xl border p-4 text-sm font-medium transition ${
                tema === valor ? 'border-stone-900 ring-1 ring-stone-900' : 'border-stone-200 hover:border-stone-400'
              }`}
            >
              <Icone className="size-6" aria-hidden />
              {rotulo}
            </button>
          ))}
        </div>
        <p className="mt-3 text-sm text-stone-500">O automático segue o tema do seu celular ou computador.</p>
      </Cartao>

      <Cartao titulo="Privacidade">
        <ul className="list-disc space-y-2 pl-5 text-sm text-stone-600">
          <li>O Pista não pede nome, e-mail, idade nem qualquer dado pessoal.</li>
          <li>Sem conta, nada fica salvo: o progresso some quando você fecha a aba.</li>
          <li>Com conta, ficam guardados só o apelido, a meta, as áreas em foco, o tema e as questões resolvidas.</li>
          <li>As mensagens para o tutor são processadas por uma IA do Google. Não escreva dados pessoais nelas.</li>
          <li>
            Você pode apagar sua conta e todo o histórico a qualquer momento no{' '}
            <a href={endereco({ pagina: 'perfil' })} className="font-semibold text-stone-900 underline-offset-4 hover:underline">
              perfil
            </a>
            .
          </li>
        </ul>
      </Cartao>

      <Cartao titulo="Sobre">
        <p className="text-sm text-stone-600">
          O Pista é um projeto de código aberto que usa questões oficiais do ENEM, publicadas pelo Inep.{' '}
          <a
            href="https://github.com/sabrinasiilva/pista-enem"
            target="_blank"
            rel="noreferrer"
            className="font-semibold text-stone-900 underline-offset-4 hover:underline"
          >
            Ver o código no GitHub
          </a>
          .
        </p>
      </Cartao>
    </Pagina>
  )
}
