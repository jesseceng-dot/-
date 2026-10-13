"""gdump.py page x0 y0 x1 y1 : dump glyphs and path items in region (PDF coords)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, engine as E
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.environ.get('SRC', os.path.join(B, 'src/book.pdf'))
pdf = pikepdf.open(src); bf = E.BookFonts(pdf)
pn = int(sys.argv[1]); x0, y0, x1, y1 = map(float, sys.argv[2:6])
pe = E.PageEdit(pdf, pn, bf)
for g in sorted(pe.glyphs_in(x0, y0, x1, y1), key=lambda g: (-round(E.gy(g)), g.x)):
    print('G op%-4d %-28s %-3r code=%-4d x=%8.3f y=%8.3f gy=%8.3f sz=%6.3f adv=%6.3f col=%s' % (g.op, g.font.name[:28], g.uni, g.code, g.x, g.y, E.gy(g), g.size, g.adv, tuple(round(c, 2) for c in g.color)))
for it in pe.items_in(x0, y0, x1, y1, full=False):
    print('I op%d-%d %s %s bbox=%s col=%s lw=%s' % (it.op0, it.op1, it.kind, getattr(it, 'paint', getattr(it, 'name', '')), tuple(round(v, 2) for v in it.bbox), tuple(round(c, 2) for c in (getattr(it, 'color', None) or ())), getattr(it, 'lw', None)))
