"""Content-stream level editing of the book PDF.

interpret() walks a page's content stream and records every glyph, path and
XObject invocation with its operator index and device-space geometry
(PDF user space, y up).  Edits are expressed against those records:
glyphs are removed by replacing them in their TJ array with the equivalent
positioning number (so later glyphs keep their places), paths and Do
operators are dropped, and new material is appended at the end of the page.
"""
import io, re, math
import pikepdf
from pikepdf import Name, Operator
from fontTools.cffLib import CFFFontSet

PAGE_H = 841.89


def mat_mul(a, b):
    # a, b: [a b c d e f] row-vector convention (PDF): p' = p * M
    return [a[0]*b[0] + a[1]*b[2], a[0]*b[1] + a[1]*b[3],
            a[2]*b[0] + a[3]*b[2], a[2]*b[1] + a[3]*b[3],
            a[4]*b[0] + a[5]*b[2] + b[4], a[4]*b[1] + a[5]*b[3] + b[5]]


def apply(m, x, y):
    return (x*m[0] + y*m[2] + m[4], x*m[1] + y*m[3] + m[5])


IDENT = [1, 0, 0, 1, 0, 0]


def parse_cmap_tounicode(data):
    """Return dict code(int)->str and code byte length."""
    txt = data.decode('latin1')
    out = {}
    nbytes = 1
    m = re.search(r'begincodespacerange\s*<([0-9A-Fa-f]+)>', txt)
    if m:
        nbytes = len(m.group(1)) // 2

    def hexstr(h):
        b = bytes.fromhex(h)
        try:
            return b.decode('utf-16-be')
        except Exception:
            return ''
    for blk in re.findall(r'beginbfchar(.*?)endbfchar', txt, re.S):
        for a, b in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]*)>', blk):
            out[int(a, 16)] = hexstr(b)
    for blk in re.findall(r'beginbfrange(.*?)endbfrange', txt, re.S):
        for a, b, rest in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(\[[^\]]*\]|<[0-9A-Fa-f]+>)', blk):
            lo, hi = int(a, 16), int(b, 16)
            if rest.startswith('['):
                items = re.findall(r'<([0-9A-Fa-f]*)>', rest)
                for i, h in enumerate(items):
                    out[lo + i] = hexstr(h)
            else:
                base = bytes.fromhex(rest[1:-1])
                bv = int.from_bytes(base, 'big')
                for i in range(hi - lo + 1):
                    v = (bv + i).to_bytes(len(base), 'big')
                    try:
                        out[lo + i] = v.decode('utf-16-be')
                    except Exception:
                        pass
    return out, nbytes


class FontInfo:
    def __init__(self, fobj):
        self.obj = fobj
        self.subtype = str(fobj.get('/Subtype'))
        self.base = str(fobj.get('/BaseFont', ''))
        self.name = self.base.split('+', 1)[-1]
        self.cid = self.subtype == '/Type0'
        self.widths = {}
        self.default_w = 0
        self.tounicode = {}
        self.nbytes = 2 if self.cid else 1
        self.glyphnames = None   # for Type1: code -> glyph name present in subset
        self.bounds = {}
        if self.cid:
            d = fobj['/DescendantFonts'][0]
            self.default_w = float(d.get('/DW', 1000))
            W = d.get('/W')
            if W is not None:
                W = list(W)
                i = 0
                while i < len(W):
                    c = int(W[i])
                    if isinstance(W[i+1], pikepdf.Array):
                        for k, w in enumerate(W[i+1]):
                            self.widths[c + k] = float(w)
                        i += 2
                    else:
                        c2 = int(W[i+1]); w = float(W[i+2])
                        for k in range(c, c2 + 1):
                            self.widths[k] = w
                        i += 3
            fd = d.get('/FontDescriptor')
        else:
            fc = int(fobj.get('/FirstChar', 0))
            for k, w in enumerate(fobj.get('/Widths', [])):
                self.widths[fc + k] = float(w)
            fd = fobj.get('/FontDescriptor')
            try:
                ff = fd.get('/FontFile3') if fd is not None else None
                if ff is not None:
                    cff = CFFFontSet()
                    cff.decompile(io.BytesIO(ff.read_bytes()), None)
                    top = cff[cff.fontNames[0]]
                    enc = top.Encoding
                    names = set(top.CharStrings.keys())
                    if isinstance(enc, list):
                        self.glyphnames = {i: n for i, n in enumerate(enc) if n and n != '.notdef' and n in names}
                    else:
                        self.glyphnames = {}
                    self.bounds = {}
                    cs = top.CharStrings
                    fm = getattr(top, 'FontMatrix', [0.001, 0, 0, 0.001, 0, 0])
                    sc = fm[0] * 1000.0
                    for code, gname in self.glyphnames.items():
                        try:
                            c = cs[gname]
                            b = c.calcBounds(cs)
                            if b:
                                self.bounds[code] = tuple(v * sc / 1000.0 for v in b)
                        except Exception:
                            pass
            except Exception:
                self.glyphnames = None
        tu = fobj.get('/ToUnicode')
        if tu is not None:
            self.tounicode, nb = parse_cmap_tounicode(tu.read_bytes())
        self.fromunicode = {}
        for c, s in self.tounicode.items():
            if s and s not in self.fromunicode:
                self.fromunicode[s] = c

    def width(self, code):
        return self.widths.get(code, self.default_w) / 1000.0

    def has(self, code):
        if self.cid:
            return self.widths.get(code, 0) > 0 or code in self.tounicode
        if self.glyphnames is not None:
            return code in self.glyphnames
        return code in self.widths

    def codes(self, s):
        b = bytes(s)
        if self.nbytes == 2:
            return [int.from_bytes(b[i:i+2], 'big') for i in range(0, len(b) - 1, 2)]
        return list(b)

    def encode(self, codes):
        if self.nbytes == 2:
            return b''.join(c.to_bytes(2, 'big') for c in codes)
        return bytes(codes)


