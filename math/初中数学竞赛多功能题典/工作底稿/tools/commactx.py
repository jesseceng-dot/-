import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, engine as E
pdf = pikepdf.open('src/book.pdf'); bf = E.BookFonts(pdf)
n0 = n1 = 0
for pn in range(int(sys.argv[1]), int(sys.argv[2]) + 1):
    pe = E.PageEdit(pdf, pn, bf)
    gl = [g for g in pe.glyphs if g.size > 6]
    for g in gl:
        if g.font.name.startswith('CMMI10') and g.code == 59:
            row = sorted([h for h in gl if abs(h.y - g.y) < 6 and abs(h.x - g.x) < 40], key=lambda h: h.x)
            nxt = [h for h in row if abs(h.y - g.y) < 0.05 and h.x > g.x + 0.1]
            if not nxt: continue
            h = nxt[0]
            if not h.font.name.startswith(('CMMI', 'CMR', 'CMSY')): continue
            gap = h.x - (g.x + g.adv)
            ctx = ''.join(x.uni or '?' for x in row)
            k = 'ORD ' if gap < 0.5 else 'PUN '
            if (k == 'ORD ' and n0 < 12) or (k == 'PUN ' and n1 < 12):
                print(k, 'p%d' % pn, ctx)
                if k == 'ORD ': n0 += 1
                else: n1 += 1
