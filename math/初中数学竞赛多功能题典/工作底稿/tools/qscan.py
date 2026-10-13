import sys, os, importlib
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, pymupdf, engine as E, para, run
src = os.path.join(run.BASE, 'src/book.pdf')
pdf = pikepdf.open(src); doc = pymupdf.open(src); bf = E.BookFonts(pdf)
for mn in sys.argv[1:]:
    m = importlib.import_module(mn)
    for s in m.SPECS:
        if s.get('kind', 'para') != 'para' or s.get('tex') is not None:
            continue
        pe = E.PageEdit(pdf, s['page'], bf)
        x = s.get('x') or para.first_text_x(pe, s['y'])
        t = run.skeleton(doc, s['page'], s['top'], s['bot'], x)
        if '``' in t or "''" in t.replace("^{''}", '') or '`' in t:
            print(mn, s['page'], s['id'], t[:160])
