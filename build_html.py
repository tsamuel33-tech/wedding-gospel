import pdfplumber
import html as htmllib
import re

def clean(text):
    # Collapse 4x repeated characters (PDF bold font artifact: "TTTThhhheeee" -> "The")
    return re.sub(r'(.)\1{3,}', r'\1', text)

# Arabic combining/diacritical mark ranges (tashkeel, etc.)
ARABIC_DIACRITICS = re.compile(
    r'^[\sؐ-ًؚ-ٰٟۖ-ۜ۟-۪ۤۧۨ-ۭ‌‍﻿]+$'
)

def is_real_word(word):
    return not ARABIC_DIACRITICS.match(word['text'])

HTML_HEAD = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Crowning Prayer — Paul &amp; Tabitha</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #000; font-family: Georgia, serif; padding: 20px 10px; max-width: 1200px; margin: 0 auto; line-height: 1.75; }
        .cross { text-align: center; font-size: 3rem; color: #c8a84b; margin-bottom: 10px; }
        h1 { text-align: center; font-size: 1.7rem; color: #c8a84b; margin-bottom: 6px; letter-spacing: 2px; }
        .sub { text-align: center; font-size: 1rem; color: #c8a84b; margin-bottom: 28px; font-style: italic; }
        table { width: 100%; border-collapse: collapse; table-layout: fixed; }
        td { padding: 1px 6px; vertical-align: top; font-size: 0.87rem; }
        .en  { color: #ffffff; width: 38%; }
        .cop { color: #c8a84b; width: 30%; }
        .ar  { color: #87ceeb; width: 32%; direction: rtl; text-align: right; }
        tr.gap td { height: 8px; }
        tr.pb  td { height: 3px; border-top: 1px solid #2a2a2a; }
    </style>
</head>
<body>
<div class="cross">☩</div>
<h1>The Crowning Prayer</h1>
<div class="sub">Paul Meawad &amp; Tabitha</div>
<table><tbody>
'''

HTML_FOOT = '</tbody></table></body></html>\n'

def esc(text):
    return htmllib.escape(text) if text else ''

rows_out = []

with pdfplumber.open("crowning_Crowning Prayer Paul & Tabitha.pdf") as pdf:
    total_pages = len(pdf.pages)
    for page_num, page in enumerate(pdf.pages):
        w = page.width
        c1 = w * 0.35   # English / Coptic boundary (~35%)
        c2 = w * 0.66   # Coptic / Arabic boundary (~66%, gap confirmed at 64-68%)

        words = page.extract_words(x_tolerance=3, y_tolerance=3)
        if not words:
            continue

        # Drop Arabic-diacritical-only tokens (combining marks extracted as lone words)
        words = [ww for ww in words if is_real_word(ww)]
        words.sort(key=lambda ww: (round(ww['top']), ww['x0']))

        # Group words into lines by y-proximity
        line_groups = []
        cur = []
        base_y = None
        for word in words:
            if base_y is None or abs(word['top'] - base_y) <= 5:
                cur.append(word)
                if base_y is None:
                    base_y = word['top']
            else:
                if cur:
                    line_groups.append(cur)
                cur = [word]
                base_y = word['top']
        if cur:
            line_groups.append(cur)

        prev_y = None
        for group in line_groups:
            avg_y = sum(ww['top'] for ww in group) / len(group)

            # Insert blank gap row on large vertical jumps (paragraph breaks)
            if prev_y is not None and (avg_y - prev_y) > 18:
                rows_out.append('<tr class="gap"><td></td><td></td><td></td></tr>')
            prev_y = avg_y

            def col_words(lo, hi):
                ws = sorted(
                    [(ww['x0'], ww['text']) for ww in group
                     if lo <= (ww['x0'] + ww['x1']) / 2 < hi],
                    key=lambda t: t[0]
                )
                return ' '.join(t for _, t in ws)

            en  = esc(clean(col_words(0,  c1)))
            cop = esc(clean(col_words(c1, c2)))
            ar  = esc(clean(col_words(c2, w * 1.1)))

            rows_out.append(
                f'<tr>'
                f'<td class="en">{en}</td>'
                f'<td class="cop">{cop}</td>'
                f'<td class="ar">{ar}</td>'
                f'</tr>'
            )

        # Thin rule between pages
        if page_num < total_pages - 1:
            rows_out.append('<tr class="pb"><td colspan="3"></td></tr>')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(HTML_HEAD)
    f.write('\n'.join(rows_out))
    f.write(HTML_FOOT)

print(f"Done. {total_pages} pages, {len(rows_out)} rows in index.html")
