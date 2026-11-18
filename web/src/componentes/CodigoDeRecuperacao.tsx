import { Check, Copy, Download, KeyRound } from 'lucide-react'
import { useState } from 'react'
import { Botao } from './ui'

/** Mostra o código de recuperação uma única vez e só libera seguir quando o aluno confirma que guardou. */
export function CodigoDeRecuperacao({ apelido, codigo, aoConcluir }: { apelido: string; codigo: string; aoConcluir: () => void }) {
  const [copiado, setCopiado] = useState(false)
  const [guardou, setGuardou] = useState(false)

  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(codigo)
      setCopiado(true)
    } catch {
      setCopiado(false)
    }
  }

  const baixar = () => {
    const texto = `Pista: código de recuperação\n\nApelido: ${apelido}\nCódigo: ${codigo}\n\nUse este código para trocar a senha se esquecê-la. Ele só vale uma vez.\n`
    const arquivo = URL.createObjectURL(new Blob([texto], { type: 'text/plain;charset=utf-8' }))
    const link = Object.assign(document.createElement('a'), { href: arquivo, download: `pista-codigo-${apelido}.txt` })
    link.click()
    URL.revokeObjectURL(arquivo)
  }

  return (
    <div className="space-y-5">
      <div className="flex gap-3 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-amber-900">
        <KeyRound className="mt-0.5 size-5 shrink-0" aria-hidden />
        <p>
          Guarde este código. Como o Pista não pede e-mail, <strong>ele é o único jeito de recuperar a conta</strong> se
          você esquecer a senha. Ele só aparece agora.
        </p>
      </div>
      <p
        aria-label="Código de recuperação"
        className="select-all rounded-2xl border-2 border-dashed border-stone-300 bg-white py-5 text-center font-mono text-xl font-bold tracking-widest sm:text-2xl"
      >
        {codigo}
      </p>
      <div className="flex flex-wrap gap-3">
        <Botao variante="secundario" onClick={copiar}>
          {copiado ? <Check className="size-4" aria-hidden /> : <Copy className="size-4" aria-hidden />}
          {copiado ? 'Copiado' : 'Copiar'}
        </Botao>
        <Botao variante="secundario" onClick={baixar}>
          <Download className="size-4" aria-hidden />
          Baixar em arquivo
        </Botao>
      </div>
      <label className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={guardou}
          onChange={(evento) => setGuardou(evento.target.checked)}
          className="mt-1 size-4 accent-stone-900"
        />
        <span>Guardei meu código em um lugar seguro.</span>
      </label>
      <Botao onClick={aoConcluir} disabled={!guardou} className="w-full sm:w-auto">
        Continuar
      </Botao>
    </div>
  )
}
