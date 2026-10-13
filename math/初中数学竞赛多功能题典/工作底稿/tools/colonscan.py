import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, engine as E
from collections import Counter
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf = pikepdf.open(os.path.join(B, 'src/book.pdf')); bf = E.BookFonts(pdf)
cnt = Counter(); ex = {}
for pn in range(int(sys.argv[1]), int(sys.argv[2]) + 1):
    pe = E.PageEdit(pdf, pn, bf)
    gl = [g for g in pe.glyphs if g.size > 9]
    for g in gl:
        if g.uni != '：':
            continue
        nxt = [h for h in gl if abs(h.y - g.y) < 0.05 and h.x > g.x + 0.1 and h.x - g.x < 20]
        if not nxt:
            continue
        h = min(nxt, key=lambda h: h.x)
        kind = 'math' if h.font.name.startswith(('CM', 'MSAM')) else ('cjk' if h.font.name.startswith('ST') else 'other')
        d = round(h.x - g.x, 1)
        cnt[(kind, d)] += 1; ex.setdefault((kind, d), []).append(pn)
for k, v in sorted(cnt.items()):
    print(k, v, ex[k][:8])
