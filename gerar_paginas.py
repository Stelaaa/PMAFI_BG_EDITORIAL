"""
Converte o PDF em imagens JPG para o flipbook carregar rápido.

Uso:
    python gerar_paginas.py                        # usa documento.pdf, 150 dpi
    python gerar_paginas.py ARQUIVO.pdf            # outro arquivo
    python gerar_paginas.py ARQUIVO.pdf 120        # outro arquivo e outra resolução

Rode de novo sempre que trocar o PDF.

Segurança: as imagens são geradas numa pasta temporária. As imagens antigas
só são substituídas se TODAS as páginas forem convertidas com sucesso.

Métodos (tenta na ordem):
  1. PyMuPDF      -> pip install pymupdf
  2. pdftoppm     -> sudo apt-get install -y poppler-utils   (mais tolerante a PDFs com defeito)
"""
import glob
import json
import os
import shutil
import subprocess
import sys

PDF = sys.argv[1] if len(sys.argv) > 1 else "documento.pdf"
DPI = int(sys.argv[2]) if len(sys.argv) > 2 else 150
PASTA = "paginas"
TEMP = "paginas_tmp"
QUALIDADE = 82


def com_pymupdf():
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf  # versões antigas

    doc = pymupdf.open(PDF)
    total = doc.page_count
    largura = altura = None
    for i in range(total):
        page = doc.load_page(i)  # gera erro se a página estiver danificada
        if i == 0:
            largura, altura = page.rect.width, page.rect.height
        pix = page.get_pixmap(dpi=DPI)
        pix.save(os.path.join(TEMP, f"{i + 1:03d}.jpg"), jpg_quality=QUALIDADE)
        print(f"  página {i + 1}/{total}", end="\r", flush=True)
    print()
    return largura, altura


def com_pdftoppm():
    if not shutil.which("pdftoppm"):
        raise RuntimeError("pdftoppm não instalado (rode: sudo apt-get install -y poppler-utils)")
    subprocess.run(
        ["pdftoppm", "-jpeg", "-jpegopt", f"quality={QUALIDADE}", "-r", str(DPI),
         PDF, os.path.join(TEMP, "p")],
        check=True,
    )
    gerados = sorted(glob.glob(os.path.join(TEMP, "p-*.jpg")),
                     key=lambda f: int(f.rsplit("-", 1)[1].split(".")[0]))
    if not gerados:
        raise RuntimeError("nenhuma página gerada")
    for n, f in enumerate(gerados, 1):
        os.rename(f, os.path.join(TEMP, f"{n:03d}.jpg"))
    # tamanho da página em pontos, a partir da primeira imagem
    from struct import unpack
    with open(os.path.join(TEMP, "001.jpg"), "rb") as fh:
        dados = fh.read()
    i = 2
    while i < len(dados):
        marcador, tam = dados[i + 1], unpack(">H", dados[i + 2:i + 4])[0]
        if marcador in (0xC0, 0xC1, 0xC2):
            h, w = unpack(">HH", dados[i + 5:i + 9])
            return w * 72 / DPI, h * 72 / DPI
        i += 2 + tam
    raise RuntimeError("não consegui ler o tamanho da página")


def main():
    if not os.path.exists(PDF):
        sys.exit(f"Arquivo não encontrado: {PDF}")
    print(f"PDF: {PDF} ({os.path.getsize(PDF) / 1024 / 1024:.1f} MB), {DPI} dpi")

    tamanho = None
    for nome, metodo in (("PyMuPDF", com_pymupdf), ("pdftoppm", com_pdftoppm)):
        shutil.rmtree(TEMP, ignore_errors=True)
        os.makedirs(TEMP)
        print(f"Tentando com {nome}...")
        try:
            tamanho = metodo()
            break
        except Exception as e:
            print(f"  falhou: {e}")

    if tamanho is None:
        shutil.rmtree(TEMP, ignore_errors=True)
        sys.exit("\nNão foi possível converter o PDF. As imagens antigas foram mantidas.\n"
                 "O PDF provavelmente está danificado: exporte de novo pelo InDesign\n"
                 "ou envie o arquivo novamente para o Codespaces.")

    # sucesso: troca a pasta antiga pela nova
    shutil.rmtree(PASTA, ignore_errors=True)
    os.rename(TEMP, PASTA)
    arquivos = [f"{PASTA}/{f}" for f in sorted(os.listdir(PASTA)) if f.endswith(".jpg")]

    with open("paginas.json", "w", encoding="utf-8") as f:
        json.dump({"pdf": PDF, "width": round(tamanho[0], 2), "height": round(tamanho[1], 2),
                   "pages": arquivos}, f, indent=1)

    mb = sum(os.path.getsize(a) for a in arquivos) / 1024 / 1024
    print(f"Pronto: {len(arquivos)} páginas em '{PASTA}/' ({mb:.1f} MB) + paginas.json")


if __name__ == "__main__":
    main()
