"""Visible-text extraction with math structure for the 题典 PDF.

visible_glyphs(page)  -> list of glyph dicts that are actually visible
                         (clip-filtered, not hidden under later white fills)
rules(page)           -> visible horizontal rules (fraction bars, vincula, overlines)
linearize(page)       -> list of (y, text) lines with ^{} _{} \\frac{}{} \\sqrt{} markup
"""
import pymupdf, re, math
from collections import defaultdict

FL_CLIP = (pymupdf.TEXT_PRESERVE_WHITESPACE | pymupdf.TEXT_PRESERVE_LIGATURES |
           pymupdf.TEXT_CLIP)
FL_ALL = pymupdf.TEXT_PRESERVE_WHITESPACE | pymupdf.TEXT_PRESERVE_LIGATURES

CMEX = {  # glyph names -> linear symbol
    'parenleftbig': '(', 'parenrightbig': ')', 'parenleftBig': '(', 'parenrightBig': ')',
    'parenleftbigg': '(', 'parenrightbigg': ')', 'parenleftBigg': '(', 'parenrightBigg': ')',
    'braceleftbig': '{', 'bracerightbig': '}', 'braceleftbigg': '{', 'bracerightbigg': '}',
    'bracketleftbigg': '[', 'bracketrightbigg': ']', 'bracketleftBig': '[', 'bracketrightBig': ']',
    'vextendsingle': '|', 'bracelefttp': '{', 'braceleftbt': '', 'braceleftmid': '', 'braceex': '',
    'radicalbig': '√', 'radicalBig': '√', 'radicalbigg': '√', 'radicalBigg': '√',
    'radicalbt': '√', 'radicalvertex': '', 'radicaltp': '',
    'bracehtipdownleft': '⏟', 'bracehtipdownright': '', 'bracehtipupleft': '⏞', 'bracehtipupright': '',
}

_glyphnames = {}


def glyph_names(doc, fontname):
    """CFF charset (gid -> name) for an embedded Type1C font, by base name."""
    if fontname in _glyphnames:
        return _glyphnames[fontname]
    from fontTools.cffLib import CFFFontSet
    import io
    names = None
    for xref in range(1, doc.xref_length()):
        try:
            if doc.xref_get_key(xref, 'Type')[1] != '/FontDescriptor':
                continue
        except Exception:
            continue
        fn = doc.xref_get_key(xref, 'FontName')[1]
        if not fn.endswith(fontname):
            continue
        v = doc.xref_get_key(xref, 'FontFile3')
        if v[0] != 'xref':
            continue
        data = doc.xref_stream(int(v[1].split()[0]))
        cs = CFFFontSet()
        cs.decompile(io.BytesIO(data), None)
        names = cs[cs.fontNames[0]].charset
        break
    _glyphnames[fontname] = names
    return names


def _drawings(page):
    """visible drawings: (seqno, kind, rect, fillcolor, strokecolor, width, items)"""
    out = []
    stack = []  # (level, scissor rect)
    for x in page.get_drawings(extended=True):
        lvl = x.get('level', 0)
        while stack and stack[-1][0] >= lvl:
            stack.pop()
        if x['type'] == 'clip':
            sc = pymupdf.Rect(x['scissor'])
            if stack:
                sc = sc & stack[-1][1]
            stack.append((lvl, sc))
            continue
        if x['type'] == 'group':
            continue
        r = pymupdf.Rect(x['rect'])
        if stack:
            sc = stack[-1][1]
            rr = pymupdf.Rect(r)
            # zero-height rects: grow a little for the test
            rr.y0 -= 0.3; rr.y1 += 0.3; rr.x0 -= 0.3; rr.x1 += 0.3
            if (rr & sc).is_empty:
                continue
            r = r & sc if not (r & sc).is_empty else r
        out.append(dict(seq=x.get('seqno', 0), type=x['type'], rect=r,
                        fill=x.get('fill'), color=x.get('color'),
                        width=x.get('width'), items=x.get('items', [])))
    return out


