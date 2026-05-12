import fitz
import os

DPI = 120
ZOOM = DPI / 72
MAT = fitz.Matrix(ZOOM, ZOOM)
OUT_DIR = "pages"

os.makedirs(OUT_DIR, exist_ok=True)

with fitz.open("crowning_Crowning Prayer Paul & Tabitha.pdf") as doc:
    total = len(doc)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=MAT, colorspace=fitz.csRGB)
        path = os.path.join(OUT_DIR, f"page_{i+1:03d}.jpg")
        pix.save(path, jpg_quality=75)
        if (i + 1) % 10 == 0 or i + 1 == total:
            print(f"  rendered {i+1}/{total}")

print(f"Done. {total} pages saved to {OUT_DIR}/")
