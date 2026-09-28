"""
Converter PDF em imagens JPG pra flipbook carregar rápido.

Uso:
    pip install pymupdf
    python gerar_paginas.py                  # usa PMAFI_BG_EDITORIAL.pdf, 150 dpi
    python gerar_paginas.py outro.pdf 120    # arquivo e dpi personalizados
"""
import json
import os
import sys

import fitz  # PyMuPDF

PDF = sys.argv[1] if len(sys.argv) > 1 else "PMAFI_BG_EDITORIAL.pdf"
DPI = int(sys.argv[2]) if len(sys.argv) > 2 else 150
PASTA = "paginas"

os.makedirs(PASTA, exist_ok=True)
for f in os.listdir(PASTA):  # limpa imagens antigas
    if f.endswith(".jpg"):
        os.remove(os.path.join(PASTA, f))

doc = fitz.open(PDF)
arquivos = []
for i, page in enumerate(doc, 1):
    pix = page.get_pixmap(dpi=DPI)
    nome = f"{PASTA}/{i:03d}.jpg"
    pix.save(nome, jpg_quality=82)
    arquivos.append(nome)
    print(f"Página {i}/{len(doc)}", end="\r", flush=True)

primeira = doc[0].rect
with open("paginas.json", "w", encoding="utf-8") as f:
    json.dump({"pdf": PDF, "width": primeira.width, "height": primeira.height,
               "pages": arquivos}, f, indent=1)

tamanho = sum(os.path.getsize(a) for a in arquivos) / 1024 / 1024
print(f"\nPronto: {len(arquivos)} páginas em '{PASTA}/' ({tamanho:.1f} MB) + paginas.json")
