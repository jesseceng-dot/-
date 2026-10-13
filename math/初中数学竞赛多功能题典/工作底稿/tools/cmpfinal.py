import sys, os, importlib
sys.path.insert(0, os.path.dirname(__file__))
import vdiff
outs = {'specs1': 'out1_new.pdf', 'specs_a': 'outA_new.pdf', 'specs_b': 'outB_new.pdf', 'specs_c': 'outC_new.pdf',
        'specs_d': 'outD_new.pdf', 'specs_e': 'outE.pdf', 'specs_f': 'outF.pdf', 'specs_g': 'outG.pdf',
        'specs_h': 'outH.pdf', 'specs_i': 'outI.pdf', 'specs_j': 'outJ.pdf', 'specs_k': 'outK.pdf', 'specs_l': 'outL.pdf', 'specs_fig': 'outFig.pdf'}
pages = {}
for m in outs:
    for s in importlib.import_module(m).SPECS:
        pages.setdefault(s['page'], set()).add(m)
multi = {p: ms for p, ms in pages.items() if len(ms) > 1}
print('pages with several batches:', sorted(multi.items()))
bad = []
for p, ms in sorted(pages.items()):
    if len(ms) > 1:
        continue
    m = next(iter(ms))
    b = vdiff.diff_boxes(outs[m], 'final.pdf', p, dpi=100, thr=40)
    if b is not None:
        bad.append((p, m, tuple(round(v) for v in b[:4])))
print('single-batch pages differing from their batch output:', bad)
# pages not edited must equal the source
import pymupdf
n = len(pymupdf.open('src/book.pdf'))
diff_unedited = []
for p in range(1, n + 1):
    if p in pages:
        continue
    if vdiff.diff_boxes('src/book.pdf', 'final.pdf', p, dpi=60, thr=40) is not None:
        diff_unedited.append(p)
print('unedited pages that differ from the source:', diff_unedited)
