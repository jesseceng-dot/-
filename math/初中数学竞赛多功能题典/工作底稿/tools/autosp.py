"""autosp.py first last : spec stubs (xtol=0.3, no edits) for paragraphs that have a
word space before an enumeration comma (、) after a math glyph"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, pymupdf, engine as E, para, survey
H = 841.89
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf = pikepdf.open(os.path.join(B, 'src/book.pdf')); doc = pymupdf.open(os.path.join(B, 'src/book.pdf')); bf = E.BookFonts(pdf)
for pn in range(int(sys.argv[1]), int(sys.argv[2]) + 1):
    pe = E.PageEdit(pdf, pn, bf)
    gl = [g for g in pe.glyphs if g.size > 4]
    hits = []
    for g in gl:
        if g.uni != '、' or g.size < 9:
            continue
        prev = [h for h in gl if abs(E.gy(h) - E.gy(g)) < 4 and h.x < g.x - 0.1 and g.x - (h.x + h.adv) < 8]
        if not prev:
            continue
        h = max(prev, key=lambda h: h.x + h.adv)
        if g.x - (h.x + h.adv) > 1.8 and h.font.name.startswith(('CM', 'MSAM')):
            hits.append(E.gy(g))
    if not hits:
        continue
    L = [l for l in survey.paragraphs(doc, pn) if 60 < l[0] < 780]
    blocks = []
    for y, x, t in L:
        lab = t.startswith('✍')
        cont = blocks and not lab and abs(x - E.LM) < 3 and 17.5 < blocks[-1][-1][0] - y < 19.5
        if cont:
            blocks[-1].append((y, x, t))
        else:
            blocks.append([(y, x, t)])
    done = set()
    for hy in hits:
        for b in blocks:
            y0 = b[0][0]; y1 = b[-1][0]
            if y1 - 3 <= hy <= y0 + 3 and (pn, y0) not in done:
                done.add((pn, y0))
                x = '' if b[0][2].startswith('✍') else ', x=%.3f' % b[0][1]
                print(" dict(page=%d, id='sp%d_%d'%s, y=%.2f, top=%.0f, bot=%.0f, xtol=0.3, edits=[]),  # %s" % (pn, pn, round(y0), x, y0, y0 + 9, y1 - 9, b[0][2][:40]))
