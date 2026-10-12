import sys, pymupdf
sys.path.insert(0,'tools')
import vis
doc=pymupdf.open('src/book.pdf')
out=[]
for pn in range(1,len(doc)+1):
    page=doc[pn-1]
    vg,rules,dr=vis.visible_glyphs(page)
    gl=[g for g in vg if g['c'].strip() and g['font']!='bbding']
    for r in rules:
        if r['x1']-r['x0']>300 or r['y']<65 or r['y']>790: continue
        if r['color'] and sum(r['color'][:3])>0.3: continue
        x0,x1,y=r['x0'],r['x1'],r['y']
        if any(g['c'] in '√\ufffd' and abs(g['x1']-x0)<2.5 and g['y0']-3<=y<=g['y0']+6 for g in vg): continue
        if x1-x0<6 and any(g['c']=='\u0338' and abs(g['x0']-x0)<3 and abs(g['oy']-y)<4 for g in vg): continue
        inr=[g for g in gl if x0-0.5<=(g['x0']+g['x1'])/2<=x1+0.5]
        above=[g for g in inr if g['y1']<=y+1 and y-g['oy']<12 and g['oy']<y]
        below=[g for g in inr if g['oy']>y and g['y0']>=y-1.5 and g['oy']-y<14]
        # neighbors on same text line: glyphs left/right within 40pt horizontally
        nb=[g for g in gl if (g['x1']<x0-0.5 and x0-g['x1']<40 or g['x0']>x1+0.5 and g['x0']-x1<40) and abs(g['oy']-(y+3))<6 and g['size']>9]
        if not nb: continue
        from collections import Counter
        base=Counter(round(g['oy']) for g in nb).most_common(1)[0][0]
        if above and not below:
            # numerator only? numerator baseline well above line baseline
            ab=min(base-g['oy'] for g in above)
            if ab>4: out.append((pn,'NO-DENOM',round(x0,1),round(y,1),''.join(g['c'] for g in above)))
        if below and not above:
            bl=max(g['oy']-base for g in below)
            if bl>4: out.append((pn,'NO-NUMER',round(x0,1),round(y,1),''.join(g['c'] for g in below)))
        if not above and not below and x1-x0<60:
            out.append((pn,'EMPTY-RULE',round(x0,1),round(x1,1),round(y,1)))
for o in out: print(*o)
