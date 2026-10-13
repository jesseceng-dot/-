import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, engine as E
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf = pikepdf.open(os.path.join(B, sys.argv[1] if len(sys.argv) > 1 else 'src/book.pdf')); bf = E.BookFonts(pdf)
tot = 0; pages = {}
for pn in range(1, len(pdf.pages) + 1):
    pe = E.PageEdit(pdf, pn, bf)
    gl = sorted([g for g in pe.glyphs if g.size > 9], key=lambda g: (round(E.gy(g)), g.x))
    for i, g in enumerate(gl):
        if not (g.font.name.startswith('CMSY10') and g.uni in '|∣'):
            continue
        nxt = [h for h in gl if abs(E.gy(h) - E.gy(g)) < 0.5 and 0 <= h.x - (g.x + g.adv) < 1.0 and h is not g]
        prv = [h for h in gl if abs(E.gy(h) - E.gy(g)) < 0.5 and 0 <= g.x - (h.x + h.adv) < 1.0 and h is not g]
        for h in nxt:
            if h.uni in '−+<>=≤≥':
                # a closing bar (preceded by an operand) followed by an operator with no space
                if prv and prv[0].uni not in '−+<>=≤≥(,':
                    pages.setdefault(pn, []).append(round(E.gy(g)))
                    tot += 1
print('total', tot)
for p, ys in sorted(pages.items()):
    print(p, len(ys), sorted(set(ys), reverse=True)[:6])
