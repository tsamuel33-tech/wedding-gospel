"""
Redacts '(...)' placeholders on page 2 and replaces them with real names,
then re-renders only page_002.jpg.
"""
import fitz
import os

REPLACEMENTS = [
    ("(...)", "Paul",    0),   # first (...) = son's name
    ("(...)", "Tabitha", 1),   # second (...) = daughter's name
]

DPI  = 120
ZOOM = DPI / 72
MAT  = fitz.Matrix(ZOOM, ZOOM)

doc  = fitz.open("crowning_Crowning Prayer Paul & Tabitha.pdf")
page = doc[1]   # page 2, 0-indexed

# Collect all (...) hit rects in order
all_hits = page.search_for("(...)")
print(f"Found {len(all_hits)} '(...)' instances on page 2: {all_hits}")

for replacement_text, name, hit_index in REPLACEMENTS:
    if hit_index >= len(all_hits):
        print(f"Warning: no hit at index {hit_index}")
        continue
    rect = all_hits[hit_index]
    print(f"Replacing hit[{hit_index}] {rect} -> '{name}'")

    # Redact the old text (fills the rect with white)
    page.add_redact_annot(rect, fill=(1, 1, 1))

page.apply_redactions()

# Insert new names at the same positions
for replacement_text, name, hit_index in REPLACEMENTS:
    if hit_index >= len(all_hits):
        continue
    rect = all_hits[hit_index]
    # insert_text point: left edge of rect, baseline near bottom
    insert_pt = fitz.Point(rect.x0, rect.y1 - 2)
    page.insert_text(
        insert_pt,
        name,
        fontname="tiro",   # PyMuPDF built-in Times-Roman
        fontsize=18.43,
        color=(0, 0, 0),
    )

# Re-render only page 2
pix  = page.get_pixmap(matrix=MAT, colorspace=fitz.csRGB)
path = os.path.join("pages", "page_002.jpg")
pix.save(path, jpg_quality=75)
print(f"Saved {path}")
doc.close()
