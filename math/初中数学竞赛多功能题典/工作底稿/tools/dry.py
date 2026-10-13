"""dry-run a paragraph retypeset: python3 tools/dry.py page x y top bot 'tex' [levels]"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, engine as E, para
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.environ.get('SRC', os.path.join(B, 'src/book.pdf'))
pdf = pikepdf.open(src); bf = E.BookFonts(pdf)
pn = int(sys.argv[1]); x = sys.argv[2]; y = float(sys.argv[3]); top = float(sys.argv[4]); bot = float(sys.argv[5]); tex = sys.argv[6]
levels = (sys.argv[7] != '0') if len(sys.argv) > 7 else True
pe = E.PageEdit(pdf, pn, bf)
x = para.first_text_x(pe, y) if x == '-' else float(x)
r = para.retypeset(pe, x, top, bot, tex, 'dry_%d' % pn, dry=True, levels=levels)
for i, b in enumerate(r['nbase']):
    print('%d %s %.2f %s' % (i, '*' if i in r['changed'] else ' ', b, ''.join(g['uni'] for g in sorted(r['nrows'][b], key=lambda g: g['x']))))
