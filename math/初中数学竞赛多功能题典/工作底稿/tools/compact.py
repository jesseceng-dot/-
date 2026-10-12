import sys, pymupdf, numpy as np
from PIL import Image, ImageDraw, ImageFont
def compact_page(doc, pn, dpi=120, gap=10):
    p=doc[pn-1]
    pix=p.get_pixmap(dpi=dpi)
    im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
    a=np.asarray(im.convert('L'))
    blank=(a>245).all(axis=1)
    rows=[]; i=0; H=a.shape[0]
    segs=[]
    while i<H:
        if blank[i]:
            j=i
            while j<H and blank[j]: j+=1
            segs.append(('b',i,j)); i=j
        else:
            j=i
            while j<H and not blank[j]: j+=1
            segs.append(('t',i,j)); i=j
    parts=[]
    for k,(t,i,j) in enumerate(segs):
        if t=='t': parts.append(im.crop((0,i,im.width,j)))
        else:
            if j-i>gap*3: 
                g=Image.new('RGB',(im.width,gap),'white'); d=ImageDraw.Draw(g)
                d.line((0,gap//2,im.width,gap//2),fill=(255,200,200))
                parts.append(g)
            else: parts.append(im.crop((0,i,im.width,j)))
    h=sum(x.height for x in parts)
    out=Image.new('RGB',(im.width,h),'white'); y=0
    for x in parts: out.paste(x,(0,y)); y+=x.height
    d=ImageDraw.Draw(out); d.text((4,4),f'p{pn}',fill=(255,0,0))
    return out
if __name__=='__main__':
    doc=pymupdf.open(sys.argv[1]); outp=sys.argv[2]; pns=[int(x) for x in sys.argv[3:]]
    ims=[compact_page(doc,pn) for pn in pns]
    W=max(i.width for i in ims); H=sum(i.height for i in ims)+6*len(ims)
    c=Image.new('RGB',(W,H),(180,180,180)); y=0
    for i in ims: c.paste(i,(0,y)); y+=i.height+6
    c.save(outp); print(c.size)
