import fitz  # PyMuPDF
import html as htmllib
import re

# ---------- text cleaning ----------

def dedup_phrase(text):
    """Remove word-level N-tuple repetitions (PyMuPDF bold artifact)."""
    words = text.split()
    n = len(words)
    for phrase_len in range(1, n // 3 + 1):
        phrase = words[:phrase_len]
        copies, pos = 1, phrase_len
        while pos + phrase_len <= n and words[pos:pos + phrase_len] == phrase:
            copies += 1
            pos += phrase_len
        if copies >= 3:
            remaining = words[pos:]
            # trim any trailing partial copy of the same phrase
            for trim_len in range(min(phrase_len, len(remaining)), 0, -1):
                if remaining[:trim_len] == phrase[:trim_len]:
                    remaining = remaining[trim_len:]
                    break
            return ' '.join(phrase) + (' ' + ' '.join(remaining) if remaining else '')
    return text

def clean(text):
    text = re.sub(r'(.)\1{3,}', r'\1', text)       # char-level 4× repetition
    lines = [dedup_phrase(l) for l in text.split('\n') if l.strip()]
    result = dedup_phrase(' '.join(lines).strip())  # deduplicate after joining lines
    return re.sub(r'  +', ' ', result)              # collapse PDF justification spaces

def esc(text):
    return htmllib.escape(text) if text else ''

# Arabic Unicode block (for splitting mixed-language blocks)
_AR = re.compile(r'[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]')

def split_ar_en(text):
    """Split a mixed block into (non-Arabic part, Arabic part)."""
    tokens = re.split(r'(\s+)', text)
    en_words, ar_words = [], []
    for tok in tokens:
        if _AR.search(tok):
            ar_words.append(tok)
        else:
            en_words.append(tok)
    return ''.join(en_words).strip(), ''.join(ar_words).strip()

# ---------- column detection ----------

def block_col(x0, x1, w):
    xc = (x0 + x1) / 2 / w
    full_width = x0 / w < 0.10 and x1 / w > 0.60
    if full_width:
        return 'mixed'          # direction note / header spanning all columns
    if xc < 0.30:
        return 'en'
    elif xc < 0.60:
        return 'cop'
    else:
        return 'ar'

# ---------- HTML template ----------

HTML_HEAD = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Crowning Prayer — Paul &amp; Tabitha</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #000; font-family: Georgia, serif;
               padding: 20px 12px; margin: 0 auto; max-width: 1300px;
               line-height: 1.75; }
        .cross { text-align: center; font-size: 3rem; color: #c8a84b;
                 margin-bottom: 10px; }
        h1 { text-align: center; font-size: 1.7rem; color: #c8a84b;
             margin-bottom: 6px; letter-spacing: 2px; }
        .sub { text-align: center; font-size: 1rem; color: #c8a84b;
               margin-bottom: 28px; font-style: italic; }
        /* Three-column flex layout */
        .columns { display: flex; gap: 18px; align-items: flex-start; }
        .col { flex: 1 1 0; min-width: 0; padding: 0 4px; }
        .col-en  { color: #ffffff; }
        .col-cop { color: #c8a84b; }
        .col-ar  { color: #87ceeb; direction: rtl; text-align: right; }
        .col p { font-size: 0.88rem; margin-bottom: 8px; }
        .col-header { font-size: 0.75rem; font-weight: bold;
                      letter-spacing: 2px; text-transform: uppercase;
                      opacity: 0.5; margin-bottom: 10px; text-align: center; }
        @media (max-width: 700px) {
            .columns { flex-direction: column; }
            .col { width: 100%; }
            .col-ar { text-align: right; }
        }
    </style>
</head>
<body>
<div class="cross">&#9769;</div>
<h1>The Crowning Prayer</h1>
<div class="sub">Paul Meawad &amp; Tabitha</div>
<div class="columns">
<div class="col col-en"><p class="col-header">English</p>
'''

HTML_MID1 = '</div>\n<div class="col col-cop"><p class="col-header">Coptic</p>\n'
HTML_MID2 = '</div>\n<div class="col col-ar"><p class="col-header">&#1593;&#1585;&#1576;&#1610;</p>\n'
HTML_FOOT = '</div>\n</div>\n</body>\n</html>\n'

# ---------- extraction ----------

en_paras, cop_paras, ar_paras = [], [], []

with fitz.open("crowning_Crowning Prayer Paul & Tabitha.pdf") as doc:
    for page in doc:
        w = page.rect.width
        for b in page.get_text('blocks', sort=True):
            x0, y0, x1, y1, text, bno, btype = b
            if btype != 0 or not text.strip():
                continue
            text = clean(text)
            if not text:
                continue
            col = block_col(x0, x1, w)
            if col == 'mixed':
                en_part, ar_part = split_ar_en(text)
                if en_part:
                    en_paras.append(en_part)
                if ar_part:
                    ar_paras.append(ar_part)
            elif col == 'en':
                en_part, ar_part = split_ar_en(text)
                if en_part:
                    en_paras.append(en_part)
                # any Arabic that leaked into the English block -> Arabic col
                if ar_part:
                    ar_paras.append(ar_part)
            elif col == 'cop':
                cop_paras.append(text)
            else:
                ar_paras.append(text)

# ---------- write HTML ----------

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(HTML_HEAD)
    for p in en_paras:
        f.write(f'<p>{esc(p)}</p>\n')
    f.write(HTML_MID1)
    for p in cop_paras:
        f.write(f'<p>{esc(p)}</p>\n')
    f.write(HTML_MID2)
    for p in ar_paras:
        f.write(f'<p>{esc(p)}</p>\n')
    f.write(HTML_FOOT)

print(f"Done. en={len(en_paras)} cop={len(cop_paras)} ar={len(ar_paras)} paragraphs")
