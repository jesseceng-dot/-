"""Pictures of the tables that the text layout cannot set (bracket images spanning rows, many columns, diagrams).

The table is rendered by Chromium from the ebook's own markup and stylesheets, with the book's fonts, at the text width
and 4 px per pt; the picture (Images/snap_<part>_<n>.png) then stands in the text like a figure (bk.fig_block, SNAP_SCALE).
    BOOK_SCRATCH=<dir> BOOK_GEOM=k16 BOOK_FONT_DIR=<fonts> python -m tools.snap        all tables of bk_extract.SNAP
"""
import os
import sys
from lxml import etree
from . import style, special
from .bk_extract import SNAP, fix_tree
from .extract import TEXT_DIR, load_body, ln

PX_PER_PT = 4.0

OVERRIDE = """
html,body{margin:0;padding:0;background:#fff}
#x{width:%(w)spt;font-size:10.5pt;line-height:1.5;color:#000;font-family:%(fam)s}
#x *{font-family:inherit;color:#000 !important}
#x .rare,#x .rare1{font-weight:normal}
#x .heiti,#x .emphasis,#x .smallxht,#x .heiti_smalltext{font-family:"GebRare","HeiTi",sans-serif}
#x .dialog_name,#x .dialog_name1{font-family:"GebRare","HeiTi",sans-serif}
#x .kaiti,#x .kaiti_smalltext{font-family:"GebRare","KaiTi",serif}
#x table{margin:0 auto}
#x.wide{width:auto}
#x.wide td{white-space:nowrap}
"""
WIDE = {('part0031', 6)}            # tables wider than the text: set at their natural width (the picture is then scaled down)


def tables(part):
    body = load_body(part)
    return [t for t in body.iter() if isinstance(t.tag, str) and ln(t) == 'table']


def html_of(el):
    s = etree.tostring(el, method='html', encoding='unicode')
    return s.replace('xmlns="http://www.w3.org/1999/xhtml"', '').replace('src="Images/', 'src="../Images/')


def render(jobs):
    """jobs = [(part, table index)]: write Images/snap_<part>_<k>.png for each."""
    from playwright.sync_api import sync_playwright
    css_dir = next((d for d in (os.path.join(os.path.dirname(TEXT_DIR), 'Styles'), os.path.join(style.SCRATCH, 'epub_raw/OEBPS/Styles'))
                    if os.path.isdir(d)), '')
    ebook_css = ''.join(open(os.path.join(css_dir, f), encoding='utf8').read() for f in ('stylesheet.css', 'layout_revision.css')
                        if os.path.exists(os.path.join(css_dir, f)))
    ebook_css = ebook_css.replace('@font-face', '@font-face-ignored')            # (the ebook's own fonts are not used)
    over = OVERRIDE % dict(w=style.TEXT_W, fam=style.BODY_FAMILY)
    done = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=style.CHROME, args=['--no-sandbox'])
        pg = b.new_page(device_scale_factor=PX_PER_PT * 72 / 96, viewport={'width': int(style.TEXT_W * 96 / 72) * 2, 'height': 1200})
        for part, k in jobs:
            el = fix_tree(part, tables(part)[k])                   # the book's corrections (bk_fixes) of this table's text
            path = os.path.join(TEXT_DIR, f'_snap_{part}_{k}.html')
            with open(path, 'w', encoding='utf8') as f:
                f.write(f'<!doctype html><html><head><meta charset="utf-8"><style>{style.FONTS_CSS}{ebook_css}{over}</style></head>'
                        f'<body><div id="x"{" class=wide" if (part, k) in WIDE else ""}>{html_of(el)}</div></body></html>')
            pg.goto('file://' + path)
            pg.evaluate('document.fonts.ready.then(()=>true)')
            pg.wait_for_timeout(150)
            out = os.path.join(special.IMG_DIR, f'snap_{part}_{k}.png')
            pg.query_selector('#x table').screenshot(path=out)
            os.remove(path)
            done.append(out)
        b.close()
    return done


def ensure(key):
    """Render the pictures of book `key` (scratch name, e.g. 'q16') that do not exist yet."""
    jobs = [(f'part{n:04d}', k) for n, k in sorted(SNAP.get(key, ()))
            if not os.path.exists(os.path.join(special.IMG_DIR, f'snap_part{n:04d}_{k}.png'))]
    return render(jobs) if jobs else []


if __name__ == '__main__':
    key = os.path.basename(style.SCRATCH.rstrip('/'))
    if '--force' in sys.argv:
        for n, k in SNAP.get(key, ()):
            f = os.path.join(special.IMG_DIR, f'snap_part{n:04d}_{k}.png')
            if os.path.exists(f):
                os.remove(f)
    for f in ensure(key):
        print(f)
