"""Page editing engine: clear regions, re-typeset paragraphs with XeLaTeX
(using the book's own fonts/metrics) and write the result into the page with
the fonts already embedded in the book."""
import os, sys, math, copy
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf
from pikepdf import Name, Operator, Array, String
import pdfedit
from pdfedit import interpret, FONTS, mat_mul, apply
import texlayout as T

LM, RM = 56.693, 538.583


def fmt(v):
    return round(float(v), 4)


class BookFonts:
    """Index of the book's font objects by normalised base name."""
    def __init__(self, pdf):
        self.pdf = pdf
        self.by_name = {}
        for pg in pdf.pages:
            fr = pg.Resources.get('/Font', {})
            for k, v in fr.items():
                nm = norm_font_name(str(v.get('/BaseFont', '')))
                if nm not in self.by_name:
                    self.by_name[nm] = v

    def get(self, nm):
        return self.by_name.get(norm_font_name(nm))


def norm_font_name(b):
    b = b.lstrip('/')
    if '+' in b:
        b = b.split('+', 1)[1]
    b = b.replace('-Identity-H', '')
    low = b.lower()
    if low.startswith('stsongbook'):
        return 'STSong'
    if low.startswith('stheitibook'):
        return 'STHeiti'
    if low.startswith('stkaitibook'):
        return 'STKaiti'
    if low.startswith('texgyretermes'):
        # TeXGyreTermes-Regular / texgyretermes-regular
        part = b.split('-', 1)[1] if '-' in b else 'Regular'
        return 'TeXGyreTermes-' + part.capitalize()
    return b


def gy(g):
    """vertical reference of a glyph for line assignment: the baseline,
    except for CMEX (big delimiters/radicals hang from their origin), where
    the visual centre is used."""
    if isinstance(g, dict):
        return g.get('vy', g['y'])
    if g.font.name.startswith('CMEX') or (g.font.name.startswith('CMSY') and g.code == 112):   # radical signs hang from the origin
        b = g.font.bounds.get(g.code)
        if b:
            return g.y + (b[1] + b[3]) / 2 * g.size
    return g.y


