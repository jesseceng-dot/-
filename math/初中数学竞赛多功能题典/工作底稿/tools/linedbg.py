"""linedbg.py spec_module id line : per-glyph comparison of book line vs unedited skeleton typeset"""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, pymupdf, engine as E, para, run
src = os.path.join(run.BASE, 'src/book.pdf')
pdf = pikepdf.open(src); doc = pymupdf.open(src); bf = E.BookFonts(pdf)
m = importlib.import_module(sys.argv[1]); s = [x for x in m.SPECS if x['id'] == sys.argv[2]][0]
li = int(sys.argv[3])
pe = E.PageEdit(pdf, s['page'], bf)
x = s.get('x') or para.first_text_x(pe, s['y'])
tex = sys.argv[4] if len(sys.argv) > 4 else (s.get('tex_orig') or run.skeleton(doc, s['page'], s['top'], s['bot'], x))
r = para.retypeset(pe, x, s['top'], s['bot'], tex, 'linedbg', dry=True, verbose=False, keep_same_text=False,
                   single_y=s['y'] if s.get('single') else None, orig_base=s.get('obase'))
ob = r['obase'][li]; nb = r['nbase'][li]
o = sorted(r['orows'][ob], key=lambda g: (g.x, g.y)); n = sorted(r['nrows'][nb], key=lambda g: (g['x'], g['y']))
print('counts', len(o), len(n))
for a, c in zip(o, n):
    flag = '' if para.same_char(a, c) and abs(a.size - c['size']) <= 0.1 and abs((a.y - ob) - (c['y'] - nb)) <= 0.08 and abs(a.x - c['x']) <= 0.08 else '  <<<'
    print('%-3s %-3s x %.3f %.3f dy %.3f %.3f sz %.2f %.2f %s %s%s' % (a.uni, c['uni'], a.x, c['x'], a.y - ob, c['y'] - nb, a.size, c['size'], a.font.name[:8], c['font'][:8], flag))
