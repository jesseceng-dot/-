"""ruledbg.py spec_module id : compare rules of book vs unedited skeleton typeset"""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, pymupdf, engine as E, para, run
src = os.path.join(run.BASE, 'src/book.pdf')
pdf = pikepdf.open(src); doc = pymupdf.open(src); bf = E.BookFonts(pdf)
m = importlib.import_module(sys.argv[1]); s = [x for x in m.SPECS if x['id'] == sys.argv[2]][0]
pe = E.PageEdit(pdf, s['page'], bf)
x = s.get('x') or para.first_text_x(pe, s['y'])
tex = s.get('tex_orig') or run.skeleton(doc, s['page'], s['top'], s['bot'], x)
gl, rules = para.typeset(x, tex, 'ruledbg')
nbase = para.cluster_baselines(gl, lambda g: g['font'], E.gy, True)
og = [g for g in pe.glyphs if s['bot'] <= E.gy(g) <= s['top']]
obase = para.cluster_baselines(og, lambda g: g.font.name, E.gy, True)
print('obase', obase, 'nbase', nbase)
for r in rules:
    print('NEW rule', [round(v, 2) for v in r['bbox']], r['paint'], round(r['lw'], 3), 'rel', round((r['bbox'][1] + r['bbox'][3]) / 2 - min(nbase, key=lambda b: abs(b - (r['bbox'][1] + r['bbox'][3]) / 2)), 2))
for it in pe.items:
    if it.kind == 'path' and it.bbox[3] - it.bbox[1] < 1.0 and s['bot'] - 5 <= it.bbox[1] <= s['top'] + 5:
        yc = (it.bbox[1] + it.bbox[3]) / 2
        print('OLD rule', [round(v, 2) for v in it.bbox], it.paint, it.lw, 'rel', round(yc - min(obase, key=lambda b: abs(b - yc)), 2))
