"""Pictures of PDF pages for a visual check.

    python -m tools.sheet <pdf> <out.png> [--pages 1-40|5,9,12] [--cols 10] [--dpi 30]     a contact sheet
    python -m tools.sheet <pdf> <out.png> --find 𤴯𫍰䷀ [--dpi 250]                          the lines holding these characters

Look at every page of a new book at least once on contact sheets (blank feet, broken headings, misplaced figures are
easy to see there), and at the lines of every transcribed glyph and symbol at a high resolution.
"""
import sys
import pymupdf
from PIL import Image, ImageDraw


def pages_arg(s, n):
    out = []
    for part in s.split(','):
        a, _, b = part.partition('-')
        out += list(range(int(a), int(b or a) + 1))
    return [p for p in out if 1 <= p <= n]


def contact(d, pages, cols, dpi):
    ims = []
    for p in pages:
        pix = d[p - 1].get_pixmap(dpi=dpi)
        ims.append((p, Image.frombytes('RGB', (pix.width, pix.height), pix.samples)))
    w, h = ims[0][1].size
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new('RGB', (cols * (w + 4), rows * (h + 14)), (110, 110, 110))
    dr = ImageDraw.Draw(sh)
    for k, (p, im) in enumerate(ims):
        x, y = (k % cols) * (w + 4), (k // cols) * (h + 14)
        sh.paste(im, (x, y + 12))
        dr.text((x + 2, y), str(p), fill='white')
    return sh


def find(d, chars, dpi):
    crops = []
    for pno, pg in enumerate(d):
        for b in pg.get_text('rawdict')['blocks']:
            for l in b.get('lines', []):
                cs = [c for s in l['spans'] for c in s['chars']]
                hit = next((c for c in cs if c['c'] in chars), None)
                if hit:
                    lb, cb = l['bbox'], hit['bbox']
                    clip = pymupdf.Rect(max(lb[0] - 4, 0), cb[1] - 6, min(lb[2] + 4, pg.rect.width), cb[3] + 6)
                    pix = pg.get_pixmap(dpi=dpi, clip=clip)
                    crops.append((pno + 1, Image.frombytes('RGB', (pix.width, pix.height), pix.samples)))
    if not crops:
        return None
    W = max(im.width for _, im in crops) + 60
    H = sum(im.height + 6 for _, im in crops)
    sh = Image.new('RGB', (W, H), 'white')
    dr = ImageDraw.Draw(sh)
    y = 0
    for p, im in crops:
        dr.text((2, y + 2), str(p), fill='red')
        sh.paste(im, (60, y))
        y += im.height + 6
    return sh


if __name__ == '__main__':
    a = sys.argv[1:]
    pdf, out = a[0], a[1]
    opt = lambda k, v: a[a.index(k) + 1] if k in a else v
    d = pymupdf.open(pdf)
    if '--find' in a:
        sh = find(d, opt('--find', ''), int(opt('--dpi', 250)))
        if sh is None:
            sys.exit('none of these characters is in the PDF')
    else:
        sh = contact(d, pages_arg(opt('--pages', f'1-{len(d)}'), len(d)), int(opt('--cols', 10)), int(opt('--dpi', 30)))
    sh.save(out)
    print(out, sh.size)
