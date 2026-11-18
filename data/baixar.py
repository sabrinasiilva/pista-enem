"""Baixa as fontes oficiais e o conjunto da Maritaca para data/brutos/.

Uso: python data/baixar.py

Dos microdados do Inep (zips de ~500 MB) só a tabela de itens é baixada,
lendo o zip por partes com requisições HTTP Range.
"""

import io
import time
import urllib.error
import urllib.request
import zipfile

import fontes

AGENTE = {"User-Agent": "pista-enem/0.1 (projeto educacional)"}


class ArquivoRemoto(io.RawIOBase):
    """Arquivo somente leitura que busca os bytes sob demanda via HTTP Range."""

    def __init__(self, url: str):
        self.url = url
        self.posicao = 0
        requisicao = urllib.request.Request(url, method="HEAD", headers=AGENTE)
        with urllib.request.urlopen(requisicao, timeout=60) as resposta:
            self.tamanho = int(resposta.headers["Content-Length"])

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.posicao

    def seek(self, deslocamento: int, origem: int = 0) -> int:
        base = {0: 0, 1: self.posicao, 2: self.tamanho}[origem]
        self.posicao = base + deslocamento
        return self.posicao

    def readinto(self, destino) -> int:
        if self.posicao >= self.tamanho or len(destino) == 0:
            return 0
        fim = min(self.posicao + len(destino), self.tamanho) - 1
        cabecalhos = {**AGENTE, "Range": f"bytes={self.posicao}-{fim}"}
        requisicao = urllib.request.Request(self.url, headers=cabecalhos)

        def ler() -> bytes:
            with urllib.request.urlopen(requisicao, timeout=120) as resposta:
                return resposta.read()

        dados = com_tentativas(ler)
        destino[: len(dados)] = dados
        self.posicao += len(dados)
        return len(dados)


def com_tentativas(funcao, tentativas: int = 4):
    """O servidor do Inep às vezes derruba a conexão; tenta de novo com espera crescente."""
    for tentativa in range(1, tentativas + 1):
        try:
            return funcao()
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if tentativa == tentativas:
                raise
            time.sleep(2 ** tentativa)


def baixar(url: str, destino) -> None:
    if destino.exists():
        print(f"já existe: {destino.name}")
        return

    def ler() -> bytes:
        requisicao = urllib.request.Request(url, headers=AGENTE)
        with urllib.request.urlopen(requisicao, timeout=120) as resposta:
            return resposta.read()

    destino.write_bytes(com_tentativas(ler))
    print(f"baixado: {destino.name}")


def baixar_itens(ano: int) -> None:
    destino = fontes.caminho_itens(ano)
    if destino.exists():
        print(f"já existe: {destino.name}")
        return
    remoto = ArquivoRemoto(fontes.MICRODADOS_URL.format(ano=ano))
    with zipfile.ZipFile(io.BufferedReader(remoto, buffer_size=1 << 20)) as pacote:
        nome = next(n for n in pacote.namelist()
                    if n.upper().endswith(f"ITENS_PROVA_{ano}.CSV"))
        destino.write_bytes(pacote.read(nome))
    print(f"extraído dos microdados: {destino.name}")


def main() -> None:
    fontes.PASTA_BRUTOS.mkdir(exist_ok=True)
    for ano in fontes.ANOS:
        baixar(fontes.MARITACA_URL.format(revisao=fontes.MARITACA_REVISAO, ano=ano),
               fontes.caminho_maritaca(ano))
        baixar(fontes.url_prova(ano), fontes.caminho_prova(ano))
        baixar_itens(ano)
    baixar(fontes.MATRIZ_URL, fontes.caminho_matriz())


if __name__ == "__main__":
    main()
