"""Static pages: covers, half-title, title page, image plates, advertisement page."""
import os
import html as _html
from PIL import Image
from . import style

IMG_DIR = os.path.join(style.SCRATCH, 'unpack/x/mobi8/OEBPS/Images')


def img_url(name):
    return 'file://' + os.path.join(IMG_DIR, name)


def _avg(im, box):
    px = list(im.crop(box).convert('RGB').getdata())
    n = len(px)
    return tuple(sum(p[i] for p in px) // n for i in range(3))


def cover_html(name, valign=0.5):
    """Full-page cover: the image is fitted to the page width; the space above/below is filled with the image's own
    edge colours so the cover looks seamless."""
    im = Image.open(os.path.join(IMG_DIR, name))
    w, h = im.size
    top = _avg(im, (0, 0, w, 3))
    bot = _avg(im, (0, h - 3, w, h))
    pw, ph = style.PAGE_W, style.PAGE_H
    ih = pw * h / w
    if ih > ph:                                   # taller than the page: fit height instead
        iw = ph * w / h
        x, y, ww, hh = (pw - iw) / 2, 0, iw, ph
    else:
        x, y, ww, hh = 0, (ph - ih) * valign, pw, ih
    c = lambda t: f'rgb({t[0]},{t[1]},{t[2]})'
    return (f'<div style="position:absolute;left:0;top:0;width:{pw}pt;height:{y + 0.5}pt;background:{c(top)}"></div>'
            f'<div style="position:absolute;left:0;top:{y + hh - 0.5}pt;width:{pw}pt;height:{ph - y - hh + 1}pt;background:{c(bot)}"></div>'
            f'<img src="{img_url(name)}" style="position:absolute;left:{x}pt;top:{y}pt;width:{ww}pt;height:{hh}pt">')


def _center(text, y, size, family='SongBody', weight=400, ls=0.0, color='#000', w=None, extra=''):
    w = w or style.PAGE_W
    return (f'<div style="position:absolute;left:0;top:0;width:{w}pt;text-align:center;white-space:nowrap;'
            f'font-family:{family};font-size:{size}pt;font-weight:{weight};letter-spacing:{ls}em;color:{color};'
            f'transform:translate(0pt,{y}pt);{extra}">{text}</div>')


def half_title_html(title):
    return _center(_html.escape(title), 190, 20, 'HeiTi', 700, 0.08)


def title_html(meta):
    """Formal title page: author, title, translator, series, publisher."""
    out = ''
    out += _center(_html.escape(meta['author']), 96, 13, 'KaiTi', 400, 0.12)
    out += _center(_html.escape(meta['title']), 176, 32, 'HeiTi', 700, 0.1)
    if meta.get('sub'):
        out += _center(_html.escape(meta['sub']), 224, 13, 'KaiTi', 400, 0.06)
    y = 288
    for line in meta.get('credits', []):
        out += _center(_html.escape(line), y, 13, 'KaiTi', 400, 0.16)
        y += 26
    out += f'<div style="position:absolute;left:{style.PAGE_W / 2 - 24}pt;top:0;width:48pt;border-top:.6pt solid #000;transform:translate(0pt,{y + 8}pt)"></div>'
    out += _center(_html.escape(meta.get('series', '')), y + 26, 11, 'HeiTi', 500, 0.3)
    out += _center(_html.escape(meta.get('publisher', '')), style.PAGE_H - 100, 12, 'HeiTi', 500, 0.2)
    return out


def volume_title_html(title, vol):
    return (_center(_html.escape(title), 200, 30, 'HeiTi', 700, 0.1) +
            _center(_html.escape(vol), 260, 20, 'KaiTi', 700, 0.4))
