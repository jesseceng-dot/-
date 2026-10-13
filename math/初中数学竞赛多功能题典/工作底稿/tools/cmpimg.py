import sys, os, pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
import vdiff
def cmp(pa, pb, pages, out, dpi=110, pad=14, full=False):
    da=pymupdf.open(pa); db=pymupdf.open(pb)
    ims=[]
    for pn in pages:
        box=vdiff.diff_boxes(pa,pb,pn)
        if box is None:
            continue
        x0,y0,x1,y1,_=box
        r=pymupdf.Rect(30, max(0,y0-pad), 565, min(842,y1+pad)) if not full else da[pn-1].rect
        a=da[pn-1].get_pixmap(dpi=dpi,clip=r); b=db[pn-1].get_pixmap(dpi=dpi,clip=r)
        A=Image.frombytes('RGB',(a.width,a.height),a.samples); B=Image.frombytes('RGB',(b.width,b.height),b.samples)
        W=A.width; H=A.height*2+24
        im=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(im)
        d.text((2,0),'p%d before'%pn,fill=(200,0,0)); im.paste(A,(0,10))
        d.text((2,A.height+12),'after',fill=(0,0,200)); im.paste(B,(0,A.height+22))
        ims.append(im)
    if not ims: return None
    W=max(i.width for i in ims); H=sum(i.height+8 for i in ims)
    o=Image.new('RGB',(W,H),(150,150,150)); y=0
    for i in ims: o.paste(i,(0,y)); y+=i.height+8
    o.save(out); return o.size
if __name__=='__main__':
    print(cmp(sys.argv[1],sys.argv[2],[int(p) for p in sys.argv[4:]],sys.argv[3]))
