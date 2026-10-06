"""Static pages: covers, half-title, title page, image plates, advertisement page."""
import math
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
    return _center(_html.escape(title), 190 * style.SY, min(20.0, 300.0 / (len(title) * 1.1)), 'HeiTi', 700, 0.08)


def title_html(meta):
    """Formal title page: author, title, translator, series, publisher."""
    out = ''
    out += _center(_html.escape(meta['author']), 96 * style.SY, 13, 'KaiTi', 400, 0.12)
    fs = min(32.0, 300.0 / (len(meta['title']) * 1.1))
    out += _center(_html.escape(meta['title']), 176 * style.SY, fs, 'HeiTi', 700, 0.1)
    if meta.get('sub'):
        out += _center(_html.escape(meta['sub']), 224 * style.SY, 13, 'KaiTi', 400, 0.06)
    y = 288 * style.SY
    for line in meta.get('credits', []):
        out += _center(_html.escape(line), y, 13, 'KaiTi', 400, 0.16)
        y += 26
    out += f'<div style="position:absolute;left:{style.PAGE_W / 2 - 24}pt;top:0;width:48pt;border-top:.6pt solid #000;transform:translate(0pt,{y + 8}pt)"></div>'
    out += _center(_html.escape(meta.get('series', '')), y + 26, 11, 'HeiTi', 500, 0.3)
    out += _center(_html.escape(meta.get('publisher', '')), style.PAGE_H - 100, 12, 'HeiTi', 500, 0.2)
    return out


def volume_title_html(title, vol):
    return (_center(_html.escape(title), 200 * style.SY, 30, 'HeiTi', 700, 0.1) +
            _center(_html.escape(vol), 260 * style.SY, 20, 'KaiTi', 700, 0.4))


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
    box_w, box_h = style.TEXT_W, style.TEXT_H - 71.0
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
    return (_center(_html.escape(title), 180 * style.SY, 17, 'HeiTi', 700, 0.3) +
            f'<div style="position:absolute;left:{style.LEFT + 30}pt;top:0;width:{style.TEXT_W - 60}pt;text-align:center;'
            f'font-family:SongBody;font-size:9.5pt;line-height:17pt;color:#333;transform:translate(0pt,{232 * style.SY}pt)">{_html.escape(note)}</div>')


# ------------------------------------------------------------------------------------------ Kant: dividers and packed plate pages
PLATE_CAP, PLATE_LINK, PLATE_GAP = 18.0, 16.0, 14.0


def plate_size(img, extra=0.0):
    """Scaled size (pt) of a plate image: as wide as the text block, at most (text height - 71 pt) high, small figures magnified a little.
    `extra` is the height taken by a long caption above the figure."""
    if img.startswith('table:'):
        from . import kant_tables
        return kant_tables.size(img)
    w, h = Image.open(os.path.join(IMG_DIR, img)).size
    s = min(style.TEXT_W / w, (style.TEXT_H - 71.0 - extra) / h, 1.6 if w < 300 else 1.0)
    return w * s, h * s