class PageEdit:
    def __init__(self, pdf, pn, bookfonts):
        self.pdf = pdf; self.pn = pn; self.page = pdf.pages[pn - 1]
        self.bf = bookfonts
        self.ops = list(pikepdf.parse_content_stream(self.page))
        self.ops_i, self.glyphs, self.items = interpret(pdf, self.page, self.ops)
        self.rm_glyphs = []
        self.rm_ops = set()
        self.new_ops = []
        self.log = []

    # ---------------- selection
    def glyphs_in(self, x0, y0, x1, y1, pred=None):
        return [g for g in self.glyphs if x0 <= g.x <= x1 and y0 <= gy(g) <= y1 and (pred is None or pred(g))]

    def items_in(self, x0, y0, x1, y1, kinds=('path', 'do'), full=True, pred=None):
        out = []
        for it in self.items:
            if it.kind not in kinds:
                continue
            b = it.bbox
            if full:
                ok = b[0] >= x0 - 0.01 and b[2] <= x1 + 0.01 and b[1] >= y0 - 0.01 and b[3] <= y1 + 0.01
            else:
                ok = b[0] <= x1 and b[2] >= x0 and b[1] <= y1 and b[3] >= y0
            if ok and (pred is None or pred(it)):
                out.append(it)
        return out

    def white_boxes(self):
        return [it for it in self.items if it.kind == 'path' and it.paint in ('f', 'F', 'f*', 'B', 'B*', 'b', 'b*') and all(abs(c - 1) < 1e-3 for c in it.color[:3])]

    # ---------------- removal
    def remove_glyphs(self, gl):
        ids = {id(g) for g in self.rm_glyphs}
        for g in gl:
            if id(g) not in ids:
                self.rm_glyphs.append(g); ids.add(id(g))

    def remove_items(self, its):
        for it in its:
            for j in range(it.op0, it.op1 + 1):
                o = str(self.ops[j][1])
                # keep pure state operators inside a path range (none expected)
                self.rm_ops.add(j)

    # ---------------- font resources
    def font_res(self, fobj):
        fr = self.page.Resources.get('/Font')
        if fr is None:
            self.page.Resources.Font = pikepdf.Dictionary(); fr = self.page.Resources.Font
        for k, v in fr.items():
            if v.objgen == fobj.objgen:
                return k
        n = 1
        while Name('/FE%d' % n) in fr:
            n += 1
        nm = Name('/FE%d' % n)
        fr[nm] = fobj
        return str(nm)

    # ---------------- emission
    def emit_glyphs(self, glyphs, color=(0, 0, 0), keep_order=False):
        """glyphs: list of dicts with keys bookfont(pikepdf obj), code, x, y, size, color(optional)"""
        if not glyphs:
            return
        ops = []
        ops.append(([], Operator('q')))
        ops.append(([0], Operator('Tc'))); ops.append(([0], Operator('Tw')))
        ops.append(([100], Operator('Tz'))); ops.append(([0], Operator('Ts'))); ops.append(([0], Operator('Tr')))
        ops.append(([], Operator('BT')))
        cur_font = None; cur_col = None; cur_tr = 0
        # group into runs: same font, size, baseline, color; consecutive in x order per line
        gl = list(glyphs) if keep_order else sorted(glyphs, key=lambda g: (-round(g['y'], 2), g['x']))
        i = 0
        while i < len(gl):
            g = gl[i]
            col = g.get('color', color)
            if g.get('tr', 0) != cur_tr:
                cur_tr = g.get('tr', 0); ops.append(([cur_tr], Operator('Tr')))
            if col != cur_col:
                ops.append(([fmt(c) for c in col], Operator('rg'))); cur_col = col
            fi = FONTS.get(g['bookfont'], self.pdf)
            res = self.font_res(g['bookfont'])
            if (res, g['size']) != cur_font:
                ops.append(([Name(res), fmt(g['size'])], Operator('Tf'))); cur_font = (res, g['size'])
            run = [g]; j = i + 1
            while j < len(gl):
                h = gl[j]
                if h['bookfont'].objgen == g['bookfont'].objgen and abs(h['size'] - g['size']) < 1e-6 and abs(h['y'] - g['y']) < 1e-4 and h.get('color', color) == col and h.get('tr', 0) == cur_tr and h['x'] >= run[-1]['x']:
                    run.append(h); j += 1
                else:
                    break
            ops.append(([1, 0, 0, 1, fmt(g['x']), fmt(g['y'])], Operator('Tm')))
            arr = []
            cur = []
            pen = g['x']
            for k, h in enumerate(run):
                if k > 0:
                    gap = h['x'] - pen
                    if abs(gap) > 0.0005:
                        if cur:
                            arr.append(String(fi.encode(cur))); cur = []
                        arr.append(fmt(-gap * 1000.0 / g['size']))
                        pen = h['x']
                cur.append(h['code'])
                pen += fi.width(h['code']) * g['size']
            if cur:
                arr.append(String(fi.encode(cur)))
            ops.append(([Array(arr)], Operator('TJ')))
            i = j
        ops.append(([], Operator('ET')))
        ops.append(([], Operator('Q')))
        self.new_ops += ops

    def emit_rule_stroke(self, x0, y, x1, lw, color=(0, 0, 0)):
        self.new_ops += [([], Operator('q')), ([fmt(c) for c in color], Operator('RG')), ([fmt(lw)], Operator('w')), ([0], Operator('J')),
                         ([fmt(x0), fmt(y)], Operator('m')), ([fmt(x1), fmt(y)], Operator('l')), ([], Operator('S')), ([], Operator('Q'))]

    def emit_rect_fill(self, x, y, w, h, color=(0, 0, 0)):
        self.new_ops += [([], Operator('q')), ([fmt(c) for c in color], Operator('rg')), ([fmt(x), fmt(y), fmt(w), fmt(h)], Operator('re')), ([], Operator('f')), ([], Operator('Q'))]

    def emit_pgram(self, x, y, lw=0.48):
        """the book's parallelogram sign (as drawn elsewhere in the book): 7 x 4.5 bp"""
        self.new_ops += [([], Operator('q')), ([0, 0, 0], Operator('RG')), ([lw], Operator('w')),
                         ([fmt(x + 1.7), fmt(y + 4.5)], Operator('m')), ([fmt(x + 7.0), fmt(y + 4.5)], Operator('l')),
                         ([fmt(x + 5.3), fmt(y)], Operator('l')), ([fmt(x), fmt(y)], Operator('l')),
                         ([], Operator('h')), ([], Operator('S')), ([], Operator('Q'))]

    def emit_path_item(self, it, dx=0.0, dy=0.0):
        """re-emit a recorded path item translated by (dx, dy) in device space"""
        ctm = mat_mul(it.ctm, [1, 0, 0, 1, dx, dy])
        ops = [([], Operator('q')), ([fmt(v) for v in ctm], Operator('cm'))]
        ops.append(([fmt(c) for c in it.color], Operator('rg')))
        ops.append(([fmt(c) for c in it.scolor], Operator('RG')))
        ops.append(([fmt(it.lw)], Operator('w'))); ops.append(([it.cap], Operator('J'))); ops.append(([it.join], Operator('j')))
        if it.dash:
            ops.append(([Array([fmt(v) for v in it.dash[0]]), fmt(it.dash[1])], Operator('d')))
        for operands, o in it.pops:
            ops.append((operands, Operator(o)))
        ops.append(([], Operator('Q')))
        self.new_ops += ops

    def emit_do_item(self, it, dx=0.0, dy=0.0):
        ctm = mat_mul(it.ctm, [1, 0, 0, 1, dx, dy])
        self.new_ops += [([], Operator('q')), ([fmt(v) for v in ctm], Operator('cm')), ([Name(it.name)], Operator('Do')), ([], Operator('Q'))]

    def move(self, glyphs=(), items=(), dx=0.0, dy=0.0):
        """remove the given content and re-emit it translated, preserving the
        original painting order."""
        glyphs = list(glyphs); items = list(items)
        self.remove_glyphs(glyphs)
        self.remove_items(items)
        seq = [(g.op, 0, g.el, g.k, 'g', g) for g in glyphs] + [(it.op0, 1, 0, 0, 'i', it) for it in items]
        seq.sort(key=lambda t: t[:4])
        batch = []
        for t in seq:
            if t[4] == 'g':
                g = t[5]
                batch.append(dict(bookfont=g.fobj, code=g.code, x=g.x + dx, y=g.y + dy, size=g.size, color=g.color, tr=g.tr))
                continue
            if batch:
                self.emit_glyphs(batch, keep_order=True); batch = []
            it = t[5]
            if it.kind == 'path':
                self.emit_path_item(it, dx, dy)
            elif it.kind == 'do':
                self.emit_do_item(it, dx, dy)
        if batch:
            self.emit_glyphs(batch, keep_order=True)

    # ---------------- commit
    def commit(self):
        new = pdfedit.rewrite(self.ops, self.rm_glyphs, self.rm_ops)
        # wrap old content so that our additions start from a clean state
        out = [([], Operator('q'))] + new + [([], Operator('Q'))] + self.new_ops
        data = pikepdf.unparse_content_stream(out)
        self.page.Contents = self.pdf.make_stream(data)
        # refresh
        self.ops = list(pikepdf.parse_content_stream(self.page))
        self.ops_i, self.glyphs, self.items = interpret(self.pdf, self.page, self.ops)
        self.rm_glyphs = []; self.rm_ops = set(); self.new_ops = []


