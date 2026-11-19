import { defineConfig, devices } from '@playwright/test'

/**
 * Testes de ponta a ponta: sobem a API de verdade (sem a chave do Gemini, então o tutor
 * responde com as pistas escritas à mão) e o site já buildado, como no GitHub Pages.
 * Uso: npm run e2e (a API precisa das dependências Python instaladas).
 */
const API = 'http://localhost:8010'
const SITE = 'http://localhost:4180/pista-enem/'
const PYTHON = process.env.PYTHON ?? 'python'

export default defineConfig({
  testDir: 'e2e',
  testMatch: '*.e2e.ts',
  fullyParallel: true,
  expect: { timeout: 15_000 },
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['list']] : 'list',
  // PW_CANAL=msedge usa o Edge instalado, sem baixar o navegador do Playwright
  use: { baseURL: SITE, trace: 'retain-on-failure', channel: process.env.PW_CANAL },
  projects: [
    { name: 'computador', use: { ...devices['Desktop Chrome'] } },
    { name: 'celular', use: { ...devices['Pixel 7'] } },
  ],
  webServer: [
    {
      command: `${PYTHON} -m uvicorn app.main:app --port 8010`,
      cwd: '../api',
      url: `${API}/health`,
      reuseExistingServer: !process.env.CI,
      env: {
        GEMINI_API_KEY: '',
        CORS_ORIGENS: 'http://localhost:4180',
        DATABASE_URL: 'sqlite:///./e2e.db',
      },
    },
    {
      command: 'npx vite build && npx vite preview --port 4180 --strictPort',
      url: SITE,
      reuseExistingServer: !process.env.CI,
      env: { VITE_API_URL: API },
      timeout: 180_000,
    },
  ],
})