def divider_html(lines):
    """Title page of a work / section: (level, text) lines, the first one large; other short lines (epigraph, sub-title, name)
    smaller underneath.  Long titles get balanced line breaks."""
    from . import normalize
    from .model import run, runs_html
    out, y = '', 176.0 * style.SY
    first = True
    for lvl, text in lines:
        if lvl == 97:
            y += 26.0                                     # (a space before an epigraph)
            continue
        if not text.strip():
            continue
        if lvl <= 1.0:
            fam, fs, wt, ls, lh, gap = 'HeiTi', 24.0, 700, 0.08, 34.0, 20.0
        elif lvl <= 2.0:
            fam, fs, wt, ls, lh, gap = 'KaiTi', 16.0, 700, 0.06, 25.0, 12.0
        elif lvl < 50:
            fam, fs, wt, ls, lh, gap = 'KaiTi', 13.0, 700, 0.04, 21.0, 8.0
        else:
            fam, fs, wt, ls, lh, gap = 'KaiTi', 10.5, 400, 0.02, 17.0, 2.0
        cap = (style.TEXT_W - 20) * 0.92 / fs
        wtxt = sum(normalize._w(ch) for ch in text)
        if '\u3000' in text and wtxt > cap and text.index('\u3000') < len(text) - 2:
            i = text.index('\u3000')
            runs = [run(text[:i]), run('\n'), run(text[i + 1:])]      # break after the ordinal ('第一部分 / 审美判断力的批判')
            rest = normalize.balance_title([run(text[i + 1:])], fs, style.TEXT_W - 20, slack=0.92)
            if len(rest) > 1:
                runs = [run(text[:i]), run('\n')] + rest
        else:
            runs = normalize.balance_title([run(text)], fs, style.TEXT_W - 20, slack=0.92)
        n = 1 + sum(1 for r in runs if r['t'] == '\n')
        body = runs_html(runs)
        out += (f'<div style="position:absolute;left:0;top:0;width:{style.PAGE_W}pt;text-align:center;font-family:{fam};'
                f'font-size:{fs}pt;font-weight:{wt};letter-spacing:{ls}em;line-height:{lh}pt;color:#000;'
                f'transform:translate(0pt,{y:.1f}pt)">{body}</div>')
        y += n * lh + gap
    return out


def _caption_height(text, fs=9.5, width=None):
    """Estimated height (pt) of a wrapped caption: CJK glyph = 1 em, Latin = 0.5 em."""
    width = width or (style.TEXT_W - 30)
    w = sum(fs if ord(c) > 0x2e80 else fs * 0.5 for c in text)
    return max(1, math.ceil(w / width * 1.06)) * 14.0


def plates_page_html(k, img, builder, page, caption=''):
    """One back-of-book plate per page (same page design as the Hegel plates): caption 'Plate N' at the top, the figure
    right below it, and the return link to the reference in the text at the foot of the text block.  The plate anchor
    (plate-N) is registered here so that the link in the text lands on this page.  A long caption is set as a wrapped
    block under the 'Plate N' line and pushes the figure down."""
    from .style import LINK_BASE
    long_cap = len(caption) > 24
    extra = (_caption_height(caption) + 6.0) if long_cap else 0.0
    iw, ih = plate_size(img, extra)
    x = style.LEFT + (style.TEXT_W - iw) / 2
    y = style.TOP + 34 + extra
    builder.anchors[f'plate-{k}'] = (page.index, style.TOP)
    if long_cap:
        out = _center(_html.escape(f'插图 {k}'), style.TOP + 6, 10.5, 'HeiTi', 700, 0.12)
        out += (f'<div style="position:absolute;left:0;top:0;width:{style.TEXT_W - 30}pt;text-align:justify;'
                f'font-family:KaiTi;font-size:9.5pt;line-height:14pt;transform:translate({style.LEFT + 15}pt,{style.TOP + 26}pt)">'
                f'{_html.escape(caption)}</div>')
    else:
        out = _center(_html.escape(f'插图 {k}' + (f'　{caption}' if caption else '')), style.TOP + 6, 10.5, 'HeiTi', 700, 0.12)
    if img.startswith('table:'):
        from . import kant_tables
        for a in kant_tables.anchors(img):
            builder.anchors[a] = (page.index, y)
        out += (f'<div style="position:absolute;left:0;top:0;transform:translate({x:.2f}pt,{y:.2f}pt)">'
                f'{kant_tables.html(img)}</div>')
    else:
        out += (f'<img src="{img_url(img)}" style="position:absolute;left:0;top:0;width:{iw:.2f}pt;height:{ih:.2f}pt;'
                f'transform:translate({x:.2f}pt,{y:.2f}pt);outline:.4pt solid #bbb">')
    ref = f'figref-{k}'
    label = ''
    if ref in builder.anchors:
        label = f'（第{builder.pages[builder.anchors[ref][0]].label}页）'
    out += (f'<div style="position:absolute;left:0;top:0;width:{style.PAGE_W}pt;text-align:center;font-family:HeiTi;'
            f'font-size:9.5pt;transform:translate(0pt,{style.TOP + style.TEXT_H - 4}pt)">'
            f'<a href="{LINK_BASE}{ref}" style="color:#1a44c8">↩ 返回正文{label}</a></div>')
    return out
