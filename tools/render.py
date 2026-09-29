"""Turn solved page plans into absolutely-positioned HTML and print it to PDF with Chromium."""
import os
import html as _html
from playwright.sync_api import sync_playwright
from . import style
from .layout import line_geom, N
from .model import runs_html

ALIGN_CLS = {'j': 'j', 'l': 'l', 'c': 'c', 'r': 'r'}

PAGE_CSS = f"""
@page{{size:{style.PAGE_W}pt {style.PAGE_H}pt;margin:0}}
html,body{{margin:0;padding:0}}
.page{{position:relative;width:{style.PAGE_W}pt;height:{style.PAGE_H}pt;overflow:hidden;break-after:page;page-break-after:always}}
.j{{text-align:justify;text-align-last:justify}}
.l{{text-align:left;text-align-last:left}}
.c{{text-align:center;text-align-last:center}}
.r{{text-align:right;text-align-last:right}}
.hd{{position:absolute;left:0;top:0;white-space:nowrap;font-family:"GrkSerif","SongBody",serif;font-size:8pt;color:#333;line-height:10pt}}
.rule{{position:absolute;height:0;border-top:.4pt solid #444}}
.tocdots{{}}
img.inl{{height:1em;vertical-align:-0.2em}}
"""


BASE = {}          # css class -> baseline y (pt from the line top) as actually painted in the PDF


def calibrate(classes, cache=None):
    """Print one line per style class and read back the painted baseline so every style can be shifted onto the body grid."""
    import json
    import pymupdf
    cache = cache or os.path.join(style.SCRATCH, 'baselines.json')
    if os.path.exists(cache):
        BASE.update(json.load(open(cache)))
        if all(c in BASE for c in classes):
            return BASE
    rows = ''.join(f'<div class="ln {c} l" style="width:200pt;transform:translate(10pt,{i * 40}pt)">中文Ag</div>'
                   for i, c in enumerate(classes))
    html = document_html([f'<section class="page">{rows}</section>'])
    pdf = os.path.join(style.SCRATCH, 'calib.pdf')
    print_pdf(html, pdf)
    d = pymupdf.open(pdf)
    ys = []
    for b in d[0].get_text('dict')['blocks']:
        for l in b.get('lines', []):
            ys.append(l['spans'][0]['origin'][1])
    ys.sort()
    for i, c in enumerate(classes):
        BASE[c] = round(ys[i] - i * 40, 3)
    json.dump(BASE, open(cache, 'w'))
    return BASE


def line_div(st, j, nlines_total, align_last, html, x, y, w, ls, slots):
    if st['align'] == 'j':
        a = 'l' if j == nlines_total - 1 else 'j'
    else:
        a = st['align']
    if slots == 1 and BASE:
        y += BASE['s-body'] - BASE[st['cls']]
    extra = ''
    if ls:
        extra += f'letter-spacing:{ls}em;'
    if slots != 1:
        extra += f'height:{slots * style.LINE}pt;line-height:{slots * style.LINE}pt;'
    return (f'<div class="ln {st["cls"]} {a}" style="width:{w:.3f}pt;{extra}'
            f'transform:translate({x:.3f}pt,{y:.3f}pt)">{html}</div>')


def page_html(page, lbs, variants, furniture=''):
    """HTML for one solved page.  page = {'items': [(block, lo, hi, slot0)], 'gap': slots}"""
    gap = page.get('gap', 0)
    k = N / (N - gap) if gap and gap < N else 1.0
    parts = []
    for (bi, lo, hi, slot0) in page['items']:
        lb = lbs[bi]
        st = lb.st
        vi = variants[bi]
        starts = lb.starts[vi]
        ends = starts[1:] + [None]
        ls = style.VARIANTS[vi]
        runs = lb.block['runs']
        for j in range(lo, hi):
            x, w = line_geom(st, j)
            slot = slot0 + (j - lo) * st['slots']
            y = style.TOP + slot * style.LINE * k
            h = runs_html(runs, starts[j], ends[j])
            parts.append(line_div(st, j, len(starts), None, h, style.LEFT + x, y, w, ls, st['slots']))
    return f'<section class="page">{"".join(parts)}{furniture}</section>'


def document_html(pages_html):
    return (f'<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><style>{style.FONTS_CSS}'
            f'{style.STYLE_CSS}{PAGE_CSS}</style></head><body>{"".join(pages_html)}</body></html>')


def print_pdf(html_text, out_pdf, work_html=None):
    work_html = work_html or (os.path.splitext(out_pdf)[0] + '.html')
    with open(work_html, 'w', encoding='utf8') as f:
        f.write(html_text)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=style.CHROME, args=['--no-sandbox'])
        pg = b.new_page()
        pg.goto('file://' + os.path.abspath(work_html))
        pg.evaluate('document.fonts.ready.then(()=>true)')
        pg.wait_for_timeout(500)
        pg.pdf(path=out_pdf, prefer_css_page_size=True, print_background=True)
        b.close()
