import sys, pymupdf
sys.path.insert(0,'tools')
import vis
doc=pymupdf.open('src/book.pdf')
tot=0
for pn in range(1,len(doc)+1):
    p=doc[pn-1]
    draws=vis._drawings(p)
    whites=[dr for dr in draws if dr['fill'] is not None and all(abs(c-1)<1e-3 for c in dr['fill'][:3])]
    if not whites: continue
    trace=p.get_texttrace()
    slashes=[]
    for sp in trace:
        if sp['size']>9: continue
        for ch in sp['chars']:
            if ch[0]==0x338: slashes.append((sp['seqno'],ch[2][0],ch[2][1]))
    allr=[]
    for dr in p.get_drawings():
        for it in dr['items']:
            if it[0]=='l' and abs(it[1].y-it[2].y)<0.05: allr.append((dr['seqno'],min(it[1].x,it[2].x),max(it[1].x,it[2].x),it[1].y))
            if it[0]=='re' and it[1].height<1.0: allr.append((dr['seqno'],it[1].x0,it[1].x1,(it[1].y0+it[1].y1)/2))
    bad=[]
    for (s,ox,oy) in slashes:
        # is this slash inside a white box drawn before it? (i.e. part of overlay)
        cover=[w for w in whites if w['seq']<s and w['rect'].x0-1<=ox+2<=w['rect'].x1+1 and w['rect'].y0-1<=oy<=w['rect'].y1+1]
        if not cover: continue
        wseq=max(w['seq'] for w in cover)
        ok=any(rs>wseq and abs(rx0-(ox+3.9))<1.5 and 0.5<=ry-oy<=3.0 for (rs,rx0,rx1,ry) in allr)
        if not ok: bad.append((round(ox,1),round(oy,1)))
    if bad:
        bad=sorted(set(bad)); tot+=len(bad)
        print(pn, bad)
print('total',tot)