class FontCache:
    def __init__(self):
        self.by_objgen = {}

    def get(self, fobj, pdf=None):
        # entries hold strong references to the document (and to direct font
        # objects) so that id() values cannot be recycled while cached
        if fobj.objgen == (0, 0):
            key = ('direct', id(fobj))
        else:
            key = (id(pdf), fobj.objgen)
        ent = self.by_objgen.get(key)
        if ent is None or ent[0] is not pdf or (fobj.objgen == (0, 0) and ent[1] is not fobj):
            ent = (pdf, fobj, FontInfo(fobj))
            self.by_objgen[key] = ent
        return ent[2]


FONTS = FontCache()


class Glyph:
    __slots__ = ('op', 'el', 'k', 'code', 'font', 'fres', 'size', 'x', 'y', 'adv', 'trm', 'uni', 'seg', 'color', 'scolor', 'tr', 'fobj')

    def __repr__(self):
        return f'G({self.uni!r} {self.font.name} {self.size:.2f} @{self.x:.2f},{self.y:.2f} op{self.op})'


class Item:
    def __init__(self, kind, op0, op1, bbox, **kw):
        self.kind = kind; self.op0 = op0; self.op1 = op1; self.bbox = bbox
        self.__dict__.update(kw)

    def __repr__(self):
        return f'{self.kind}[{self.op0}-{self.op1}] bbox=({self.bbox[0]:.1f},{self.bbox[1]:.1f},{self.bbox[2]:.1f},{self.bbox[3]:.1f}) ' + str({k: v for k, v in self.__dict__.items() if k not in ('kind', 'op0', 'op1', 'bbox')})