def visible_glyphs(page):
    doc = page.parent
    # seqno per char from texttrace
    seqmap = defaultdict(list)
    gidmap = {}
    for sp in page.get_texttrace():
        for ch in sp['chars']:
            u, gid, org, bb = ch[0], ch[1], ch[2], ch[3]
            k = (u, round(org[0], 1), round(org[1], 1))
            seqmap[k].append(sp['seqno'])
            gidmap[(k, sp['font'])] = gid
    draws = _drawings(page)
    whites = [dr for dr in draws if dr['fill'] is not None and
              all(abs(c - 1) < 1e-3 for c in dr['fill'][:3])]
    out = []
    rd = page.get_text('rawdict', flags=FL_CLIP)
    acc = {}
    rda = page.get_text('rawdict', flags=FL_CLIP | pymupdf.TEXT_ACCURATE_BBOXES)
    for b in rda['blocks']:
        for l in b.get('lines', []):
            for sp in l['spans']:
                for ch in sp['chars']:
                    acc.setdefault((ch['c'], round(ch['origin'][0], 1), round(ch['origin'][1], 1)), []).append(ch['bbox'])
    used = defaultdict(int)
    for b in rd['blocks']:
        for l in b.get('lines', []):
            for sp in l['spans']:
                font = sp['font']
                size = sp['size']
                for ch in sp['chars']:
                    c = ch['c']
                    ox, oy = ch['origin']
                    k = (ord(c) if c else 0, round(ox, 1), round(oy, 1))
                    lst = seqmap.get(k, [0])
                    i = used[k]
                    seq = lst[min(i, len(lst) - 1)]
                    used[k] += 1
                    bb = pymupdf.Rect(ch['bbox'])
                    ak = (c, round(ox, 1), round(oy, 1))
                    al = acc.get(ak)
                    ib = pymupdf.Rect(al[min(used[k] - 0, len(al) - 1)]) if al else bb
                    cx, cy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
                    hidden = False
                    for w in whites:
                        if w['seq'] > seq and w['rect'].x0 - 0.2 <= cx <= w['rect'].x1 + 0.2 \
                                and w['rect'].y0 - 0.2 <= cy <= w['rect'].y1 + 0.2:
                            hidden = True
                            break
                    if hidden:
                        continue
                    name = None
                    if c in ('�',) or font in ('CMEX10', 'bbding', 'manfnt'):
                        gid = gidmap.get((k, font))
                        gn = glyph_names(doc, font) if font in ('CMEX10', 'bbding', 'manfnt') else None
                        if gn and gid is not None and gid < len(gn):
                            name = gn[gid]
                    out.append(dict(c=c, x0=bb.x0, x1=bb.x1, y0=ib.y0, y1=ib.y1, ox=ox, oy=oy,
                                    ix0=ib.x0, ix1=ib.x1,
                                    font=font, size=size, color=sp['color'], seq=seq, name=name))
    # rules
    rules = []
    for dr in draws:
        if dr in whites:
            continue
        r = dr['rect']
        col = dr['color'] if dr['type'] == 's' else dr['fill']
        # hidden under later white box?
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        if any(w['seq'] > dr['seq'] and w['rect'].contains(pymupdf.Point(cx, cy)) for w in whites):
            continue
        if dr['type'] == 's':
            # each line item
            for it in dr['items']:
                if it[0] == 'l':
                    p1, p2 = it[1], it[2]
                    if abs(p1.y - p2.y) < 0.05 and abs(p1.x - p2.x) > 1:
                        rules.append(dict(x0=min(p1.x, p2.x), x1=max(p1.x, p2.x), y=p1.y,
                                          w=dr['width'] or 0.4, color=col, seq=dr['seq']))
        elif r.height < 1.5 and r.width > 1:
            rules.append(dict(x0=r.x0, x1=r.x1, y=(r.y0 + r.y1) / 2, w=r.height,
                              color=col, seq=dr['seq']))
    return out, rules, draws


