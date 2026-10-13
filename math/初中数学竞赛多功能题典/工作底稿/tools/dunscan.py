"""dunscan.py first last [min_gap]: list 、 preceded by a math glyph with a gap (word space)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, engine as E
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf = pikepdf.open(os.environ.get('SRC', os.path.join(B, 'src/book.pdf'))); bf = E.BookFonts(pdf)
mg = float(sys.argv[3]) if len(sys.argv) > 3 else 1.8
tot = 0
for pn in range(int(sys.argv[1]), int(sys.argv[2]) + 1):
    pe = E.PageEdit(pdf, pn, bf)
    gl = [g for g in pe.glyphs if g.size > 4]
    hits = []
    for g in gl:
        if g.uni != '、' or g.size < 9:
            continue
        prev = [h for h in gl if abs(E.gy(h) - E.gy(g)) < 4 and h.x < g.x - 0.1 and g.x - (h.x + h.adv) < 8 and h is not g]
        if not prev:
            continue
        h = max(prev, key=lambda h: h.x + h.adv)
        gap = g.x - (h.x + h.adv)
        if gap > mg and h.font.name.startswith(('CM', 'MSAM')):
            hits.append((round(E.gy(g), 1), round(h.x, 1), h.uni, round(gap, 2)))
    if hits:
        tot += len(hits)
        print(pn, len(hits), sorted(hits, key=lambda t: (-t[0], t[1])))
print('total', tot)
