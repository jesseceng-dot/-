import sys, pymupdf
sys.path.insert(0,'tools')
import vis
from collections import defaultdict
doc=pymupdf.open('src/book.pdf')
def chars_all(page):
    out=[]
    for sp in page.get_texttrace():
        for ch in sp['chars']:
            out.append((chr(ch[0]) if ch[0] else '', ch[2][0], ch[2][1], sp['font'], sp['size'], sp['seqno'], pymupdf.Rect(ch[3])))
    return out
pages=[int(a) for a in sys.argv[1:]] or range(1,len(doc)+1)
for pn in pages:
    page=doc[pn-1]
    draws=vis._drawings(page)
    whites=[dr for dr in draws if dr['fill'] is not None and all(abs(c-1)<1e-3 for c in dr['fill'][:3])]
    if not whites: continue
    vg,_,_=vis.visible_glyphs(page)
    tc=chars_all(page)
    for w in whites:
        r=w['rect']
        hid=[c for c in tc if c[5]<w['seq'] and r.x0-0.2<= (c[6].x0+c[6].x1)/2 <= r.x1+0.2 and r.y0-0.2<=(c[6].y0+c[6].y1)/2<=r.y1+0.2]
        # only main-content chars (not from fullpage xobjects): approximate by clip-visible set ignoring occlusion
        hid.sort(key=lambda c:(round(c[2]),c[1]))
        vis_in=[g for g in vg if r.x0-0.5<=(g['x0']+g['x1'])/2<=r.x1+0.5 and r.y0-0.5<=(g['y0']+g['y1'])/2<=r.y1+0.5]
        vis_in.sort(key=lambda g:(round(g['oy']),g['x0']))
        hs=''.join(c[0] for c in hid)
        vs=''.join(g['c'] for g in vis_in)
        print(f'p{pn} [{r.x0:.0f},{r.y0:.0f},{r.x1:.0f},{r.y1:.0f}] seq{w["seq"]}\n   OLD: {hs[:200]}\n   NEW: {vs[:200]}')
