import { act, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Carregando, ESPERA_ANTES_DO_AVISO } from './Avisos'

describe('Carregando', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('avisa que o servidor pode estar acordando se demorar', () => {
    vi.useFakeTimers()
    render(<Carregando />)
    expect(screen.queryByText(/leva até 1 minuto/)).not.toBeInTheDocument()
    act(() => {
      vi.advanceTimersByTime(ESPERA_ANTES_DO_AVISO)
    })
    expect(screen.getByText(/leva até 1 minuto/)).toBeInTheDocument()
  })
})
