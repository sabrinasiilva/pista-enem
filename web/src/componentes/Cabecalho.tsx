export function Cabecalho() {
  return (
    <header className="sticky top-0 z-10 border-b border-stone-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <a href="#/" className="text-xl font-bold tracking-tight" aria-label="Pista, página inicial">
          pista<span className="text-amber-500">.</span>
        </a>
        <a
          href="https://github.com/sabrinasiilva/pista-enem"
          target="_blank"
          rel="noreferrer"
          className="text-sm text-stone-500 hover:text-stone-900"
        >
          Código aberto
        </a>
      </div>
    </header>
  )
}
