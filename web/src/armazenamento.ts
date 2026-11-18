// Acesso ao localStorage/sessionStorage que nunca quebra a página: em modo privado ou com
// armazenamento bloqueado, os métodos só não guardam nada.

function seguro<T>(funcao: () => T, padrao: T): T {
  try {
    return funcao()
  } catch {
    return padrao
  }
}

export const local = {
  ler: (chave: string) => seguro(() => localStorage.getItem(chave), null),
  gravar: (chave: string, valor: string) => seguro(() => localStorage.setItem(chave, valor), undefined),
  apagar: (chave: string) => seguro(() => localStorage.removeItem(chave), undefined),
}

export const daAba = {
  ler: (chave: string) => seguro(() => sessionStorage.getItem(chave), null),
  gravar: (chave: string, valor: string) => seguro(() => sessionStorage.setItem(chave, valor), undefined),
  apagar: (chave: string) => seguro(() => sessionStorage.removeItem(chave), undefined),
}
