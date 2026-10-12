import sys, pymupdf
sys.path.insert(0,'tools')
import vis
doc=pymupdf.open('src/book.pdf')
out=[]
for pn in range(1,len(doc)+1):
    p=doc[pn-1]
    draws=vis._drawings(p)
    whites=[dr for dr in draws if dr['fill'] is not None and all(abs(c-1)<1e-3 for c in dr['fill'][:3])]
    _,rules,_=vis.visible_glyphs(p)
    for sp in p.get_texttrace():
        if not sp['font'].startswith('CMSY') and 'Computer Modern' not in sp['font']: continue
        if sp['size']>9: continue
        for ch in sp['chars']:
            if ch[0]!=0x338: continue
            ox,oy=ch[2]; bb=pymupdf.Rect(ch[3])
            cx,cy=(bb.x0+bb.x1)/2,(bb.y0+bb.y1)/2
            if any(w['seq']>sp['seqno'] and w['rect'].contains(pymupdf.Point(cx,cy)) for w in whites): continue
            ok=any(abs(r['x0']-ox)<3.5 and -1.0<=r['y']-oy<=3.0 and r['x1']-r['x0']<8 for r in rules)
            if not ok: out.append((pn,round(ox,1),round(oy,1)))
for o in out: print(*o)
print(len(out))
