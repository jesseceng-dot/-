"""Reprinting a delivered PDF with a printing fix only, its line breaks and pages unchanged.

The layout of every module is cached under a key made of the module's content and the code of the layout engine
(layout/style/hyph/measure/typeset/model/book.py); render.py is not part of the key.  So a checkout of the commit
that built a PDF, with only render.py changed, prints the same pages from the same cache:

    git worktree add <dir> <commit of the PDF>                  # git log -1 --format=%h -- out/16k/03-….pdf
    python -m tools.reprint patch <dir>                         # the joiner fix of 7120948 into its render.py
    cd <dir> && BOOK_SCRATCH=… BOOK_GEOM=k16 BOOK_FONT_DIR=… python -m tools.bk_build 3     # (or make_all, kant_make_all)
    python -m tools.reprint compare <delivered.pdf> <reprinted.pdf>

`compare` checks page count, the text of every line (word joiners left out), every baseline, links, bookmarks and
page labels, and counts the word joiners that take width (the gap before note marks): the reprint must be the same
in everything but that count, which must be 0.
"""
import re
import sys

import pymupdf

from .qa_pdf import joiners


def patch(root):
    """render.line_div drops U+2060 from printed lines (Chromium draws the joiner as a space glyph, ~1.8 pt)."""
    p = root + '/tools/render.py'
    s = open(p, encoding='utf8').read()
    if "html.replace('\\u2060', '')" in s:
        return 'already'
    m = re.search(r"def line_div\(([^)]*)\):\n", s)
    if not m:
        raise SystemExit('no line_div in ' + p)
    s = s[:m.end()] + "    html = html.replace('\\u2060', '')          # word joiners only steer the line breaking (fix of 7120948)\n" + s[m.end():]
    open(p, 'w', encoding='utf8').write(s)
    return 'patched'


def _lines(pg):
    out = []
    for b in pg.get_text('rawdict')['blocks']:
        for l in b.get('lines', []):
            t = ''.join(c['c'] for s in l['spans'] for c in s['chars']).replace('⁠', '')
            if t.strip():
                out.append((round(l['spans'][0]['origin'][1], 1), t))
    return out


def compare(old, new):
    a, b = pymupdf.open(old), pymupdf.open(new)
    res = dict(pages=(a.page_count, b.page_count))
    dt = dl = 0
    ex = []
    for i in range(min(a.page_count, b.page_count)):
        la, lb = _lines(a[i]), _lines(b[i])
        if [t for _, t in la] != [t for _, t in lb]:
            dt += 1
            if len(ex) < 3:
                ex.append((i + 1, [x for x in la if x not in lb][:2], [x for x in lb if x not in la][:2]))
        elif [y for y, _ in la] != [y for y, _ in lb]:
            dl += 1
    res['pages_text_diff'] = dt
    res['pages_baseline_diff'] = dl
    res['links'] = (sum(len(p.get_links()) for p in a), sum(len(p.get_links()) for p in b))
    res['outline'] = (len(a.get_toc()), len(b.get_toc()))
    res['labels'] = (a[a.page_count - 1].get_label(), b[b.page_count - 1].get_label())
    res['joiners_wide'] = (joiners(a)[1], joiners(b)[1])
    res['fonts_type3'] = sum(1 for p in b for f in p.get_fonts() if f[2] == 'Type3')
    return res, ex


if __name__ == '__main__':
    if sys.argv[1] == 'patch':
        print(patch(sys.argv[2]))
    else:
        r, ex = compare(sys.argv[2], sys.argv[3])
        print(r)
        for e in ex:
            print('  diff', e)
