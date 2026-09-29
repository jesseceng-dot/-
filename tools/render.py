"""Turn solved page plans into absolutely-positioned HTML and print it to PDF with Chromium."""
import os
import html as _html
from playwright.sync_api import sync_playwright
from . import style
from .layout import line_geom, N
from .model import runs_html
from .style import LINK_BASE

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


BASE = {}          # "css-class@pitch" -> baseline y (pt from the line top) as actually painted in the PDF


def calibrate(pairs, cache=None):
    """Print one line per (style class, pitch) and read back the painted baseline so every style can be shifted onto the body grid."""
    import json
    import pymupdf
    cache = cache or os.path.join(style.SCRATCH, 'baselines.json')
    keys = [f'{c}@{p}' for c, p in pairs]
    if os.path.exists(cache):
        BASE.update(json.load(open(cache)))
        if all(k in BASE for k in keys):
            return BASE
    per = 12
    pages = []
    for c0 in range(0, len(pairs), per):
        rows = ''.join(f'<div class="ln {c} l" style="width:200pt;height:{p}pt;line-height:{p}pt;'
                       f'transform:translate(10pt,{i * 40}pt)">中文Ag</div>' for i, (c, p) in enumerate(pairs[c0:c0 + per]))
        pages.append(f'<section class="page">{rows}</section>')
    pdf = os.path.join(style.SCRATCH, 'calib.pdf')
    print_pdf(document_html(pages), pdf)
    d = pymupdf.open(pdf)
    for pi, c0 in enumerate(range(0, len(pairs), per)):
        ys = []
        for blk in d[pi].get_text('dict')['blocks']:
            for l in blk.get('lines', []):
                ys.append(l['spans'][0]['origin'][1])
        ys.sort()
        for i, k in enumerate(keys[c0:c0 + per]):
            BASE[k] = round(ys[i] - i * 40, 3)
    json.dump(BASE, open(cache, 'w'))
    return BASE


def baseline_dy(st):
    """Vertical shift of a single-slot line so that its baseline lands on the body grid (and, for the small grid,
    so that the last baseline of the page coincides with the last baseline of body pages)."""
    from .layout import GRIDS
    key = f'{st["cls"]}@{st["pitch"]}'
    if st['slots'] != 1 or not BASE or key not in BASE:
        return 0.0
    if st['pitch'] == style.LINE:
        return BASE[f's-body@{style.LINE}'] - BASE[key]
    n = [g['n'] for g in GRIDS.values() if g['pitch'] == st['pitch']][0]
    body_last = (style.NLINES - 1) * style.LINE + BASE[f's-body@{style.LINE}']
    return body_last - ((n - 1) * st['pitch'] + BASE[key])


def line_div(st, j, nlines_total, html, x, y, w, ls):
    if st['align'] == 'j':
        a = 'l' if j == nlines_total - 1 else 'j'
    else:
        a = st['align']
    y += baseline_dy(st)
    extra = ''
    if ls:
        extra += f'letter-spacing:{ls}em;'
    if st['slots'] != 1:
        h = st['slots'] * st['pitch']
        extra += f'height:{h}pt;line-height:{h}pt;'
    elif st['pitch'] != style.LINE:
        extra += f'height:{st["pitch"]}pt;line-height:{st["pitch"]}pt;'
    return (f'<div class="ln {st["cls"]} {a}" style="width:{w:.3f}pt;{extra}'
            f'transform:translate({x:.3f}pt,{y:.3f}pt)">{html}</div>')


def logical_page_html(page, lbs, variants, grid='body', col=0, anchors=None, page_ref=None):
    """Lines of one solved logical page.  page = {'items': [(block, lo, hi, slot0)], 'gap': slots}.
    Records anchor positions into `anchors` (id -> (page_ref, y))."""
    from .layout import GRIDS
    g = GRIDS[grid]
    gap = page.get('gap', 0)
    n = g['n']
    k = n / (n - gap) if gap and gap < n else 1.0
    x0 = style.LEFT + col * (g['W'] + g['gutter'])
    parts = []
    for (bi, lo, hi, slot0) in page['items']:
        lb = lbs[bi]
        st = lb.st
        vi = variants[bi]
        starts = lb.starts[vi]
        ends = starts[1:] + [None]
        ls = style.VARIANTS[vi]
        runs = lb.block['runs']
        if lb.block['k'] == 'img':
            b = lb.block
            y = style.TOP + slot0 * st['pitch'] * k
            iw, ih = b['w'], b['h']
            parts.append(f'<img src="{b["src"]}" style="position:absolute;left:0;top:0;width:{iw}pt;height:{ih}pt;'
                         f'transform:translate({x0 + (st["W"] - iw) / 2:.2f}pt,{y:.2f}pt)">')
            continue
        if lb.block['k'] == 'space':
            continue
        for j in range(lo, hi):
            x, w = line_geom(st, j)
            slot = slot0 + (j - lo) * st['slots']
            y = style.TOP + slot * st['pitch'] * k
            h = runs_html(runs, starts[j], ends[j], final=True)
            parts.append(line_div(st, j, len(starts), h, x0 + x, y, w, ls))
            if lb.block.get('rule') and j == 0 and slot0 > 0:
                parts.append(f'<div class="rule" style="left:{x0:.2f}pt;width:{st["W"]:.2f}pt;top:{y - 9:.2f}pt"></div>')
            if lb.block.get('pg') is not None and j == len(starts) - 1:
                parts.append(toc_tail(st, lb.nat[vi][j], x0 + x, x0 + st['W'], y, lb.block['pg'], lb.block.get('h', ''),
                                      plain=(lb.block.get('tail') == 'plain')))
            if anchors is not None:
                _register_anchors(anchors, lb.block, runs, starts[j], ends[j], page_ref, y, j == 0)
    return ''.join(parts)


def toc_tail(st, nat, x, right, y, label, href, plain=False):
    """Dot leader and right-aligned page number of a table-of-contents line.  With `plain` the label is a small
    right-aligned note (a book's page count) without leader."""
    nw = 30.0
    if plain:
        st2 = dict(st, cls='s-mnote')
        y2 = y + baseline_dy(st2)
        num = f'<div class="ln s-mnote r" style="width:120pt;transform:translate({right - 120:.2f}pt,{y2:.2f}pt)">{label}</div>'
        return f'<a href="{LINK_BASE}{href}">{num}</a>' if href else num
    y += baseline_dy(st)
    xs, xe = x + nat + 6, right - nw - 4
    base = BASE.get(f'{st["cls"]}@{st["pitch"]}', 12.0)
    out = ''
    if xe - xs > 10:
        out += (f'<div style="position:absolute;left:0;top:0;height:0;width:{xe - xs:.2f}pt;border-top:.9pt dotted #333;'
                f'transform:translate({xs:.2f}pt,{y + base - 1.2:.2f}pt)"></div>')
    num = f'<div class="ln {st["cls"]} r" style="width:{nw}pt;transform:translate({right - nw:.2f}pt,{y:.2f}pt)">{label}</div>'
    if href:
        num = f'<a href="{LINK_BASE}{href}">{num}</a>'
    return out + num


def _register_anchors(anchors, block, runs, s, e, page_ref, y, first_line):
    if first_line and block.get('id') and block['id'] not in anchors:
        anchors[block['id']] = (page_ref, y)
    pos = 0
    for r in runs:
        n = len(r['t'])
        if r.get('a') and s <= pos < (e if e is not None else 10 ** 9) and r['a'] not in anchors:
            anchors[r['a']] = (page_ref, y)
        pos += n


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
