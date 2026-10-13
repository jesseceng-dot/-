"""seldiff.py specs_module id [tex-override]: per-glyph comparison of the
original paragraph with the re-typeset unedited skeleton (or given tex)."""
import sys, os, importlib, difflib
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, pymupdf, engine as E, para, run
mod = importlib.import_module(sys.argv[1])
s = [x for x in mod.SPECS if x['id'] == sys.argv[2]][0]
src = os.path.join(run.BASE, 'src/book.pdf')
pdf = pikepdf.open(src); doc = pymupdf.open(src); bf = E.BookFonts(pdf)
pn = s['page']; pe = E.PageEdit(pdf, pn, bf)
x_first = s.get('x') or para.first_text_x(pe, s['y'])
tex = sys.argv[3] if len(sys.argv) > 3 else (s.get('tex_orig') or run.skeleton(doc, pn, s['top'], s['bot'], x_first))
print(tex)
r = para.retypeset(pe, x_first, s['top'], s['bot'], tex, 'seldiff', extra=s.get('extra', ''), xmin_other=s.get('xmin_other'),
                   dry=True, verbose=False, levels=s.get('levels', True))
for i, b in enumerate(r['nbase']):
    if i >= len(r['obase']):
        print('line %d extra' % i); continue
    ob = r['obase'][i]
    o = sorted(r['orows'][ob], key=lambda g: (g.x, g.y)); n = sorted(r['nrows'][b], key=lambda g: (g['x'], g['y']))
    a = [g.uni for g in o]; bb = [g['uni'] for g in n]
    sm = difflib.SequenceMatcher(a=a, b=bb, autojunk=False)
    print('--- line %d %s' % (i, 'changed' if i in r['changed'] else 'same'))
    if i not in r['changed']:
        continue
    prev = None; out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                g, h = o[i1 + k], n[j1 + k]
                dx = h['x'] - g.x; dy = (h['y'] - b) - (g.y - ob)
                mark = ''
                if prev is None or abs(dx - prev) > 0.05 or abs(dy) > 0.05:
                    mark = '%s[%+.2f%s]' % (g.uni or '?', dx, (',%+.2f' % dy) if abs(dy) > 0.05 else '')
                out.append(mark or (g.uni or '?'))
                prev = dx
        else:
            out.append(' <%s %r/%r> ' % (tag, ''.join(x or '?' for x in a[i1:i2]), ''.join(x or '?' for x in bb[j1:j2])))
    print(''.join(out))
