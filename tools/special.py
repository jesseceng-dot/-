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
    """Full-page cover: the image is fitted inside the page; the remaining space is filled with the image's own edge
    colours so the cover looks seamless."""
    im = Image.open(os.path.join(IMG_DIR, name))
    w, h = im.size
    pw, ph = style.PAGE_W, style.PAGE_H
    c = lambda t: f'rgb({t[0]},{t[1]},{t[2]})'
    ih = pw * h / w
    if ih > ph:                                   # taller than the page: fit height, fill left/right
        iw = ph * w / h
        x = (pw - iw) / 2
        left = _avg(im, (0, 0, 3, h))
        right = _avg(im, (w - 3, 0, w, h))
        return (f'<div style="position:absolute;left:0;top:0;width:{x + 0.5}pt;height:{ph}pt;background:{c(left)}"></div>'
                f'<div style="position:absolute;left:{x + iw - 0.5}pt;top:0;width:{pw - x - iw + 1}pt;height:{ph}pt;background:{c(right)}"></div>'
                f'<img src="{img_url(name)}" style="position:absolute;left:{x}pt;top:0;width:{iw}pt;height:{ph}pt">')
    top = _avg(im, (0, 0, w, 3))
    bot = _avg(im, (0, h - 3, w, h))
    y = (ph - ih) * valign
    return (f'<div style="position:absolute;left:0;top:0;width:{pw}pt;height:{y + 0.5}pt;background:{c(top)}"></div>'
            f'<div style="position:absolute;left:0;top:{y + ih - 0.5}pt;width:{pw}pt;height:{ph - y - ih + 1}pt;background:{c(bot)}"></div>'
            f'<img src="{img_url(name)}" style="position:absolute;left:0;top:{y}pt;width:{pw}pt;height:{ih}pt">')


def _center(text, y, size, family='SongBody', weight=400, ls=0.0, color='#000', w=None, extra=''):
    w = w or style.PAGE_W
    return (f'<div style="position:absolute;left:0;top:0;width:{w}pt;text-align:center;white-space:nowrap;'
            f'font-family:{family};font-size:{size}pt;font-weight:{weight};letter-spacing:{ls}em;color:{color};'
            f'transform:translate(0pt,{y}pt);{extra}">{text}</div>')


def half_title_html(title):
    return _center(_html.escape(title), 190, min(20.0, 300.0 / (len(title) * 1.1)), 'HeiTi', 700, 0.08)


def title_html(meta):
    """Formal title page: author, title, translator, series, publisher."""
    out = ''
    out += _center(_html.escape(meta['author']), 96, 13, 'KaiTi', 400, 0.12)
    fs = min(32.0, 300.0 / (len(meta['title']) * 1.1))
    out += _center(_html.escape(meta['title']), 176, fs, 'HeiTi', 700, 0.1)
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


def ads_html(items, heading=''):
    """Back-matter page with book covers, captions and their (external) purchase links – kept from the original ebook."""
    out = ''
    cols, cw = 3, 96.0
    gx = (style.TEXT_W - cols * cw) / (cols - 1)
    y0 = 120
    if heading:
        out += _center(_html.escape(heading), 76, 12, 'HeiTi', 700, 0.2)
    for k, (img, cap, url) in enumerate(items):
        col, row = k % cols, k // cols
        x = style.LEFT + col * (cw + gx)
        y = y0 + row * 210
        im = Image.open(os.path.join(IMG_DIR, img))
        ih = cw * im.size[1] / im.size[0]
        out += (f'<img src="{img_url(img)}" style="position:absolute;left:0;top:0;width:{cw}pt;height:{ih:.1f}pt;'
                f'transform:translate({x:.1f}pt,{y}pt);box-shadow:0 0 2pt #999">')
        out += (f'<div style="position:absolute;left:0;top:0;width:{cw}pt;text-align:center;font-family:SongBody;'
                f'font-size:8.5pt;line-height:11pt;transform:translate({x:.1f}pt,{y + ih + 8:.1f}pt)">{_html.escape(cap)}</div>')
        out += (f'<div style="position:absolute;left:0;top:0;width:{cw}pt;text-align:center;'
                f'font-family:HeiTi;font-size:8pt;transform:translate({x:.1f}pt,{y + ih + 8 + 24:.1f}pt)">'
                f'<a href="{_html.escape(url)}" style="color:#1a44c8;text-decoration:underline">纸书购买链接</a></div>')
    return out


def plate_html(n, img, ref_anchor, caption, builder=None, page=None):
    """One back-of-book plate: caption, the image scaled to the text block, and a return link to the reference in the text."""
    from .style import LINK_BASE
    im = Image.open(os.path.join(IMG_DIR, img))
    w, h = im.size
    box_w, box_h = style.TEXT_W, 388.0
    s = min(box_w / w, box_h / h)
    iw, ih = w * s, h * s
    x = style.LEFT + (style.TEXT_W - iw) / 2
    y = style.TOP + 34
    out = _center(_html.escape(caption), style.TOP + 6, 10.5, 'HeiTi', 700, 0.12)
    out += (f'<img src="{img_url(img)}" style="position:absolute;left:0;top:0;width:{iw:.2f}pt;height:{ih:.2f}pt;'
            f'transform:translate({x:.2f}pt,{y:.2f}pt);outline:.4pt solid #bbb">')
    label = ''
    if builder is not None and ref_anchor in builder.anchors:
        pi = builder.anchors[ref_anchor][0]
        lab = builder.pages[pi].label
        label = f'（第{lab}页）'
    out += (f'<div style="position:absolute;left:0;top:0;width:{style.PAGE_W}pt;text-align:center;font-family:HeiTi;'
            f'font-size:9.5pt;transform:translate(0pt,{style.TOP + style.TEXT_H - 4}pt)">'
            f'<a href="{LINK_BASE}{ref_anchor}" style="color:#1a44c8">↩ 返回正文{label}</a></div>')
    return out


def plate_divider_html(title, note):
    return (_center(_html.escape(title), 180, 17, 'HeiTi', 700, 0.3) +
            f'<div style="position:absolute;left:{style.LEFT + 30}pt;top:0;width:{style.TEXT_W - 60}pt;text-align:center;'
            f'font-family:SongBody;font-size:9.5pt;line-height:17pt;color:#333;transform:translate(0pt,232pt)">{_html.escape(note)}</div>')
