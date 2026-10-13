"""blocks.py page...: segment pages into paragraphs and print geometry + skeleton"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, pymupdf, engine as E, para, totex, survey
H = 841.89
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf = pikepdf.open(os.path.join(B, 'src/book.pdf')); doc = pymupdf.open(os.path.join(B, 'src/book.pdf')); bf = E.BookFonts(pdf)
for pn in map(int, sys.argv[1:]):
    pe = E.PageEdit(pdf, pn, bf)
    L = [l for l in survey.paragraphs(doc, pn) if 60 < l[0] < 780]
    blocks = []
    for y, x, t in L:
        lab = t.startswith('✍')
        cont = blocks and not lab and abs(x - E.LM) < 3 and 17.5 < blocks[-1][-1][0] - y < 19.5
        if cont:
            blocks[-1].append((y, x, t))
        else:
            blocks.append([(y, x, t)])
    print('=== p%d' % pn)
    for b in blocks:
        y0 = b[0][0]; y1 = b[-1][0]; t0 = b[0][2]
        if t0.startswith('✍'):
            fx = para.first_text_x(pe, y0)
        else:
            fx = b[0][1]
        if fx is None:
            print('  [label only] y=%.2f %s' % (y0, t0[:60])); continue
        if b[0][1] > 150 and len(b) == 1 and not t0.startswith('✍'):
            print('  [display?] y=%.2f x=%.2f %s' % (y0, b[0][1], t0[:80])); continue
        top, bot = y0 + 9, y1 - 9
        try:
            sk = totex.paragraph_tex(doc, pn, H - top, H - bot, fx)
        except Exception as e:
            sk = 'ERR %s' % e
        # angle check: plain-TeX \\angle = scriptsize slash (CMSY8 code 54) + short rule
        nsl = len([g for g in pe.glyphs if g.font.name.startswith('CMSY8') and g.code == 54 and bot <= g.y <= top and g.x >= fx - 0.5])
        nan = sk.count('\\angle') + sk.count('\\not')
        warn = '' if nsl == sk.count('\\angle') else '  [ANGLES: %d slashes in book, %d \\angle in skeleton]' % (nsl, sk.count('\\angle'))
        print('  y=%.2f x=%.3f top=%.0f bot=%.0f n=%d%s\n    %s' % (y0, fx, top, bot, len(b), warn, sk))
