import { CheckCircle2, Flame, ListChecks, Target } from 'lucide-react'
import { type ReactNode, useCallback, useEffect, useState } from 'react'
import { api, ErroDaApi } from '../api'
import { areaDaHabilidade } from '../areas'
import { CaixaDeErro, Carregando } from '../componentes/Avisos'
import { BarraDeProgresso, Cartao, ExigeConta, Pagina } from '../componentes/ui'
import { useConta } from '../conta'
import { endereco } from '../rotas'
import type { Progresso, ResultadoDaQuestao } from '../tipos'

function Numero({ icone, valor, rotulo }: { icone: ReactNode; valor: ReactNode; rotulo: string }) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
      <div className="text-stone-400">{icone}</div>
      <p className="mt-2 text-2xl font-bold">{valor}</p>
      <p className="text-sm text-stone-500">{rotulo}</p>
    </div>
  )
}

export function descreverResultado(resultado: ResultadoDaQuestao): string {
  if (resultado.acertou_de_primeira) return 'Acertou de primeira'
  if (resultado.acertou) return `Acertou na ${resultado.tentativas}ª tentativa`
  return 'Viu a explicação'
}

export function PaginaProgresso() {
  const { usuario, carregando } = useConta()
  const [progresso, setProgresso] = useState<Progresso | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  const carregar = useCallback(async () => {
    setErro(null)
    try {
      setProgresso(await api.progresso())
    } catch (e) {
      setErro(e instanceof ErroDaApi ? e.message : 'Não consegui carregar o progresso.')
    }
  }, [])

  useEffect(() => {
    if (usuario) void carregar()
  }, [usuario, carregar])

  if (carregando) return <Carregando />
  if (!usuario) {
    return (
      <Pagina titulo="Meu progresso">
        <ExigeConta motivo="Com uma conta, o Pista guarda as questões que você resolveu e mostra sua evolução por assunto." />
      </Pagina>
    )
  }

  return (
    <Pagina titulo="Meu progresso" subtitulo="Como você está indo, por semana e por assunto." largura="max-w-4xl">
      {erro && <CaixaDeErro mensagem={erro} aoTentarDeNovo={carregar} />}
      {!erro && !progresso && <Carregando />}
      {progresso && (
        <>
          <Cartao>
            <div className="flex items-baseline justify-between gap-3">
              <h2 className="text-lg font-semibold">Meta da semana</h2>
              <span className="text-sm text-stone-500">
                {progresso.feitas_na_semana} de {progresso.meta_semanal} questões
              </span>
            </div>
            <div className="mt-3">
              <BarraDeProgresso valor={progresso.feitas_na_semana} maximo={progresso.meta_semanal} rotulo="Meta da semana" />
            </div>
            <p className="mt-3 text-sm text-stone-600">
              {progresso.feitas_na_semana >= progresso.meta_semanal
                ? 'Meta cumprida! Tudo o que vier agora é bônus.'
                : `Faltam ${progresso.meta_semanal - progresso.feitas_na_semana} para bater a meta (a semana vira na segunda).`}
            </p>
          </Cartao>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Numero icone={<Flame className="size-5 text-amber-500" />} valor={progresso.sequencia_de_dias} rotulo="dias seguidos" />
            <Numero icone={<ListChecks className="size-5" />} valor={progresso.total_de_questoes} rotulo="questões resolvidas" />
            <Numero
              icone={<CheckCircle2 className="size-5 text-emerald-500" />}
              valor={progresso.acertos_de_primeira}
              rotulo="acertos de primeira"
            />
            <Numero
              icone={<Target className="size-5" />}
              valor={
                progresso.total_de_questoes
                  ? `${Math.round((progresso.acertos_de_primeira / progresso.total_de_questoes) * 100)}%`
                  : '—'
              }
              rotulo="de aproveitamento"
            />
          </div>

          <Cartao titulo="Por assunto">
            {progresso.por_habilidade.length === 0 ? (
              <p className="text-stone-500">
                Resolva algumas questões para ver aqui em quais assuntos você vai melhor.{' '}
                <a href={endereco({ pagina: 'foco' })} className="font-semibold text-stone-900 underline-offset-4 hover:underline">
                  Começar um foco
                </a>
              </p>
            ) : (
              <ul className="space-y-4">
                {progresso.por_habilidade.map((habilidade) => (
                  <li key={habilidade.codigo}>
                    <div className="flex items-baseline justify-between gap-3 text-sm">
                      <span className="font-medium">
                        {areaDaHabilidade(habilidade.codigo)?.nome ?? 'Outro assunto'}{' '}
                        <span className="text-stone-400">· {habilidade.codigo}</span>
                      </span>
                      <span className="shrink-0 text-stone-500">
                        {habilidade.acertos_de_primeira}/{habilidade.feitas} de primeira
                      </span>
                    </div>
                    <p className="mt-0.5 text-xs text-stone-500">{habilidade.descricao}</p>
                    <div className="mt-2">
                      <BarraDeProgresso
                        valor={habilidade.acertos_de_primeira}
                        maximo={habilidade.feitas}
                        rotulo={`Acertos de primeira em ${habilidade.codigo}`}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Cartao>

          {progresso.recentes.length > 0 && (
            <Cartao titulo="Últimas questões">
              <ul className="divide-y divide-stone-200">
                {progresso.recentes.map((resultado) => (
                  <li key={`${resultado.questao_id}-${resultado.concluido_em}`} className="flex items-center justify-between gap-3 py-3">
                    <a href={endereco({ pagina: 'questao', id: resultado.questao_id })} className="font-medium underline-offset-4 hover:underline">
                      ENEM {resultado.questao_id.replace('-', ' · Q')}
                    </a>
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        resultado.acertou_de_primeira
                          ? 'bg-emerald-100 text-emerald-800'
                          : resultado.acertou
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-stone-100 text-stone-600'
                      }`}
                    >
                      {descreverResultado(resultado)}
                    </span>
                  </li>
                ))}
              </ul>
            </Cartao>
          )}
        </>
      )}
    </Pagina>
  )
}
