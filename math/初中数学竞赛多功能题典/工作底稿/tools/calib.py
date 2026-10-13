import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, pdfedit, texlayout as T
from difflib import SequenceMatcher
PDF = None
def book():
    global PDF
    if PDF is None:
        PDF = pikepdf.open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src/book.pdf'))
    return PDF

def orig_glyphs(pn, y0, y1):
    """visible-ish glyphs of page pn with baseline in [y0,y1] (PDF y-up)"""
    pdf = book()
    ops, gl, it = pdfedit.interpret(pdf, pdf.pages[pn-1])
    out = [dict(font=g.font.name, code=g.code, uni=g.uni, x=g.x, y=g.y, size=g.size, adv=g.adv) for g in gl if y0 <= g.y <= y1]
    return out

def compare(orig, new, label=''):
    """align by (uni,font) sequences sorted by y then x"""
    def key(g): return (round(-g['y'], 0), g['x'])
    a = sorted(orig, key=key); b = sorted(new, key=key)
    sa = [(g['uni'], g['font'][:6]) for g in a]; sb = [(g['uni'], g['font'][:6]) for g in b]
    sm = SequenceMatcher(None, sa, sb, autojunk=False)
    dx = []; dy = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for i, j in zip(range(i1, i2), range(j1, j2)):
                dx.append(b[j]['x'] - a[i]['x']); dy.append(b[j]['y'] - a[i]['y'])
        else:
            print(label, tag, ''.join(x[0] for x in sa[i1:i2]), '->', ''.join(x[0] for x in sb[j1:j2]))
    if dx:
        print(label, 'matched', len(dx), 'of', len(a), len(b), 'max|dx|', round(max(abs(v) for v in dx), 3), 'dy range', round(min(dy), 3), round(max(dy), 3))
    return dx, dy
