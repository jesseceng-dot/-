import sys, pymupdf
import numpy as np
from PIL import Image
def diff_boxes(pa, pb, pn, dpi=100, thr=40):
    da=pymupdf.open(pa); db=pymupdf.open(pb)
    ia=da[pn-1].get_pixmap(dpi=dpi); ib=db[pn-1].get_pixmap(dpi=dpi)
    A=np.frombuffer(ia.samples,dtype=np.uint8).reshape(ia.height,ia.width,ia.n)[:,:,:3].astype(int)
    Bm=np.frombuffer(ib.samples,dtype=np.uint8).reshape(ib.height,ib.width,ib.n)[:,:,:3].astype(int)
    d=np.abs(A-Bm).max(axis=2)>thr
    ys,xs=np.nonzero(d)
    if len(ys)==0: return None
    s=72/dpi
    return (xs.min()*s, ys.min()*s, xs.max()*s, ys.max()*s, int(d.sum()))
if __name__=='__main__':
    print(diff_boxes(sys.argv[1],sys.argv[2],int(sys.argv[3])))
