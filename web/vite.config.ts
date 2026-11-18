/// <reference types="vitest/config" />
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import { politicaDeConteudo } from './csp'

// Publicado em sabrinasiilva.github.io/pista-enem/ (Fase 5); em desenvolvimento, na raiz.
export default defineConfig(({ command, mode }) => ({
  base: command === 'build' ? '/pista-enem/' : '/',
  plugins: [
    react(),
    tailwindcss(),
    politicaDeConteudo(loadEnv(mode, '.', 'VITE_').VITE_API_URL),
  ],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/testes/preparar.ts'],
    css: false,
    testTimeout: 15000,
  },
}))
