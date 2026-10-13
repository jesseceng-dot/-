"""crop.py pdf out.png page:ytop:ybot[:x0:x1] ... (PDF y-up coords), dpi via DPI env"""
import sys, os, pymupdf
from PIL import Image, ImageDraw
H = 841.89
dpi = int(os.environ.get('DPI', 160))
doc = pymupdf.open(sys.argv[1]); out = sys.argv[2]
ims = []
for spec in sys.argv[3:]:
    p = spec.split(':')
    pn, yt, yb = int(p[0]), float(p[1]), float(p[2])
    x0, x1 = (float(p[3]), float(p[4])) if len(p) > 4 else (30, 565)
    r = pymupdf.Rect(x0, H - yt, x1, H - yb)
    pm = doc[pn - 1].get_pixmap(dpi=dpi, clip=r)
    im = Image.frombytes('RGB', (pm.width, pm.height), pm.samples)
    c = Image.new('RGB', (im.width, im.height + 12), 'white'); d = ImageDraw.Draw(c)
    d.text((2, 0), 'p%d %s' % (pn, spec), fill=(200, 0, 0)); c.paste(im, (0, 12))
    ims.append(c)
W = max(i.width for i in ims); Ht = sum(i.height + 6 for i in ims)
o = Image.new('RGB', (W, Ht), (150, 150, 150)); y = 0
for i in ims:
    o.paste(i, (0, y)); y += i.height + 6
o.save(out); print(o.size)
