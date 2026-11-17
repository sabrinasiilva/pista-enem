/// <reference types="vitest/config" />
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Publicado em sabrinasiilva.github.io/pista-enem/ (Fase 5); em desenvolvimento, na raiz.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/pista-enem/' : '/',
  plugins: [react(), tailwindcss()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/testes/preparar.ts'],
    css: false,
  },
}))
