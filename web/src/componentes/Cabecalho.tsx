export function Cabecalho() {
  return (
    <header className="border-b border-stone-200 bg-white">
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
        <a href="#/" className="text-xl font-bold tracking-tight" aria-label="Pista, página inicial">
          pista<span className="text-pista">.</span>
        </a>
        <span className="text-sm text-stone-500">Matemática · ENEM</span>
      </div>
    </header>
  )
}
