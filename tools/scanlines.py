"""Text that the ebook sets as pictures, set line by line on the text grid.

Book 71: the reference lists of 城镇化与增长 are scans of the English original.  Book 65: 空间经济学 shows most of its
derivations as pictures, passages of text with displayed equations among them (scans of the printed book, and pages a
reviser set again in LaTeX).  Each picture is cut into its lines, and each line takes one slot of the text grid (a line
taller than that, a fraction or a sum with its limits: as many slots as it needs, centred in them), its baseline on the
grid's baseline: the passage runs on from page to page like text, no page foot is left blank, facing pages keep one
baseline grid.

The scale: `fit` (book 71) the widest line of the scan is a full justified line of the original: the scan to the text
width; otherwise the pictures of one kind share one scale (C['scan_scale']: (width up to, pt per pixel) pairs, by the
width of the picture: book 65, the scans 10.5/24.3, the LaTeX pages 10.5/38.5, three scans of 2400 px and more 10.5/79,
the pitch of their characters measured, so that the characters are the size of the text's).
A line is the band of rows with ink between two white gaps (small bands, the limits of a sum, the parts of a fraction,
go with the line they belong to), shown through a window cut in the middle of those gaps; the picture itself is embedded
once (render.py).  Lines are set flush left with their own indent; a run of lines indented far (the displayed formulas
of the scans, centred there) is centred as a group; an equation number at the right edge of the picture goes to the
right edge of the text block.
Book 72: the notes that are pictures of text, on the small grid of the notes, their characters the size of the notes',
indented as the notes' text, the note's number beside the first line."""
import math
import os
import numpy as np
from PIL import Image
from . import style, special

INK = 128            # a pixel darker than this is ink (the grey frame lines of some scans are lighter)
_CACHE = {}


def _bands(rows):
    out, start = [], None
    for y, v in enumerate(list(rows) + [False]):
        if v and start is None:
            start = y
        elif not v and start is not None:
            out.append([start, y])
            start = None
    merged = []
    for b in out:
        if merged and b[0] - merged[-1][1] <= 3:          # accents, a dash or an underline a row or two off its line
            merged[-1][1] = b[1]
        else:
            merged.append(b)
    return merged


def _attach_small(bands, med):
    """Bands much lower than a line of text (a sum's limits, a fraction's numerator, a superscript standing alone) join
    the nearer of their neighbours, when it is close."""
    bands = [list(b) for b in bands]
    changed = True
    while changed and len(bands) > 1:
        changed = False
        for i, (t, b) in enumerate(bands):
            if b - t >= 0.6 * med:
                continue
            up = t - bands[i - 1][1] if i else 1e9
            dn = bands[i + 1][0] - b if i + 1 < len(bands) else 1e9
            j = i - 1 if up <= dn else i + 1
            if min(up, dn) > 0.6 * med:
                continue
            lo, hi = sorted((i, j))
            bands[lo:hi + 1] = [[bands[lo][0], bands[hi][1]]]
            changed = True
            break
    return bands


