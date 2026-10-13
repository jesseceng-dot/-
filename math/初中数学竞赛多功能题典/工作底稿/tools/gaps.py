"""gaps.py page y [spec_module id]: print inter-glyph gaps of a book line and
(optionally) of the re-typeset unedited skeleton line."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, pymupdf, engine as E, para, run, importlib
import texlayout as T
pdf = pikepdf.open(os.path.join(run.BASE, 'src/book.pdf')); bf = E.BookFonts(pdf)
pn = int(sys.argv[1]); y = float(sys.argv[2])
pe = E.PageEdit(pdf, pn, bf)
def show(row, get):
    prev = None; out = []
    for g in row:
        u, x, adv = get(g)
        if prev is not None:
            out.append('%s|%.2f|' % (prev[0] or '?', x - (prev[1] + prev[2])))
        prev = (u, x, adv)
    out.append(prev[0])
    return ' '.join(out)
row = sorted([g for g in pe.glyphs if -1 < g.y - y < 6 and g.size > 6], key=lambda g: g.x)
print('BOOK:', show(row, lambda g: (g.uni, g.x, g.adv)))
if len(sys.argv) > 4:
    mod = importlib.import_module(sys.argv[3])
    s = [x for x in mod.SPECS if x['id'] == sys.argv[4]][0]
    doc = pymupdf.open(os.path.join(run.BASE, 'src/book.pdf'))
    x_first = s.get('x') or para.first_text_x(pe, s['y'])
    tex = sys.argv[5] if len(sys.argv) > 5 else run.skeleton(doc, pn, s['top'], s['bot'], x_first)
    r = para.retypeset(pe, x_first, s['top'], s['bot'], tex, 'gaps', dry=True, verbose=False, levels=s.get('levels', True))
    ob = min(r['obase'], key=lambda b: abs(b - y)); i = r['obase'].index(ob)
    if i < len(r['nbase']):
        nb = r['nbase'][i]
        row = sorted(r['nrows'][nb], key=lambda g: g['x'])
        print('NEW :', show(row, lambda g: (g['uni'], g['x'], g['adv'])))
