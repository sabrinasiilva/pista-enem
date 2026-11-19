import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'

// Questão de Matemática de 2022 com fórmula no enunciado ($p(t) = -t^2 + 10t + 24$). Gabarito: C.
const QUESTAO = '2022-158'

async function semProblemasDeAcessibilidade(page: Page) {
  const { violations } = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze()
  const resumo = violations.map((v) => `${v.id}: ${v.help} (${v.nodes.map((n) => n.target.join(' ')).join(', ')})`)
  expect(resumo, 'problemas de acessibilidade (WCAG AA)').toEqual([])
}

async function responder(page: Page, letra: string) {
  // o radio fica escondido (sr-only) e quem recebe o clique é o <label> em volta dele
  const radio = page.getByRole('radio', { name: new RegExp(`^${letra}\\)`) })
  await page.locator('label').filter({ has: radio }).click()
  await expect(radio).toBeChecked()
  // pelo teclado, como faria quem não usa mouse
  await page.getByRole('button', { name: 'Responder' }).press('Enter')
}

for (const tema of ['light', 'dark'] as const) {
  test.describe(`tema ${tema === 'light' ? 'claro' : 'escuro'}`, () => {
    test.use({ colorScheme: tema })

    test('página inicial lista as questões e passa na checagem de acessibilidade', async ({ page }) => {
      await page.goto('./')
      await expect(page.getByRole('tab', { name: 'Matemática' })).toBeVisible()
      await expect(page.locator('a[href^="#/questao/"]').first()).toBeVisible()
      await semProblemasDeAcessibilidade(page)
    })

    test('resolve uma questão: erra, recebe a pista e acerta', async ({ page }) => {
      await page.goto(`./#/questao/${QUESTAO}`)
      await expect(page.getByText(/ENEM 2022 · Questão 158/)).toBeVisible()
      await semProblemasDeAcessibilidade(page)

      await responder(page, 'A')
      await expect(page.getByText(/Pista 1 de 2/)).toBeVisible()
      await expect(page.getByRole('radio', { name: /^A\)/ })).toBeDisabled()
      await semProblemasDeAcessibilidade(page)

      await responder(page, 'C')
      await expect(page.getByText(/Você acertou! A resposta é a alternativa C/)).toBeVisible()
      await semProblemasDeAcessibilidade(page)
    })
  })
}

test('fórmulas têm versão em MathML para leitores de tela', async ({ page }) => {
  await page.goto(`./#/questao/${QUESTAO}`)
  const formula = page.locator('.katex').first()
  await expect(formula).toBeVisible()
  // o desenho da fórmula fica escondido do leitor de tela, e o MathML é o que ele lê
  await expect(formula.locator('.katex-mathml math')).toHaveCount(1)
  await expect(formula.locator('.katex-html')).toHaveAttribute('aria-hidden', 'true')
})

test('dá para chegar numa questão só com o teclado, vendo onde está o foco', async ({ page, isMobile }) => {
  test.skip(isMobile, 'teclado só no computador')
  await page.goto('./')
  await expect(page.locator('a[href^="#/questao/"]').first()).toBeVisible()
  for (let i = 0; i < 40; i++) {
    await page.keyboard.press('Tab')
    const href = await page.evaluate(() => document.activeElement?.getAttribute('href') ?? '')
    if (href.startsWith('#/questao/')) break
  }
  const foco = await page.evaluate(() => {
    const el = document.activeElement as HTMLElement
    const estilo = getComputedStyle(el)
    return { href: el.getAttribute('href'), contorno: estilo.outlineStyle, sombra: estilo.boxShadow }
  })
  expect(foco.href, 'o Tab chegou num card de questão').toMatch(/^#\/questao\//)
  expect(foco.contorno !== 'none' || foco.sombra !== 'none', 'o foco aparece na tela').toBe(true)
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/#\/questao\//)
})