def lines(src, scale=None, attach=False):
    """The lines of a picture: dict(scale=pt per px, x0, x1=ink extent in px, w=, h= picture size in px,
    lines=[dict(top, bot, base, it, ib, segs)] in px; top and bot in the middle of the white around the line, it/ib the
    ink, segs the column runs of ink [(x0, x1)])."""
    key = (src, scale, attach)
    if key in _CACHE:
        return _CACHE[key]
    im = Image.open(os.path.join(special.IMG_DIR, src))
    if im.mode in ('RGBA', 'LA', 'P'):
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
        bg.alpha_composite(im.convert('RGBA'))
        im = bg
    a = np.array(im.convert('L'))
    ink = a < INK
    H, W = ink.shape
    rule = ink.sum(1) > 0.8 * W                           # a frame line across the scan: not text
    ink[rule] = False
    cols = np.where(ink.any(0))[0]
    bands = _bands(ink.any(1))
    hts = sorted(b - t for t, b in bands)
    med = hts[len(hts) // 2]
    bands = [b for b in bands if b[1] - b[0] > 0.25 * med or ink[b[0]:b[1]].sum() > 0.2 * med * med]   # specks
    if attach:
        txt = sorted(b - t for t, b in bands if b - t >= 0.6 * med) or hts
        bands = _attach_small(bands, txt[len(txt) // 2])
    else:
        split = []
        for t, b in bands:                                # two lines touching (a descender on an ascender): cut at the
            if b - t > 1.7 * med:                         # emptiest row near the middle
                cnt = ink[t:b].sum(1)
                mid = (b - t) // 2
                k = t + mid // 2 + int(np.argmin(cnt[mid // 2:mid + mid // 2]))
                split += [[t, k], [k + 1, b]]
            else:
                split.append([t, b])
        bands = split
    gaps = [bands[i + 1][0] - bands[i][1] for i in range(len(bands) - 1)]
    g = sorted(gaps)[len(gaps) // 2] if gaps else med // 2
    out = []
    for i, (t, b) in enumerate(bands):
        cnt = ink[t:b].sum(1)
        core = np.where(cnt >= 0.35 * cnt.max())[0]
        base = t + int(core[-1]) + 1                      # the foot of the x-height: the rows below are descenders
        top = (bands[i - 1][1] + t) / 2 if i else max(0, t - g / 2)
        bot = (b + bands[i + 1][0]) / 2 if i + 1 < len(bands) else min(H, b + g / 2)
        c = ink[t:b].any(0)
        segs, s0 = [], None
        for x, v in enumerate(list(c) + [False]):
            if v and s0 is None:
                s0 = x
            elif not v and s0 is not None:
                segs.append((s0, x))
                s0 = None
        out.append(dict(top=top, bot=bot, base=base, it=t, ib=b, segs=segs))
    s = scale or style.TEXT_W / (cols[-1] + 1 - cols[0])
    res = dict(scale=s, x0=int(cols[0]), x1=int(cols[-1]) + 1, w=W, h=H, lines=out, med=med)
    _CACHE[key] = res
    return res


def ruled(src):
    """The longest horizontal stroke of a picture, as a share of the width of its ink: a table's rules and a graph's axes
    run across most of it (0.5 and more), the bar of a fraction in a formula does not."""
    key = ('ruled', src)
    if key not in _CACHE:
        a = np.array(Image.open(os.path.join(special.IMG_DIR, src)).convert('L')) < INK
        cols = np.where(a.any(0))[0]
        span = cols[-1] - cols[0] + 1 if len(cols) else a.shape[1]
        best = 0
        for row in a:
            if not row.any():
                continue
            x = np.flatnonzero(np.diff(np.concatenate(([0], row.astype(np.int8), [0]))))
            cur = None
            for s0, e0 in zip(x[::2], x[1::2]):
                cur = (cur[0], e0) if cur and s0 - cur[1] <= 2 else (s0, e0)
                best = max(best, cur[1] - cur[0])
        _CACHE[key] = best / span
    return _CACHE[key]


def _scale(C, src):
    rules = C.get('scan_scale')
    if not rules:
        return None
    w = special.img_size(src)[0]
    return next(s for wmax, s in rules if w <= wmax)


def blocks(src, C=None, pitch=None, fs=None, indent=0.0, cls='s-body', centre=True):
    """Image blocks for the lines of a picture, one per line, a slot high or more (render.py draws each line's window
    of the picture, `scan`).  pitch, fs: the grid's and the type's (the notes': their small grid, their 8.5 pt);
    indent: of every line (the notes' text); cls: the style class whose baseline the lines sit on; centre: the far
    indented lines centred (not in a note: there each line keeps its place in the picture)."""
    C = C or {}
    pitch, fs = pitch or style.LINE, fs or style.FONT
    s0 = _scale(C, src)
    s0 = s0 * fs / style.FONT if s0 else s0
    L = lines(src, s0, attach=bool(s0))
    s = L['scale']
    x0, x1 = L['x0'], L['x1']
    span = x1 - x0
    W = style.TEXT_W - indent
    rows = []
    for ln_ in L['lines']:
        segs = ln_['segs']
        num = None
        if s0 and len(segs) > 1:                          # an equation number: a short run of ink at the right edge, far
            k = len(segs) - 1                             # from the rest
            while k > 1 and segs[k][0] - segs[k - 1][1] < 0.02 * span:
                k -= 1
            if segs[k][0] - segs[k - 1][1] >= 0.06 * span and segs[-1][1] - segs[k][0] <= 0.16 * span \
                    and segs[-1][1] >= x1 - 0.04 * span:
                num = (segs[k][0], segs[-1][1])
                segs = segs[:k]
        m0, m1 = segs[0][0], segs[-1][1]
        rows.append(dict(ln_, m0=m0, m1=m1, num=num, disp=bool(s0) and centre and m0 - x0 > 0.12 * span))
    if s0 and centre and L['h'] < 250 and len(rows) <= 3:            # (book 65) a picture of a displayed formula alone: centred
        for r in rows:
            r['disp'] = True
    i = 0
    while i < len(rows):                                  # a run of far indented lines: centred as a group
        if not rows[i]['disp']:
            i += 1
            continue
        j = i
        while j + 1 < len(rows) and rows[j + 1]['disp']:
            j += 1
        g0, g1 = min(r['m0'] for r in rows[i:j + 1]), max(r['m1'] for r in rows[i:j + 1])
        for r in rows[i:j + 1]:
            r['gx'] = (W - (g1 - g0) * s) / 2 - (g0 - x0) * s     # the group's left edge, from the text block's
        i = j + 1
    out = []
    for r in rows:
        gx = r.get('gx')
        left = r['m0'] if gx is not None else x0          # where the line's window starts in the picture (px)
        dx = gx + (r['m0'] - x0) * s if gx is not None else 0.0
        numw = (r['num'][1] - r['num'][0] + 2) * s if r['num'] else 0.0
        room = W - (numw + 6.0 if r['num'] else 0.0)
        f = 1.0
        if dx + (r['m1'] - left + 2) * s > room:          # a line too wide for the text block: flush left, smaller
            dx = 0.0
            f = max(0.7, room / ((r['m1'] - left + 2) * s))
        sl = s * f
        pieces = [(round(left * sl, 2), round((r['m1'] - left + 2) * sl, 2), round(indent + dx, 2))]
        if r['num']:
            nw = (r['num'][1] - r['num'][0] + 2) * sl
            pieces.append((round(r['num'][0] * sl, 2), round(nw, 2), round(indent + W - nw, 2)))
        asc, desc = (r['base'] - r['it']) * sl, (r['ib'] - r['base']) * sl
        one = asc <= 11.5 / 17.0 * pitch and desc <= 4.6 / 17.0 * pitch      # (at the body's 17 pt: 11.5 and 4.6 pt)
        n = 1 if one else max(1, math.ceil(((r['ib'] - r['it']) * sl + 3.0 * pitch / 17.0) / pitch))
        out.append(dict(k='img', style='center', runs=[], src=special.img_url(src), w=round(W, 2),
                        h=round(n * pitch, 2), n=n, float=0,
                        scan=dict(fw=round(L['w'] * sl, 2), fh=round(L['h'] * sl, 2), top=round(r['top'] * sl, 2),
                                  wh=round((r['bot'] - r['top']) * sl, 2), base=round((r['base'] - r['top']) * sl, 2),
                                  ink=(round((r['it'] - r['top']) * sl, 2), round((r['ib'] - r['it']) * sl, 2)),
                                  mid=0 if one else 1, pieces=pieces, end=round(indent + dx + (r['m1'] - left) * sl, 2),
                                  cls=cls)))
    return out