CJK_RE = re.compile(r'[　-〿一-鿿＀-￯]')


def is_cjk(c):
    return bool(CJK_RE.match(c))


def sym(g):
    c = g['c']
    f = g['font']
    if f == 'CMEX10' and g.get('name'):
        return CMEX.get(g['name'], '?' + g['name'])
    if f == 'bbding':
        return '✍'
    if f == 'manfnt':
        return '☡'
    if f.startswith('CMSY') and c == '̸':
        return '̸'   # negation slash; resolved later (≠ or ∠)
    return c


class Item:
    __slots__ = ('x0', 'x1', 'y0', 'y1', 'base', 'size', 'text', 'kind', 'font', 'g')

    def __init__(self, x0, x1, y0, y1, base, size, text, kind='g', font='', g=None):
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1
        self.base, self.size, self.text, self.kind, self.font, self.g = base, size, text, kind, font, g

    @property
    def cx(self):
        return (self.x0 + self.x1) / 2

    def __repr__(self):
        return f'<{self.kind} {self.text!r} x={self.x0:.1f}-{self.x1:.1f} b={self.base:.1f} s={self.size:.1f}>'


def tight_box(g):
    """approximate ink box from font metrics: rawdict box is ascender..descender"""
    return g['x0'], g['x1'], g['y0'], g['y1']


def linear(items, ctx_size=10.9):
    """linearize a list of Items forming one horizontal run (same main baseline)."""
    if not items:
        return ''
    items = sorted(items, key=lambda it: (it.x0, it.base))
    # main baseline: most common baseline among items of the largest size class
    big = [it for it in items if it.size >= max(i.size for i in items) - 0.6]
    from collections import Counter
    cnt = Counter(round(it.base * 2) / 2 for it in big)
    mb = cnt.most_common(1)[0][0]
    msize = max(i.size for i in items)
    out = []
    prev = None
    mode = None  # None, '^', '_'
    buf = []

    def flush():
        nonlocal buf, mode
        if buf:
            s = ''.join(buf)
            if mode == '^':
                out.append('^{' + s + '}' if len(s) > 1 else '^' + s)
            elif mode == '_':
                out.append('_{' + s + '}' if len(s) > 1 else '_' + s)
            else:
                out.append(s)
        buf = []

    for it in items:
        d = mb - it.base   # positive: raised
        small = it.size < msize - 1.5
        if small and d > 1.2:
            m = '^'
        elif small and d < -0.8:
            m = '_'
        else:
            m = None
        if m != mode:
            flush()
            mode = m
        # spacing
        if prev is not None and it.x0 - prev.x1 > 2.2 and not (is_cjk(it.text[:1]) and is_cjk(prev.text[-1:])):
            if not (buf and buf[-1].endswith(' ')):
                buf.append(' ')
        buf.append(it.text)
        prev = it
    flush()
    s = ''.join(out)
    return s


def build_items(glyphs, rules):
    items = []
    for g in glyphs:
        t = sym(g)
        if t == '' or t == ' ':
            continue
        base = g['oy']
        if g['font'] == 'CMEX10':
            base = (g['y0'] + g['y1']) / 2 + 0.25 * g['size']
        items.append(Item(g['x0'], g['x1'], g['y0'], g['y1'], base, g['size'], t,
                          'g', g['font'], g))
    return items


