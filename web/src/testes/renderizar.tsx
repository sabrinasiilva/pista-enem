import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { ProvedorDaConta } from '../conta'
import { ProvedorDoTema } from '../tema'

/** Renderiza com os provedores de tema e de conta, como no App. */
export function renderizar(elemento: ReactElement) {
  return render(
    <ProvedorDoTema>
      <ProvedorDaConta>{elemento}</ProvedorDaConta>
    </ProvedorDoTema>,
  )
}
