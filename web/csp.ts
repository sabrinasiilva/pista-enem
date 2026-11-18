import type { Plugin } from 'vite'

/**
 * Política de segurança de conteúdo (CSP) do site, como <meta>, só no build.
 *
 * O GitHub Pages não deixa configurar cabeçalhos HTTP, então a CSP vai no HTML. Por isso,
 * `frame-ancestors` (que só vale como cabeçalho) fica de fora; ver SECURITY.md.
 * - script: só os arquivos do próprio site e o script inline do tema, liberado pelo hash;
 * - style: 'unsafe-inline' porque o KaTeX e o React usam o atributo style;
 * - connect: só o próprio site e a API configurada em VITE_API_URL.
 */
export function politicaDeConteudo(apiUrl: string | undefined): Plugin {
  return {
    name: 'pista-csp',
    apply: 'build',
    async transformIndexHtml(html) {
      const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1])
      const hashes = await Promise.all(scripts.map(async (s) => `'sha256-${await sha256(s)}'`))
      const api = apiUrl ? new URL(apiUrl).origin : ''
      const diretivas = [
        "default-src 'self'",
        `script-src 'self' ${hashes.join(' ')}`.trim(),
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "font-src 'self' data:",
        `connect-src 'self' ${api}`.trim(),
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
      ]
      const meta = `<meta http-equiv="Content-Security-Policy" content="${diretivas.join('; ')}" />`
      return html.replace('<meta charset="UTF-8" />', `<meta charset="UTF-8" />\n    ${meta}`)
    },
  }
}

async function sha256(texto: string): Promise<string> {
  const resumo = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(texto))
  return btoa(String.fromCharCode(...new Uint8Array(resumo)))
}
