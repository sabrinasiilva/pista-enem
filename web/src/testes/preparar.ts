import '@testing-library/jest-dom/vitest'
import { cleanup, configure } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import { aoExpirarASessao, definirToken } from '../api'

// telas carregadas sob demanda podem passar de 1 s numa máquina ocupada (como o CI)
configure({ asyncUtilTimeout: 3000 })
localStorage.setItem('pista:apresentacao', 'vista') // os testes começam depois da apresentação

afterEach(() => {
  cleanup()
  definirToken(null)
  aoExpirarASessao(null)
  vi.unstubAllGlobals()
  sessionStorage.clear()
  localStorage.clear()
  localStorage.setItem('pista:apresentacao', 'vista') // os outros testes começam depois dela
  document.documentElement.classList.remove('dark')
  window.location.hash = ''
})
