"""pair.py a.pdf b.pdf out.png page:ytop:ybot[:x0:x1] ... — before/after crops stacked"""
import sys, os, pymupdf
from PIL import Image, ImageDraw
H = 841.89
dpi = int(os.environ.get('DPI', 150))
da, db = pymupdf.open(sys.argv[1]), pymupdf.open(sys.argv[2]); out = sys.argv[3]
ims = []
for spec in sys.argv[4:]:
    p = spec.split(':')
    pn, yt, yb = int(p[0]), float(p[1]), float(p[2])
    x0, x1 = (float(p[3]), float(p[4])) if len(p) > 4 else (50, 545)
    r = pymupdf.Rect(x0, H - yt, x1, H - yb)
    for tag, d in (('old', da), ('new', db)):
        pm = d[pn - 1].get_pixmap(dpi=dpi, clip=r)
        im = Image.frombytes('RGB', (pm.width, pm.height), pm.samples)
        c = Image.new('RGB', (im.width + 70, im.height), 'white'); dr = ImageDraw.Draw(c)
        dr.text((2, 2), 'p%d %s' % (pn, tag), fill=(200, 0, 0) if tag == 'new' else (0, 0, 200)); c.paste(im, (70, 0))
        ims.append(c)
W = max(i.width for i in ims); Ht = sum(i.height + 3 for i in ims)
o = Image.new('RGB', (W, Ht), (150, 150, 150)); y = 0
for k, i in enumerate(ims):
    o.paste(i, (0, y)); y += i.height + (3 if k % 2 == 0 else 8)
o.save(out); print(o.size)
