import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import { aoExpirarASessao, definirToken } from '../api'

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