# ---------------------------------------------------------------- layout mapping
LOG_EXT = []


def map_layout_glyph(bf, g):
    pdf = bf.pdf
    """map a glyph from the XeTeX output to (book font obj, code)."""
    nm = norm_font_name(g['font'])
    fobj = bf.get(nm)
    if fobj is None and nm.startswith(('ARPL', 'Bousung')) and g.get('fobj') is not None:
        # external fallback font (AR PL SungtiL GB): copy the subset embedded by the
        # layout run into the book, once per layout document
        key = ('ext', nm, g['src'])
        fobj = bf.by_name.get(key)
        if fobj is None:
            fobj = pdf.copy_foreign(g['fobj'])
            bf.by_name[key] = fobj
        return fobj, g['code']
    if fobj is None:
        raise KeyError('no book font for %s (%s)' % (g['font'], nm))
    fi = FONTS.get(fobj, pdf)
    if nm.startswith('TeXGyreTermes'):
        code = fi.fromunicode.get(g['uni'])
        if code is None:
            raise KeyError('glyph %r not in book %s' % (g['uni'], nm))
        return fobj, code
    code = g['code']
    if not fi.has(code):
        if g.get('fobj') is not None:
            # glyph missing from the book's subset of this font (e.g. CMMI8 'L'):
            # copy the subset embedded by the layout run (same font program)
            key = ('ext', nm, g['src'])
            f2 = bf.by_name.get(key)
            if f2 is None:
                f2 = pdf.copy_foreign(g['fobj'])
                bf.by_name[key] = f2
            if bf.pdf is pdf:
                LOG_EXT.append((nm, code, g['uni']))
            return f2, code
        raise KeyError('code %d (%r) not in book subset %s' % (code, g['uni'], nm))
    bu = fi.tounicode.get(code) if hasattr(fi, 'tounicode') and fi.tounicode else None
    if bu and g['uni'] and bu != g['uni']:
        raise KeyError('unicode mismatch for %s code %d: book %r, layout %r' % (nm, code, bu, g['uni']))
    return fobj, code
