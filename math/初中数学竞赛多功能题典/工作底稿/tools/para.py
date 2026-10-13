"""Re-typeset one paragraph of a page."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import engine as E
import texlayout as T

# paragraph end: the book has nothing after the last word (checked against
# a last line that is 0.3pt short of full on p290)
TAIL = os.environ.get('PARA_TAIL', '')
FOOT_Y = 60.0       # nothing above the page-number band may move below this
HEAD_Y = 781.0


def cluster_baselines(glyphs, getf, gety, levels=True):
    """baselines from CJK glyphs; fall back to dense levels of full-size glyphs"""
    cjk = sorted({round(gety(g), 2) for g in glyphs if getf(g).startswith(('STSong', 'STHeiti', 'STKaiti')) and g_size(g) > 10}, reverse=True)
    base = []
    for y in cjk:
        if not base or base[-1] - y > 6:
            base.append(y)
    # other full size levels far from CJK baselines
    if levels or not base:
        from collections import Counter
        full = [g for g in glyphs if g_size(g) > 10]
        cnt = Counter(round(gety(g), 1) for g in full)
        # a formula-only line: prefer the level of its relation/punctuation signs
        # (fraction numerators and denominators are levels too)
        rel = Counter(round(gety(g), 1) for g in full if (g['uni'] if isinstance(g, dict) else g.uni) in '+−=≥≤<>,.;≠∼')
        for y, n in sorted(cnt.items(), key=lambda t: (-(rel[t[0]] * 10 + t[1]), -t[0])):
            if n >= 2 and all(abs(y - b) > 12 for b in base):
                base.append(y)
    return sorted(base, reverse=True)


def same_char(a, c):
    """book Glyph a and layout glyph dict c show the same character (fonts
    without a ToUnicode entry, e.g. CMEX pieces, compare by font and code)"""
    if a.uni and c['uni']:
        return a.uni == c['uni']
    return E.norm_font_name(a.font.name) == E.norm_font_name(c['font']) and a.code == c['code']


def g_size(g):
    return g['size'] if isinstance(g, dict) else g.size


def assign(glyphs, base, gety):
    rows = {b: [] for b in base}
    for g in glyphs:
        b = min(base, key=lambda b: abs(b - gety(g)))
        rows[b].append(g)
    return rows


def typeset(first_x, tex, name, extra=''):
    ind = first_x - E.LM
    body = '\\parshape 2 %.4fbp %.4fbp 0bp 481.89bp\n%s%s\\par\n' % (ind, 481.89 - ind, tex, TAIL)
    pdff = T.run(body, extra=extra, name=name)
    gl, rules = T.read_layout(pdff)
    return gl, rules


def main_baseline(gl):
    """baseline of a formula-only line: the level of binary/relation signs"""
    from collections import Counter
    c = Counter(round(g['y'], 2) for g in gl if g['size'] > 10 and g['uni'] in '+−=≥≤<>,.;≠')
    return c.most_common(1)[0][0]


def retypeset(pe, first_x, y_top, y_bot, tex, name, extra='', xmin_other=None, dry=False, force_lines=None,
              shift_below=True, keep_unchanged=True, verbose=True, top_band=None, levels=True, single_y=None,
              keep_same_text=True, orig_base=None, max_lines=None, xtol=1.2, para_x=None, skip_lines=0):
    """Replace the paragraph whose glyphs lie between y_top and y_bot (PDF y-up),
    first line starting at first_x, by the typeset `tex`."""
    bf = pe.bf
    if xmin_other is None:
        xmin_other = E.LM - 3
    # original glyphs of the paragraph (exclude the label on the first line)
    og = [g for g in pe.glyphs if y_bot <= E.gy(g) <= y_top]
    obase = [single_y] if single_y is not None else (list(orig_base) if orig_base else cluster_baselines(og, lambda g: g.font.name, E.gy, levels))
    first_b = obase[0]
    def in_para(g):
        b = min(obase, key=lambda b: abs(b - E.gy(g)))
        if b == first_b:
            return g.x >= first_x - 0.3
        return g.x >= xmin_other
    og = [g for g in og if in_para(g)]
    # what the reader sees: glyphs and rules painted over by a later white box
    # (old patches) do not count when comparing a line with its re-typeset version
    whites = [it for it in pe.items if it.kind == 'path' and it.op0 not in pe.rm_ops and it.paint in ('f', 'F', 'f*', 'B', 'B*', 'b', 'b*')
              and all(abs(c - 1) < 1e-3 for c in it.color[:3])]
    def hidden(op, x, y):
        return any(w.op0 > op and w.bbox[0] - 0.2 <= x <= w.bbox[2] + 0.2 and w.bbox[1] - 0.2 <= y <= w.bbox[3] + 0.2 for w in whites)
    og_vis = [g for g in og if not hidden(g.op, g.x + g.adv / 2, E.gy(g) + 0.3 * g.size)]
    orows = assign(og_vis, obase, E.gy)
    # new layout
    gl, rules = typeset(para_x or first_x, tex, name, extra)
    nbase = [main_baseline(gl)] if single_y is not None else cluster_baselines(gl, lambda g: g["font"], E.gy, levels)
    nrows = assign(gl, nbase, E.gy)
    if skip_lines:
        # the continuation (on this page) of a paragraph begun on the previous page
        hi_keep = (nbase[skip_lines - 1] + nbase[skip_lines]) / 2
        rules = [r for r in rules if (r['bbox'][1] + r['bbox'][3]) / 2 < hi_keep]
        nbase = nbase[skip_lines:]
        gl = [g for b in nbase for g in nrows[b]]
    if max_lines:
        # a paragraph continued on the next page: typeset with its continuation,
        # keep only the lines on this page
        keep = nbase[:max_lines]
        lo_keep = (keep[-1] + nbase[max_lines]) / 2 if len(nbase) > max_lines else -1e9
        rules = [r for r in rules if (r['bbox'][1] + r['bbox'][3]) / 2 > lo_keep]
        gl = [g for b in keep for g in nrows[b]]
        nbase = keep
    # vertical placement: snap line i to original baseline i, extra lines follow TeX spacing
    place = {}
    for i, b in enumerate(nbase):
        if i < len(obase):
            place[b] = obase[i] - b
        else:
            place[b] = place[nbase[i - 1]]
    # compare lines
    changed = []
    for i, b in enumerate(nbase):
        if i >= len(obase) or not keep_unchanged:
            changed.append(i); continue
        o = sorted(orows[obase[i]], key=lambda g: (g.x, g.y))
        n = sorted(nrows[b], key=lambda g: (g['x'], g['y']))
        same = len(o) == len(n)
        if same:
            for a, c in zip(o, n):
                # a line with the same characters (same sizes and vertical offsets) is
                # kept as it is, even if the emulated justification differs slightly
                if not same_char(a, c) or abs(a.size - c['size']) > 0.1 or \
                        abs((a.y - obase[i]) - (c['y'] - b)) > (0.08 if keep_same_text else 0.08) or \
                        (not keep_same_text and abs(a.x - c['x']) > 0.08) or abs(a.x - c['x']) > xtol:
                    same = False; break
        if not same:
            changed.append(i)
    # lines whose glyphs match must also have the same rules (fraction bars, vincula)
    def band(i, base):
        hi = (base[i - 1] + base[i]) / 2 if i > 0 else base[i] + 15
        lo = (base[i] + base[i + 1]) / 2 if i + 1 < len(base) else base[i] - 12
        return lo, hi
    orules = [it for it in pe.items if it.kind == 'path' and it.op0 not in pe.rm_ops and it.bbox[3] - it.bbox[1] < 1.0
              and not (it.paint in ('f', 'F', 'B', 'b') and all(abs(c - 1) < 1e-3 for c in it.color[:3]))
              and it.bbox[2] >= xmin_other - 1 and not hidden(it.op0, (it.bbox[0] + it.bbox[2]) / 2, (it.bbox[1] + it.bbox[3]) / 2)]
    for i, b in enumerate(nbase):
        if i in changed or i >= len(obase):
            continue
        lo, hi = band(i, nbase)
        nr = sorted((r['bbox'][0], r['bbox'][2], (r['bbox'][1] + r['bbox'][3]) / 2 - b) for r in rules if lo <= (r['bbox'][1] + r['bbox'][3]) / 2 <= hi)
        olo, ohi = band(i, obase)
        orr = sorted((it.bbox[0], it.bbox[2], (it.bbox[1] + it.bbox[3]) / 2 - obase[i]) for it in orules if olo <= (it.bbox[1] + it.bbox[3]) / 2 <= ohi
                     and (i > 0 or it.bbox[2] >= first_x - 1))
        if len(nr) != len(orr) or any(abs(a[1] - a[0] - (c[1] - c[0])) > 0.3 or abs(a[0] - c[0]) > 1.2 or abs(a[2] - c[2]) > 0.3 for a, c in zip(nr, orr)):
            changed.append(i)
    changed.sort()
    removed_lines = list(range(len(nbase), len(obase)))
    if verbose:
        print('p%d %s: orig lines %d new lines %d changed %s removed %s' % (pe.pn, name, len(obase), len(nbase), changed, removed_lines))
        for i, b in enumerate(nbase):
            if i in changed:
                print('   new %d: %s' % (i, ''.join(g['uni'] for g in sorted(nrows[b], key=lambda g: g['x']))))
    if dry:
        return dict(obase=obase, nbase=nbase, changed=changed, nrows=nrows, orows=orows)
    # bands of original lines to clear
    clear = sorted(set(changed + removed_lines) & set(range(len(obase))))
    bands = []
    for i in clear:
        b = obase[i]
        hi = y_top if i == 0 else (obase[i - 1] + b) / 2
        lo = y_bot if i == len(obase) - 1 else (b + obase[i + 1]) / 2
        bands.append((i, lo, hi))
    for i, lo, hi in bands:
        # a radical's vinculum belongs to the line of its radical sign even when
        # it lies above the band boundary
        for g in og:
            if lo <= E.gy(g) <= hi and ((g.font.name.startswith('CMSY') and g.code == 112) or (g.font.name.startswith('CMEX') and g.uni == '√')):
                for it in pe.items:
                    if it.kind == 'path' and it.op0 not in pe.rm_ops and it.bbox[3] - it.bbox[1] < 1.0 and abs(it.bbox[0] - (g.x + g.adv)) < 0.6:
                        pe.remove_items([it])
    # warn about rules/glyphs of the paragraph just outside the cleared zone
    # (a vinculum or numerator above y_top would survive next to the new text)
    if bands:
        top_hi = max(h for _, _, h in bands); bot_lo = min(l for _, l, _ in bands)
        for it in pe.items:
            if it.kind == 'path' and it.op0 not in pe.rm_ops and it.bbox[3] - it.bbox[1] < 1.0 and it.bbox[2] > first_x:
                yc = (it.bbox[1] + it.bbox[3]) / 2
                if top_hi < yc <= top_hi + 6 or bot_lo - 4 <= yc < bot_lo:
                    if not (it.paint in ('f', 'F', 'B', 'b') and all(abs(c - 1) < 1e-3 for c in it.color[:3])):
                        pe.log.append('WARN rule %s just outside the zone (%.1f-%.1f)' % (tuple(round(v, 1) for v in it.bbox), bot_lo, top_hi))
    for i, lo, hi in bands:
        xmin = first_x - 0.3 if i == 0 else xmin_other
        pe.remove_glyphs([g for g in og if lo <= E.gy(g) <= hi])
        # also any other glyph (patch text etc.) in the band, right of xmin
        pe.remove_glyphs(pe.glyphs_in(xmin, lo, 600, hi))
        pe.remove_items(pe.items_in(xmin - 0.5, lo, 600, hi, kinds=('path', 'do')))
    # white boxes / patch overlays overlapping cleared bands
    for it in pe.items:
        if it.op0 in pe.rm_ops:
            continue
        b = it.bbox
        is_white = it.kind == 'path' and it.paint in ('f', 'F', 'f*', 'B', 'B*', 'b', 'b*') and all(abs(c - 1) < 1e-3 for c in it.color[:3])
        is_patch_do = it.kind == 'do' and it.name.startswith('/fzFrm')
        if not (is_white or is_patch_do):
            continue
        for i, lo, hi in bands:
            if b[1] < hi - 0.5 and b[3] > lo + 0.5:
                inside = any(b[1] >= l2 - 1.5 and b[3] <= h2 + 1.5 for _, l2, h2 in bands) or \
                    (b[1] >= min(l for _, l, _ in bands) - 1.5 and b[3] <= max(h for _, _, h in bands) + 1.5)
                if inside:
                    pe.remove_items([it])
                else:
                    pe.log.append('WARN overlay %s %s crosses band %d (%.1f-%.1f) but extends beyond' % (it.kind, tuple(round(v, 1) for v in b), i, lo, hi))
                break
    # emit new lines
    emit = []
    for i, b in enumerate(nbase):
        if i not in changed:
            continue
        dy = place[b]
        for g in nrows[b]:
            fobj, code = E.map_layout_glyph(bf, g)
            emit.append(dict(bookfont=fobj, code=code, x=g['x'], y=g['y'] + dy, size=g['size']))
    pe.emit_glyphs(emit)
    for r in rules:
        y = (r['bbox'][1] + r['bbox'][3]) / 2
        b = min(nbase, key=lambda b: abs(b - y))
        i = nbase.index(b)
        if i not in changed:
            continue
        dy = place[b]
        ops = r['ops']
        if r['paint'] == 'S' and len(ops) == 3 and ops[0][0] == 'm' and ops[1][0] == 'l':
            x0, y0 = r['bbox'][0], r['bbox'][1]
            x1 = r['bbox'][2]
            if abs(x1 - x0 - 7.0) < 0.05 and abs(r['lw'] - 4.5) < 0.05:
                # \pgram placeholder (xdvipdfmx strokes rules): the book's parallelogram sign
                pe.emit_pgram(x0, y0 - 2.25 + dy)
                continue
            pe.emit_rule_stroke(x0, y0 + dy, x1, r['lw'])
        elif r['paint'] in ('f', 'F'):
            bb = r['bbox']
            if abs(bb[2] - bb[0] - 7.0) < 0.05 and abs(bb[3] - bb[1] - 4.5) < 0.05:
                pe.emit_pgram(bb[0], bb[1] + dy)
            else:
                pe.emit_rect_fill(bb[0], bb[1] + dy, bb[2] - bb[0], bb[3] - bb[1])
        else:
            raise RuntimeError('unsupported rule %r' % r)
    # shift content below if the line count changed
    delta_lines = len(nbase) - len(obase)
    delta = 0.0
    if delta_lines:
        delta = (nbase[-1] + place[nbase[-1]]) - obase[-1]
    return dict(delta=delta, obase=obase, nbase=nbase, changed=changed, place=place)


def shift_region(pe, y_from, delta, y_to=FOOT_Y, x0=0, x1=600):
    """move everything with y in [y_to, y_from) by delta (negative = down)."""
    gl = [g for g in pe.glyphs if y_to <= g.y < y_from and x0 <= g.x <= x1 and not any(g is r for r in pe.rm_glyphs)]
    its = [it for it in pe.items if it.op0 not in pe.rm_ops and it.bbox[3] < y_from and it.bbox[1] >= y_to - 0.5]
    pe.move(gl, its, 0, delta)
    return len(gl), len(its)


def first_text_x(pe, y, tol=0.6):
    """x of the first body glyph after the exercise label on baseline y."""
    row = sorted([g for g in pe.glyphs if abs(g.y - y) < tol], key=lambda g: g.x)
    last_label = None
    for g in row:
        if g.font.name in ('MSAM10', 'STHeiti', 'TeXGyreTermes-Bold-Identity-H', 'bbding') or g.font.name.startswith('TeXGyreTermes-Bold'):
            last_label = g
    if last_label is None:
        return row[0].x
    after = [g for g in row if g.x > last_label.x + 0.1]
    return after[0].x if after else None
