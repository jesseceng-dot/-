"""lines.py x_first 'tex' : typeset a paragraph and print its lines (first/last glyph x)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import para, engine as E
x = float(sys.argv[1]); tex = sys.argv[2]
gl, rules = para.typeset(x, tex, 'lines')
nb = para.cluster_baselines(gl, lambda g: g['font'], E.gy, True)
rows = para.assign(gl, nb, E.gy)
for b in nb:
    r = sorted(rows[b], key=lambda g: g['x'])
    print('%.2f  %.2f..%.2f  %s' % (b, r[0]['x'], r[-1]['x'] + r[-1]['adv'], ''.join(g['uni'] for g in r)))
