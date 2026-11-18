import '@testing-library/jest-dom/vitest'
import { cleanup, configure } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import { aoExpirarASessao, definirToken } from '../api'

// telas carregadas sob demanda podem passar de 1 s numa máquina ocupada (como o CI)
configure({ asyncUtilTimeout: 3000 })

afterEach(() => {
  cleanup()
  definirToken(null)
  aoExpirarASessao(null)
  vi.unstubAllGlobals()
  sessionStorage.clear()
  localStorage.clear()
  document.documentElement.classList.remove('dark')
  window.location.hash = ''
})
