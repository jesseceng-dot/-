import sys, pymupdf
sys.path.insert(0,'tools')
import vis
from collections import defaultdict, Counter
doc=pymupdf.open('src/book.pdf')
STD={10.91,7.97,5.98,9.96,14.35,17.22}
res=[]
for pn in range(1,len(doc)+1):
    page=doc[pn-1]
    vg,rules,dr=vis.visible_glyphs(page)
    # lines by baseline
    byb=defaultdict(list)
    for g in vg:
        if g['c'] in (' ',''): continue
        byb[round(g['oy']*2)/2].append(g)
    for b,gs in byb.items():
        gs.sort(key=lambda g:g['x0'])
        for a,c in zip(gs,gs[1:]):
            ov=a['x1']-c['x0']
            if ov>0.8 and a['size']>9 and c['size']>9 and not (a['font']=='CMEX10' or c['font']=='CMEX10'):
                # ignore combining negation slash etc
                if a['c'] in '̸' or c['c'] in '̸': continue
                res.append((pn,'OVERLAP',round(b,1),round(a['x0'],1),a['c']+c['c'],a['font'],c['font'],round(ov,2)))
    for g in vg:
        s=round(g['size'],2)
        if s not in STD and g['font'] not in ('CMEX10',):
            res.append((pn,'SIZE',round(g['oy'],1),round(g['x0'],1),g['c'],g['font'],s))
        if g['font']=='ArialMT':
            res.append((pn,'ARIAL',round(g['oy'],1),round(g['x0'],1),g['c']))
for r in res: print(*r)
print(Counter(r[1] for r in res))
