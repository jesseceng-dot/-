"""Figure repairs: raster figure edits/redraws and a vector figure for 6.68."""
import os, sys, zlib, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pikepdf
from pikepdf import Name, Operator
import engine as E

FONT_IT = '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-italic.otf'
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_image(pdf, objnum):
    o = pdf.get_object((objnum, 0))
    return o, pikepdf.PdfImage(o).as_pil_image()


def replace_image(pdf, objnum, im):
    o = pdf.get_object((objnum, 0))
    w, h = int(o.Width), int(o.Height)
    assert im.size == (w, h), (im.size, w, h)
    if str(o.ColorSpace) == '/DeviceGray':
        im = im.convert('L')
    else:
        im = im.convert('RGB')
    o.write(zlib.compress(im.tobytes(), 9), filter=Name.FlateDecode)
    if '/DecodeParms' in o:
        del o['/DecodeParms']


def fix_1016(pe, doc, bf, report):
    # 10.16 (p214): caption "题10.2.5" of the scanned source book under the figure
    o, im = load_image(pe.pdf, 578)
    a = np.array(im.convert('L'))
    a[216:234, :] = 255
    replace_image(pe.pdf, 578, Image.fromarray(a))
    report.append('p214_10_16fig: caption removed from image 578')


def fix_1440(pe, doc, bf, report):
    # 14.40 (p289): the point is G in the text, G' in the figure
    o, im = load_image(pe.pdf, 752)
    a = np.array(im.convert('RGB'))
    a[259:275, 336:351, :] = 255
    replace_image(pe.pdf, 752, Image.fromarray(a))
    report.append("p289_14_40fig: prime after G removed from image 752")


def _lines_image(w, h, lines, width, ss=4, dashed=(), marks=(), labels=(), font_px=44):
    big = Image.new('L', (w * ss, h * ss), 255)
    d = ImageDraw.Draw(big)
    for (x0, y0), (x1, y1) in lines:
        d.line([(x0 * ss, y0 * ss), (x1 * ss, y1 * ss)], fill=0, width=int(round(width * ss)))
    for (x0, y0), (x1, y1), dash, gap in dashed:
        L = math.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / L, (y1 - y0) / L
        t = 0.0
        while t < L:
            t1 = min(t + dash, L)
            d.line([((x0 + ux * t) * ss, (y0 + uy * t) * ss), ((x0 + ux * t1) * ss, (y0 + uy * t1) * ss)], fill=0, width=int(round(width * ss)))
            t += dash + gap
    for pts in marks:
        d.line([(x * ss, y * ss) for x, y in pts], fill=0, width=int(round(width * 0.8 * ss)))
    if labels:
        f = ImageFont.truetype(FONT_IT, font_px * ss)
        for txt, (x, y) in labels:
            d.text((x * ss, y * ss), txt, font=f, fill=0)
    return big.resize((w, h), Image.LANCZOS)


def fix_2326(pe, doc, bf, report):
    # 23.26 (p421): counting marks of the solution printed on the figure; redrawn without them
    o, im = load_image(pe.pdf, 1021)
    w, h = im.size
    xs = [53.0, 131.3, 209.5, 287.8, 366.0]
    ys = [84.0, 162.6, 241.0, 319.0, 397.2]
    lines = [((x, ys[0]), (x, ys[-1])) for x in xs] + [((xs[0], y), (xs[-1], y)) for y in ys]
    for i in range(4):
        for j in range(4):
            lines.append(((xs[i], ys[j]), (xs[i + 1], ys[j + 1])))
            lines.append(((xs[i + 1], ys[j]), (xs[i], ys[j + 1])))
    replace_image(pe.pdf, 1021, _lines_image(w, h, lines, 3.2).convert('RGB'))
    report.append('p421_23_26fig: image 1021 redrawn without the counting marks')


def fig_1422_image(w=523, h=457):
    s = 40.0; ox, oy = 60.0, 370.0
    P = lambda x, y: (ox + s * x, oy - s * y)
    A, Bp, C = (3.5, 7.5), (0.0, 0.0), (10.0, 0.0)
    ab = math.hypot(3.5, 7.5); ac = math.hypot(6.5, 7.5)
    M = (10 * ab / (ab + ac), 0.0)
    u = (3.5 / ab, 7.5 / ab); t = M[0] * u[0]; Ep = (t * u[0], t * u[1])
    v = (-6.5 / ac, 7.5 / ac); t2 = (M[0] - 10) * v[0]; F = (10 + t2 * v[0], t2 * v[1])
    # intersection of CE and BF
    ex, ey = Ep; fx, fy = F
    s_ = 10 / (10 - ex + (ey * fx / fy))
    Pp = (10 + s_ * (ex - 10), s_ * ey)
    D = (Pp[0], 0.0)
    pa, pb, pc, pm, pe_, pf, pp, pd = [P(*q) for q in (A, Bp, C, M, Ep, F, Pp, D)]
    lines = [(pa, pb), (pb, pc), (pc, pa), (pa, pm), (pm, pe_), (pm, pf), (pc, pe_), (pb, pf), (pa, pp)]
    dashed = [(pp, pd, 9, 6)]
    def mark(at, to1, to2, k=14):
        u1 = (to1[0] - at[0], to1[1] - at[1]); l1 = math.hypot(*u1); u1 = (u1[0] / l1 * k, u1[1] / l1 * k)
        u2 = (to2[0] - at[0], to2[1] - at[1]); l2 = math.hypot(*u2); u2 = (u2[0] / l2 * k, u2[1] / l2 * k)
        return [(at[0] + u1[0], at[1] + u1[1]), (at[0] + u1[0] + u2[0], at[1] + u1[1] + u2[1]), (at[0] + u2[0], at[1] + u2[1])]
    marks = [mark(pe_, pa, pm), mark(pf, pa, pm)]
    labels = [('A', (pa[0] - 12, pa[1] - 52)), ('B', (pb[0] - 30, pb[1] + 6)), ('C', (pc[0] + 2, pc[1] + 6)),
              ('M', (pm[0] - 16, pm[1] + 6)), ('E', (pe_[0] - 40, pe_[1] - 30)), ('F', (pf[0] + 12, pf[1] - 34)),
              ('P', (pp[0] - 36, pp[1] - 58))]
    return _lines_image(w, h, lines, 4.0, dashed=dashed, marks=marks, labels=labels).convert('RGB'), dict(P=Pp, A=A)


