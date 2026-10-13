"""skx.py page x_first|- y top bot : skeleton with explicit first x ('-' = after label)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, pymupdf, engine as E, para, totex
H = 841.89
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf = pikepdf.open(os.path.join(B, 'src/book.pdf')); doc = pymupdf.open(os.path.join(B, 'src/book.pdf')); bf = E.BookFonts(pdf)
a = sys.argv[1:]
for i in range(0, len(a), 5):
    pn = int(a[i]); y = float(a[i + 2]); top = float(a[i + 3]); bot = float(a[i + 4])
    pe = E.PageEdit(pdf, pn, bf)
    fx = para.first_text_x(pe, y) if a[i + 1] == '-' else float(a[i + 1])
    print('p%d y=%.2f x=%.3f top=%s bot=%s\n  %s' % (pn, y, fx, a[i + 3], a[i + 4], totex.paragraph_tex(doc, pn, H - top, H - bot, fx)))