def interpret(pdf, page, ops=None):
    """Return (ops, glyphs, items).  items: paths and XObject invocations.
    Each record has .seg: 0 for the original typeset block (first top-level
    q..Q), 1 for anything after it (later patches)."""
    if ops is None:
        ops = pikepdf.parse_content_stream(page)
    res = page.Resources
    fonts = res.get('/Font', {})
    xobjs = res.get('/XObject', {})
    glyphs = []; items = []
    ctm = IDENT[:]
    stack = []
    fill = (0, 0, 0)
    gs = dict(stroke=(0, 0, 0), lw=1.0, cap=0, join=0, miter=10.0, dash=None, tr=0)
    tf = None; tfs = 0; tc = 0; tw = 0; th = 1; tl = 0; ts = 0
    tm = IDENT[:]; tlm = IDENT[:]
    path_start = None; pts = []
    depth = 0; seg = 0; top_closed = False

    def show(opi, arr):
        nonlocal tm
        for ei, el in enumerate(arr):
            if not isinstance(el, (bytes, pikepdf.String)):
                try:
                    v = float(el)
                except Exception:
                    continue
                tx = -v / 1000.0 * tfs * th
                tm = mat_mul([1, 0, 0, 1, tx, 0], tm)
                continue
            codes = tf.codes(el)
            for k, code in enumerate(codes):
                w0 = tf.width(code)
                trm = mat_mul(mat_mul([tfs * th, 0, 0, tfs, 0, ts], tm), ctm)
                g = Glyph()
                g.op = opi; g.el = ei; g.k = k; g.code = code; g.font = tf; g.fres = tfres
                g.size = math.hypot(trm[2], trm[3])
                g.x, g.y = trm[4], trm[5]
                single = (tf.nbytes == 1 and code == 32)
                tx = (w0 * tfs + tc + (tw if single else 0)) * th
                M = mat_mul(tm, ctm)
                g.adv = tx * math.hypot(M[0], M[1])
                g.trm = trm
                g.uni = tf.tounicode.get(code, '')
                g.seg = seg
                g.color = fill
                g.scolor = gs['stroke']
                g.tr = gs['tr']
                g.fobj = fonts[tfres]
                glyphs.append(g)
                tm = mat_mul([1, 0, 0, 1, tx, 0], tm)

    tfres = None
    for i, (operands, op) in enumerate(ops):
        o = str(op)
        if o == 'q':
            stack.append((ctm[:], fill, dict(gs))); depth += 1
        elif o == 'Q':
            if stack:
                ctm, fill, gs = stack.pop()
            depth -= 1
            if depth == 0 and not top_closed:
                top_closed = True; seg = 1
        elif o == 'cm':
            m = [float(v) for v in operands]
            ctm = mat_mul(m, ctm)
        elif o in ('RG', 'G', 'K', 'SC', 'SCN'):
            try:
                vals = [float(v) for v in operands]
                if o == 'G':
                    gs['stroke'] = (vals[0],) * 3
                elif o == 'RG':
                    gs['stroke'] = tuple(vals)
                elif o == 'K':
                    c, m_, y, k_ = vals
                    gs['stroke'] = (1 - min(1, c + k_), 1 - min(1, m_ + k_), 1 - min(1, y + k_))
                else:
                    gs['stroke'] = tuple(vals)
            except Exception:
                pass
        elif o == 'w':
            gs['lw'] = float(operands[0])
        elif o == 'J':
            gs['cap'] = int(operands[0])
        elif o == 'j':
            gs['join'] = int(operands[0])
        elif o == 'M':
            gs['miter'] = float(operands[0])
        elif o == 'd':
            gs['dash'] = ([float(v) for v in operands[0]], float(operands[1]))
        elif o == 'Tr':
            gs['tr'] = int(operands[0])
        elif o in ('rg', 'g', 'k', 'sc', 'scn'):
            try:
                vals = [float(v) for v in operands]
                if o == 'g':
                    fill = (vals[0],) * 3
                elif o == 'rg':
                    fill = tuple(vals)
                elif o == 'k':
                    c, m_, y, k_ = vals
                    fill = (1 - min(1, c + k_), 1 - min(1, m_ + k_), 1 - min(1, y + k_))
                else:
                    fill = tuple(vals)
            except Exception:
                pass
        elif o == 'BT':
            tm = IDENT[:]; tlm = IDENT[:]
        elif o == 'Tf':
            tfres = str(operands[0])
            tf = FONTS.get(fonts[tfres], pdf); tfs = float(operands[1])
        elif o == 'Tc':
            tc = float(operands[0])
        elif o == 'Tw':
            tw = float(operands[0])
        elif o == 'Tz':
            th = float(operands[0]) / 100.0
        elif o == 'TL':
            tl = float(operands[0])
        elif o == 'Ts':
            ts = float(operands[0])
        elif o == 'Td':
            tlm = mat_mul([1, 0, 0, 1, float(operands[0]), float(operands[1])], tlm); tm = tlm[:]
        elif o == 'TD':
            tl = -float(operands[1])
            tlm = mat_mul([1, 0, 0, 1, float(operands[0]), float(operands[1])], tlm); tm = tlm[:]
        elif o == 'Tm':
            tlm = [float(v) for v in operands]; tm = tlm[:]
        elif o == 'T*':
            tlm = mat_mul([1, 0, 0, 1, 0, -tl], tlm); tm = tlm[:]
        elif o == 'TJ':
            show(i, list(operands[0]))
        elif o == 'Tj':
            show(i, [operands[0]])
        elif o == "'":
            tlm = mat_mul([1, 0, 0, 1, 0, -tl], tlm); tm = tlm[:]
            show(i, [operands[0]])
        elif o == '"':
            tw = float(operands[0]); tc = float(operands[1])
            tlm = mat_mul([1, 0, 0, 1, 0, -tl], tlm); tm = tlm[:]
            show(i, [operands[2]])
        elif o in ('m', 'l', 'c', 'v', 'y', 're', 'h'):
            if path_start is None:
                path_start = i; pts = []
            vals = [float(v) for v in operands]
            if o == 're':
                x, y, w, h = vals
                pts += [apply(ctm, x, y), apply(ctm, x + w, y), apply(ctm, x, y + h), apply(ctm, x + w, y + h)]
            else:
                for j in range(0, len(vals), 2):
                    pts.append(apply(ctm, vals[j], vals[j + 1]))
        elif o in ('S', 's', 'f', 'F', 'f*', 'B', 'B*', 'b', 'b*', 'n'):
            if path_start is not None:
                xs = [p[0] for p in pts] or [0]; ys = [p[1] for p in pts] or [0]
                items.append(Item('path', path_start, i, (min(xs), min(ys), max(xs), max(ys)), paint=o, seg=seg, color=fill, nops=i - path_start + 1,
                                  ctm=ctm[:], scolor=gs['stroke'], lw=gs['lw'], cap=gs['cap'], join=gs['join'], miter=gs['miter'], dash=gs['dash'],
                                  pops=[(list(ops[j][0]), str(ops[j][1])) for j in range(path_start, i + 1)]))
            path_start = None; pts = []
        elif o == 'Do':
            nm = str(operands[0])
            xo = xobjs.get(nm)
            bb = None
            if xo is not None and xo.get('/Subtype') == Name.Form:
                b = [float(v) for v in xo.BBox]
                m = [float(v) for v in xo.get('/Matrix', IDENT)]
                full = mat_mul(m, ctm)
                cs = [apply(full, b[0], b[1]), apply(full, b[2], b[1]), apply(full, b[0], b[3]), apply(full, b[2], b[3])]
                bb = (min(c[0] for c in cs), min(c[1] for c in cs), max(c[0] for c in cs), max(c[1] for c in cs))
            elif xo is not None:
                cs = [apply(ctm, 0, 0), apply(ctm, 1, 0), apply(ctm, 0, 1), apply(ctm, 1, 1)]
                bb = (min(c[0] for c in cs), min(c[1] for c in cs), max(c[0] for c in cs), max(c[1] for c in cs))
            items.append(Item('do', i, i, bb or (0, 0, 0, 0), name=nm, seg=seg, sub=str(xo.get('/Subtype')) if xo is not None else None, ctm=ctm[:], xobj=xo))
    return ops, glyphs, items


