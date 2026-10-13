import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, engine as E
from collections import Counter
pdf = pikepdf.open(sys.argv[1]); bf = E.BookFonts(pdf)
pages = range(int(sys.argv[2]), int(sys.argv[3]) + 1)
cnt = Counter(); ex = {}
for pn in pages:
    pe = E.PageEdit(pdf, pn, bf)
    big = [g for g in pe.glyphs if g.size > 10 and g.font.name.startswith(('CMMI', 'CMR')) ]
    small = [g for g in pe.glyphs if 7.5 < g.size < 8.5 and g.font.name.startswith(('CMR8', 'CMMI8'))]
    for s in small:
        left = [b for b in big if 0 < s.x - (b.x + b.adv) < 0.8 and 1.5 < s.y - b.y < 6]
        if not left:
            continue
        b = max(left, key=lambda b: b.x)
        # is the base glyph in a text line (CJK on same baseline)?
        cjk = any(abs(g.y - b.y) < 0.05 and g.font.name.startswith('STSong') for g in pe.glyphs)
        d = round(s.y - b.y, 2)
        cnt[(cjk, d)] += 1
        ex.setdefault((cjk, d), pn)
for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])[:20]:
    print(k, v, 'e.g. p%d' % ex[k])
