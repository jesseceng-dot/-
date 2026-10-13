import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, engine as E
from collections import Counter
pdf = pikepdf.open('src/book.pdf'); bf = E.BookFonts(pdf)
cnt = Counter(); ex = {}
for pn in range(int(sys.argv[1]), int(sys.argv[2]) + 1):
    pe = E.PageEdit(pdf, pn, bf)
    gl = [g for g in pe.glyphs if g.size > 10]
    for g in gl:
        if g.font.name.startswith('CMMI10') and g.code == 59:   # math comma
            nxt = [h for h in gl if abs(h.y - g.y) < 0.05 and h.x > g.x + 0.1 and h.x - (g.x + g.adv) < 6]
            if not nxt:
                continue
            h = min(nxt, key=lambda h: h.x)
            if not h.font.name.startswith(('CMMI', 'CMR', 'CMSY')):
                continue
            gap = round(h.x - (g.x + g.adv), 1)
            cnt[gap] += 1; ex.setdefault(gap, (pn, round(g.x), round(g.y)))
for k, v in sorted(cnt.items()):
    print(k, v, ex[k])