def num_for_skip(g, tc=0.0, tw=0.0):
    """TJ positioning number equivalent to the advance of glyph g."""
    return -(g.font.width(g.code) * 1000.0)


def rewrite(ops, remove_glyphs=(), remove_ops=()):
    """Return a new op list with the given glyphs replaced by spacing and the
    given operator indices dropped."""
    rg = {}
    for g in remove_glyphs:
        rg.setdefault(g.op, set()).add((g.el, g.k))
    drop = set(remove_ops)
    new = []
    for i, (operands, op) in enumerate(ops):
        if i in drop:
            continue
        o = str(op)
        if i in rg and o in ('TJ', 'Tj', "'", '"'):
            if o == 'TJ':
                arr = list(operands[0])
            else:
                arr = [operands[-1]]
            out = []
            # we need the font for this op: find by scanning glyph list given
            fobj = next(g.font for g in remove_glyphs if g.op == i)
            for ei, el in enumerate(arr):
                if isinstance(el, pikepdf.String) or isinstance(el, bytes):
                    codes = fobj.codes(el)
                    cur = []
                    for k, c in enumerate(codes):
                        if (ei, k) in rg[i]:
                            if cur:
                                out.append(pikepdf.String(fobj.encode(cur))); cur = []
                            out.append(-fobj.width(c) * 1000.0)
                        else:
                            cur.append(c)
                    if cur:
                        out.append(pikepdf.String(fobj.encode(cur)))
                else:
                    out.append(float(el))
            # merge adjacent numbers
            merged = []
            for el in out:
                if not isinstance(el, pikepdf.String) and merged and not isinstance(merged[-1], pikepdf.String):
                    merged[-1] = merged[-1] + el
                else:
                    merged.append(el)
            if o in ("'", '"'):
                # move to next line first, then show
                if o == "'":
                    new.append(([], Operator('T*')))
                else:
                    new.append(([operands[0]], Operator('Tw')))
                    new.append(([operands[1]], Operator('Tc')))
                    new.append(([], Operator('T*')))
            new.append(([pikepdf.Array([m if isinstance(m, pikepdf.String) else round(m, 4) for m in merged])], Operator('TJ')))
        else:
            new.append((operands, op))
    return new


def save_ops(pdf, page, ops):
    data = pikepdf.unparse_content_stream(ops)
    page.Contents = pdf.make_stream(data)
