import { Loader2, LogIn, UserPlus } from 'lucide-react'
import { type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode, useId } from 'react'
import { endereco } from '../rotas'

export function Pagina({ titulo, subtitulo, children, largura = 'max-w-3xl' }: {
  titulo: string
  subtitulo?: ReactNode
  children: ReactNode
  largura?: string
}) {
  return (
    <main className={`mx-auto ${largura} px-4 py-8 sm:py-10`}>
      <h1 className="text-3xl font-bold tracking-tight">{titulo}</h1>
      {subtitulo && <p className="mt-2 text-stone-600">{subtitulo}</p>}
      <div className="mt-8 space-y-6">{children}</div>
    </main>
  )
}

export function Cartao({ titulo, children, className = '' }: { titulo?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-2xl border border-stone-200 bg-white p-5 shadow-sm sm:p-6 ${className}`}>
      {titulo && <h2 className="mb-4 text-lg font-semibold">{titulo}</h2>}
      {children}
    </section>
  )
}

const VARIANTES = {
  primario: 'bg-stone-900 text-white shadow-sm hover:bg-stone-700 disabled:bg-stone-300 disabled:shadow-none',
  secundario: 'border border-stone-300 bg-white text-stone-900 hover:bg-stone-100 disabled:opacity-50',
  perigo: 'bg-red-600 text-white hover:bg-red-700 disabled:opacity-50',
  fantasma: 'text-stone-600 hover:bg-stone-100 hover:text-stone-900 disabled:opacity-50',
}

export function Botao({
  variante = 'primario',
  carregando = false,
  children,
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variante?: keyof typeof VARIANTES; carregando?: boolean }) {
  return (
    <button
      type="button"
      {...props}
      disabled={props.disabled || carregando}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 font-semibold transition ${VARIANTES[variante]} ${className}`}
    >
      {carregando && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  )
}

export function Campo({
  rotulo,
  ajuda,
  erro,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { rotulo: string; ajuda?: ReactNode; erro?: string | null }) {
  const id = useId()
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium">
        {rotulo}
      </label>
      <input
        id={id}
        {...props}
        aria-invalid={erro ? true : undefined}
        aria-describedby={ajuda || erro ? `${id}-ajuda` : undefined}
        className={`mt-1.5 w-full rounded-xl border bg-white px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-stone-900/20 ${
          erro ? 'border-red-400' : 'border-stone-300 focus:border-stone-900'
        }`}
      />
      {(ajuda || erro) && (
        <p id={`${id}-ajuda`} className={`mt-1.5 text-sm ${erro ? 'text-red-600' : 'text-stone-500'}`}>
          {erro || ajuda}
        </p>
      )}
    </div>
  )
}

/** Convite para criar conta, nas telas que dependem dela. */
export function ExigeConta({ motivo }: { motivo: string }) {
  return (
    <Cartao>
      <p className="text-stone-700">{motivo}</p>
      <p className="mt-2 text-sm text-stone-500">A conta é opcional e só pede um apelido e uma senha, sem e-mail.</p>
      <div className="mt-5 flex flex-wrap gap-3">
        <a
          href={endereco({ pagina: 'criar-conta' })}
          className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-4 py-2.5 font-semibold text-white hover:bg-stone-700"
        >
          <UserPlus className="size-4" aria-hidden />
          Criar conta
        </a>
        <a
          href={endereco({ pagina: 'entrar' })}
          className="inline-flex items-center gap-2 rounded-xl border border-stone-300 bg-white px-4 py-2.5 font-semibold hover:bg-stone-100"
        >
          <LogIn className="size-4" aria-hidden />
          Já tenho conta
        </a>
      </div>
    </Cartao>
  )
}

export function BarraDeProgresso({ valor, maximo, rotulo }: { valor: number; maximo: number; rotulo: string }) {
  const porcentagem = maximo > 0 ? Math.min(100, Math.round((valor / maximo) * 100)) : 0
  return (
    <div
      role="progressbar"
      aria-label={rotulo}
      aria-valuenow={valor}
      aria-valuemin={0}
      aria-valuemax={maximo}
      className="h-2.5 overflow-hidden rounded-full bg-stone-200"
    >
      <div
        className={`h-full rounded-full transition-all ${porcentagem >= 100 ? 'bg-emerald-500' : 'bg-amber-500'}`}
        style={{ width: `${porcentagem}%` }}
      />
    </div>
  )
}