def collapse(items, rules):
    """Fold fractions / radicals / overlines into composite items."""
    rs = [r for r in rules if r['x1'] - r['x0'] < 470 and r['w'] < 1.5 and
          (r['color'] is None or sum(r['color'][:3]) < 0.3)]
    rs.sort(key=lambda r: r['x1'] - r['x0'])
    used_rule = set()
    # angle: script negation slash with a short rule under it
    for ri, r in enumerate(rs):
        for it in items:
            if it.kind == 'g' and it.text == '̸' and it.size < 9 and \
                    it.x0 - 1.5 <= r['x0'] <= it.x1 and 0 <= r['y'] - it.base <= 2.5 and \
                    r['x1'] - r['x0'] < 9:
                it.text = '∠'
                it.kind = 'angle'
                used_rule.add(ri)
                break
    for ri, r in enumerate(rs):
        if ri in used_rule:
            continue
        x0, x1, y = r['x0'], r['x1'], r['y']
        inr = [it for it in items if x0 - 0.8 <= it.cx <= x1 + 0.8]
        # radical sign touching the left end
        rad = None
        for it in items:
            if it.text == '√' and abs(it.x1 - x0) < 1.6 and it.y0 - 2.5 <= y <= it.y0 + 6:
                rad = it
                break
        if rad is not None:
            body = [it for it in inr if it is not rad and it.y0 >= y - 3.5 and it.base <= rad.y1 + 6
                    and it.base > y]
            # index (e.g. cube root): small item left-above the radical
            rw = rad.x1 - rad.x0
            idx = [it for it in items if it.size < 9 and it.x0 >= rad.x0 - 7 and
                   it.x1 <= rad.x0 + 0.8 * rw + 1.5 and it.base < rad.y1 - 2 and
                   it.base > rad.y0 - 6 and it.y1 < rad.y1 - 1 and it is not rad]
            if not body:
                continue
            txt = linear(body)
            idxs = linear(idx) if idx else ''
            new = Item(min([rad.x0] + [i.x0 for i in idx]), max(x1, max(b.x1 for b in body)),
                       min(y, rad.y0), max(rad.y1, max(b.y1 for b in body)),
                       sorted(body, key=lambda b: -b.size)[0].base, max(b.size for b in body),
                       ('\\sqrt[' + idxs + ']{' if idxs else '\\sqrt{') + txt + '}', 'sqrt')
            rm = set(map(id, body + [rad] + idx))
            items = [it for it in items if id(it) not in rm] + [new]
            used_rule.add(ri)
            continue
        above = [it for it in inr if it.y1 <= y + 0.9 and it.base < y and y - it.base < 16]
        below = [it for it in inr if it.base > y and it.y0 >= y - 0.9 and it.base - y < 18]
        def band(group, closest_is_max):
            if not group:
                return []
            bigs = [it for it in group if it.size >= max(g.size for g in group) - 1.5] or group
            if closest_is_max:
                b0 = max(it.base for it in bigs)
            else:
                b0 = min(it.base for it in bigs)
            return [it for it in group if b0 - 5.5 <= it.base <= b0 + 3.2]
        above = band(above, True)
        below = band(below, False)
        width = x1 - x0
        if above and below:
            # fraction: numerator/denominator must roughly fill the bar
            ext_a = max(i.x1 for i in above) - min(i.x0 for i in above)
            ext_b = max(i.x1 for i in below) - min(i.x0 for i in below)
            if max(ext_a, ext_b) < 0.45 * width and width > 8:
                continue
            num = linear(above)
            den = linear(below)
            sz = max(i.size for i in above + below)
            axis = 0.25 * sz
            new = Item(x0, x1, min(i.y0 for i in above), max(i.y1 for i in below),
                       y + axis, sz, '\\frac{' + num + '}{' + den + '}', 'frac')
            rm = set(map(id, above + below))
            items = [it for it in items if id(it) not in rm] + [new]
            used_rule.add(ri)
        elif below and not above:
            # overline: glyphs just under the rule
            bl = [it for it in below if it.y0 - y < 6]
            if not bl:
                continue
            txt = linear(bl)
            new = Item(min(x0, min(i.x0 for i in bl)), max(x1, max(i.x1 for i in bl)), y,
                       max(i.y1 for i in bl), bl[0].base, max(i.size for i in bl),
                       '\\ov{' + txt + '}', 'ov')
            rm = set(map(id, bl))
            items = [it for it in items if id(it) not in rm] + [new]
            used_rule.add(ri)
        elif above and not below:
            ab = [it for it in above if y - it.base < 4.5]
            if not ab:
                continue
            txt = linear(ab)
            new = Item(min(x0, min(i.x0 for i in ab)), max(x1, max(i.x1 for i in ab)),
                       min(i.y0 for i in ab), y, ab[0].base, max(i.size for i in ab),
                       '\\un{' + txt + '}', 'un')
            rm = set(map(id, ab))
            items = [it for it in items if id(it) not in rm] + [new]
            used_rule.add(ri)
    return items


