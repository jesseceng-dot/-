import sys, os, importlib
sys.path.insert(0, os.path.dirname(__file__))
import vdiff
for k, mod in [('1', 'specs1'), ('A', 'specs_a'), ('B', 'specs_b'), ('C', 'specs_c'), ('D', 'specs_d')]:
    m = importlib.import_module(mod)
    pages = sorted({s['page'] for s in m.SPECS})
    diffs = []
    for pn in pages:
        b = vdiff.diff_boxes('out%s.pdf' % k, 'out%s_new.pdf' % k, pn, dpi=100, thr=40)
        if b is not None:
            diffs.append((pn, tuple(round(v) for v in b[:4])))
    print(k, len(pages), 'pages; changed:', diffs)