def fix_1422(pe, doc, bf, report):
    # 14.22 (p283): the figure was a copy of the figure of 14.21; redrawn for this problem
    o, im = load_image(pe.pdf, 733)
    new, info = fig_1422_image(*im.size)
    replace_image(pe.pdf, 733, new)
    report.append('p283_14_22fig: image 733 redrawn (P=(%.3f, %.3f) on the altitude x=3.5)' % info['P'])


def _ops_path(pts, closed=False):
    ops = [([E.fmt(pts[0][0]), E.fmt(pts[0][1])], Operator('m'))]
    for x, y in pts[1:]:
        ops.append(([E.fmt(x), E.fmt(y)], Operator('l')))
    return ops


def _parabola_beziers(f, df, x0, x1, X, Y):
    """exact cubic Bezier pieces of y = f(x) on [x0, x1] (f quadratic), mapped by X, Y"""
    xm = (x0 + x1) / 2
    p0 = (x0, f(x0)); p2 = (x1, f(x1)); p1 = (xm, f(x0) + df(x0) * (xm - x0))
    c1 = (p0[0] + 2 / 3 * (p1[0] - p0[0]), p0[1] + 2 / 3 * (p1[1] - p0[1]))
    c2 = (p2[0] + 2 / 3 * (p1[0] - p2[0]), p2[1] + 2 / 3 * (p1[1] - p2[1]))
    return (X(p0[0]), Y(p0[1])), [(X(c1[0]), Y(c1[1])), (X(c2[0]), Y(c2[1])), (X(p2[0]), Y(p2[1]))]


def fig_668(pe, doc, bf, report, ox=125.0, oy=598.0, u=8.0):
    """6.68 (p143): the figure "图中实线表示的曲线" is missing: y = -|x^2/2 - 2x - 2|,
    with the reflected arcs of the original parabola dashed."""
    X = lambda x: ox + u * x
    Y = lambda y: oy + u * y
    f = lambda x: 0.5 * x * x - 2 * x - 2
    df = lambda x: x - 2
    g = lambda x: -f(x); dg = lambda x: -df(x)
    r1, r2 = 2 - 2 * math.sqrt(2), 2 + 2 * math.sqrt(2)
    ops = [([], Operator('q')), ([0, 0, 0], Operator('RG')), ([0, 0, 0], Operator('rg')), ([1], Operator('j')), ([1], Operator('J'))]
    # axes with arrow heads
    ops += [([E.fmt(0.45)], Operator('w'))]
    xa0, xa1, ya0, ya1 = X(-3.0), X(7.4), Y(-4.9), Y(5.0)
    ops += _ops_path([(xa0, oy), (xa1, oy)]) + [([], Operator('S'))]
    ops += _ops_path([(ox, ya0), (ox, ya1)]) + [([], Operator('S'))]
    ah = 3.2
    ops += _ops_path([(xa1 - ah, oy + ah * 0.42), (xa1, oy), (xa1 - ah, oy - ah * 0.42)]) + [([], Operator('h')), ([], Operator('f'))]
    ops += _ops_path([(ox - ah * 0.42, ya1 - ah), (ox, ya1), (ox + ah * 0.42, ya1 - ah)]) + [([], Operator('h')), ([], Operator('f'))]
    # solid curve: -|f| on [-2, 6]
    ops += [([E.fmt(0.75)], Operator('w'))]
    for a, b, fn, dfn in ((-2, r1, g, dg), (r1, 2, f, df), (2, r2, f, df), (r2, 6, g, dg)):
        p0, cs = _parabola_beziers(fn, dfn, a, b, X, Y)
        ops += [([E.fmt(p0[0]), E.fmt(p0[1])], Operator('m')),
                ([E.fmt(v) for c in cs for v in c], Operator('c')), ([], Operator('S'))]
    # dashed: the arcs of the original parabola above the x-axis
    ops += [([E.fmt(0.45)], Operator('w')), ([pikepdf.Array([2, 1.6]), 0], Operator('d'))]
    for a, b in ((-2, r1), (r2, 6)):
        p0, cs = _parabola_beziers(f, df, a, b, X, Y)
        ops += [([E.fmt(p0[0]), E.fmt(p0[1])], Operator('m')),
                ([E.fmt(v) for c in cs for v in c], Operator('c')), ([], Operator('S'))]
    ops += [([], Operator('Q'))]
    pe.new_ops += ops
    # labels (CMMI10 at 8.5pt, as in the other drawn figures)
    fobj = bf.get('CMMI10'); fi = E.FONTS.get(fobj, pe.pdf)
    sz = 8.5
    lab = [('x', xa1 - 1.0, oy - 8.2), ('y', ox + 2.6, ya1 - 5.6), ('O', ox + 1.6, oy - 8.2)]
    pe.emit_glyphs([dict(bookfont=fobj, code=fi.fromunicode[c], x=x, y=y, size=sz) for c, x, y in lab])
    report.append('p143_6_68fig: graph of y = -|x^2/2 - 2x - 2| drawn at origin (%.1f, %.1f)' % (ox, oy))