def fix_cong(items):
    """\\cong = ∼ stacked over = ; \\neq = negation slash over = """
    eqs = [it for it in items if it.text == '=' and it.kind == 'g']
    rm = set()
    for it in items:
        if it.kind != 'g':
            continue
        if it.text == '∼':
            for e in eqs:
                if abs(e.cx - it.cx) < 2 and 1.5 < e.base - it.base < 6:
                    e.text = '≅'
                    rm.add(id(it))
        if it.text == '̸':
            icx = (it.g['ix0'] + it.g['ix1']) / 2 if it.g and 'ix0' in it.g else it.cx
            for e in eqs + [x for x in items if x.text in ('∈', '≡', '∥', '<', '>', '≤', '≥', '∼', '∽', '⊥')]:
                if abs(e.cx - icx) < 3 and abs(e.base - it.base) < 1.5 and id(e) != id(it):
                    e.text = {'=': '≠', '≡': '≢', '∥': '∦', '<': '≮', '>': '≯', '≤': '≰',
                              '≥': '≱', '∼': '≁', '∽': '≁', '⊥': '⊥̸', '∈': '∉'}.get(e.text, e.text + '̸')
                    rm.add(id(it))
                    break
    return [it for it in items if id(it) not in rm]


def lines_of(items, tol=3.2):
    """cluster items into text lines by baseline (main-size items define lines)."""
    if not items:
        return []
    msz = 9.5
    mains = sorted([it for it in items if it.size >= msz], key=lambda it: it.base)
    clusters = []
    for it in mains:
        if clusters and abs(it.base - clusters[-1]['b']) <= tol:
            c = clusters[-1]
            c['its'].append(it)
            # keep baseline of plain glyphs preferentially
        else:
            clusters.append(dict(b=it.base, its=[it]))
    # recompute representative baselines: mode of plain glyph baselines
    for c in clusters:
        pl = [it.base for it in c['its'] if it.kind == 'g'] or [it.base for it in c['its']]
        from collections import Counter
        c['b'] = Counter(round(b, 1) for b in pl).most_common(1)[0][0]
    for it in items:
        if it.size >= msz:
            continue
        # attach small items to nearest line by baseline and horizontal overlap
        best = None
        for c in clusters:
            d = abs(it.base - c['b'])
            if d < 7 and (best is None or d < best[0]):
                best = (d, c)
        if best:
            best[1]['its'].append(it)
        else:
            clusters.append(dict(b=it.base, its=[it]))
    clusters.sort(key=lambda c: c['b'])
    return clusters


def page_lines(page):
    glyphs, rules, draws = visible_glyphs(page)
    items = build_items(glyphs, rules)
    items = collapse(items, rules)
    items = fix_cong(items)
    out = []
    for c in lines_of(items):
        its = sorted(c['its'], key=lambda it: it.x0)
        out.append((c['b'], its[0].x0, linear(its)))
    return out, glyphs, rules, draws


if __name__ == '__main__':
    import sys
    doc = pymupdf.open(sys.argv[1])
    for pn in map(int, sys.argv[2:]):
        lines, *_ = page_lines(doc[pn - 1])
        print(f'===== p{pn}')
        for b, x, t in lines:
            print(f'{b:6.1f} {x:5.1f} | {t}')
