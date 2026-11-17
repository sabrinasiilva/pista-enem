import 'katex/dist/katex.min.css'
import ReactMarkdown from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkBreaks from 'remark-breaks'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'

/**
 * Markdown com tabelas e fórmulas em LaTeX ($...$). Cifrão literal vem escapado: R\$.
 * Quebra de linha simples vira quebra de linha (as resoluções têm um passo por linha).
 */
export function TextoRico({ texto, className = '' }: { texto: string; className?: string }) {
  return (
    <div className={`texto-rico ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath, remarkBreaks]}
        rehypePlugins={[rehypeKatex]}
        components={{
          table: ({ children }) => (
            <div className="tabela-rolavel">
              <table>{children}</table>
            </div>
          ),
          // links abrem em outra aba e sem passar a origem
          a: ({ children, href }) => (
            <a href={href} target="_blank" rel="noreferrer noopener" className="underline">
              {children}
            </a>
          ),
        }}
      >
        {texto}
      </ReactMarkdown>
    </div>
  )
}
