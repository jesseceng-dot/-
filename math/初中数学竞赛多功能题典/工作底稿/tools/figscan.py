import pymupdf, re, json, sys
doc=pymupdf.open('src/book.pdf')
items=[]  # (page, y, kind, data)
for i,p in enumerate(doc):
    # exercise labels
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines',[]):
            t=''.join(s['text'] for s in l['spans'])
            m=re.search(r'练习\s*(\d+\.\d+)',t)
            if m and l['spans'][0]['font'].startswith('STHeiti'):
                items.append((i+1,l['bbox'][1],'ex',m.group(1)))
            if re.search(r'^第.+章',t.strip()) and l['spans'][0]['size']>15:
                items.append((i+1,l['bbox'][1],'chap',t.strip()))
    for im in p.get_image_info():
        r=im['bbox']
        if r[3]-r[1]>15: items.append((i+1,r[1],'fig','img'))
    # vector drawings: cluster those not header rules
    ds=[d for d in p.get_drawings() if d['rect'].height>2 or d['rect'].width<400]
    ds=[d for d in ds if not (d['rect'].y1<62 or d['rect'].y0>790)]
    if len(ds)>=3:
        ys=sorted(d['rect'].y0 for d in ds)
        items.append((i+1,ys[0],'fig','vec%d'%len(ds)))
items.sort(key=lambda t:(t[0],t[1]))
# text per exercise
text={}
cur=None
for i,p in enumerate(doc):
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines',[]):
            t=''.join(s['text'] for s in l['spans'])
            m=re.search(r'练习\s*(\d+\.\d+)',t)
            if m and l['spans'][0]['font'].startswith('STHeiti'): cur=m.group(1); text[cur]=''
            if cur: text[cur]+=t
res=[]
for k,(pg,y,kind,d) in enumerate(items):
    if kind!='ex': continue
    t=text.get(d,'')
    if not re.search(r'如图|图中|见图|图\s*\(|下图|右图|左图',t): continue
    # look forward to next ex/chap
    has=False
    for pg2,y2,kind2,d2 in items[k+1:]:
        if kind2 in ('ex','chap'): break
        if kind2=='fig': has=True;break
    # also figure placed before label on same page? check previous item
    if not has:
        prev=items[k-1] if k>0 else None
        res.append((pg,d,t[:60]))
for r in res: print(r)
print(len(res))
