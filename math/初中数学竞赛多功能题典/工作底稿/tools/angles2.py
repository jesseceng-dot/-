import sys, pymupdf, numpy as np
doc=pymupdf.open('src/book.pdf')
DPI=300; S=DPI/72
res=[]
for pn in range(1,len(doc)+1):
    p=doc[pn-1]
    cands=[]
    for sp in p.get_texttrace():
        if sp['size']>9: continue
        for ch in sp['chars']:
            if ch[0]==0x338:
                ox,oy=ch[2]
                if 0<oy<842: cands.append((ox,oy))
    if not cands: continue
    pix=p.get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
    a=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width)
    seen=set()
    for ox,oy in cands:
        key=(round(ox,1),round(oy,1))
        if key in seen: continue
        seen.add(key)
        # slash ink region: x in [ox, ox+4], y in [oy-6, oy]
        x0,x1=int(ox*S),int((ox+4.5)*S); y0,y1=int((oy-6)*S),int((oy+0.2)*S)
        slash=(a[y0:y1,x0:x1]<128).sum()
        if slash<10: continue   # slash not visible at all
        # rule: y in [oy-0.3, oy+1.2], x in [ox+0.8, ox+4]
        ry0,ry1=int((oy+0.9)*S),int((oy+2.6)*S); rx0,rx1=int((ox+4.4)*S),int((ox+7.4)*S)
        reg=(a[ry0:ry1,rx0:rx1]<128)
        rowmax=reg.sum(axis=1).max() if reg.size else 0
        if rowmax < (rx1-rx0)*0.7:
            res.append((pn,round(ox,1),round(oy,1),int(rowmax),rx1-rx0))
for r in res: print(*r)
print(len(res))
