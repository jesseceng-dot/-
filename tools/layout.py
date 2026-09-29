"""Block styles, measuring, and the page-fill solver.

Vertical layout is a grid of NLINES slots per page.  Every block occupies a whole number of slots,
so all pages of running text carry exactly NLINES lines and their last baselines coincide.
The solver chooses, per paragraph, one of a few imperceptible letter-spacing variants so that the
number of lines each paragraph takes lets every page fill exactly, headings never end a page, and
no page ends with a single stray line.  Only if that is impossible is one page stretched slightly.
"""
import re
from dataclasses import dataclass, field
from . import style
from .model import runs_html, runs_len, runs_text

INF = float('inf')
N = style.NLINES

# ---- grids ---------------------------------------------------------------------------------------
GRIDS = {
    # n slots per (logical) page, pitch in pt, cols per physical page, column width, gutter
    'body':   dict(n=style.NLINES, pitch=style.LINE, cols=1, W=style.TEXT_W, gutter=0.0),
    'small1': dict(n=style.SMALL_N, pitch=style.TEXT_H / style.SMALL_N, cols=1, W=style.TEXT_W, gutter=0.0),
    'small2': dict(n=style.SMALL_N, pitch=style.TEXT_H / style.SMALL_N, cols=2, W=(style.TEXT_W - 16.0) / 2, gutter=16.0),
}

# style table: em-based indents use the style's own font size (fs, pt).
#   first = first-line indent (em), left/right = block indents (em), slots = grid lines per text line
STYLES = {
    #            css class   fs    first left right align slots before after keep
    'body':     dict(cls='s-body',    fs=10.5, first=2, left=0, right=0, align='j', slots=1, before=0, after=0, keep=0),
    'noindent': dict(cls='s-body',    fs=10.5, first=0, left=0, right=0, align='j', slots=1, before=0, after=0, keep=0),
    'quote':    dict(cls='s-quote',   fs=10.0, first=2, left=2, right=2, align='j', slots=1, before=0, after=0, keep=0),
    'kaibody':  dict(cls='s-kaibody', fs=10.5, first=2, left=0, right=0, align='j', slots=1, before=0, after=0, keep=0),
    'trow':     dict(cls='s-body',    fs=10.5, first=0, left=0, right=0, align='l', slots=1, before=0, after=0, keep=0),
    'quotel':   dict(cls='s-quote',   fs=10.0, first=2, left=2, right=2, align='l', slots=1, before=0, after=0, keep=0),
    'verse':    dict(cls='s-quote',   fs=10.0, first=0, left=4, right=0, align='l', slots=1, before=0, after=0, keep=0),
    'center':   dict(cls='s-body',    fs=10.5, first=0, left=0, right=0, align='c', slots=1, before=0, after=0, keep=0),
    'orn':      dict(cls='s-body',    fs=10.5, first=0, left=0, right=0, align='c', slots=1, before=0, after=0, keep=2),   # ornament under a heading: stays with the heading and the text after it
    'right':    dict(cls='s-body',    fs=10.5, first=0, left=0, right=2, align='r', slots=1, before=0, after=0, keep=0),
    'epi':      dict(cls='s-quote',   fs=10.0, first=0, left=2, right=2, align='c', slots=1, before=1, after=1, keep=0),
    'left':     dict(cls='s-body',    fs=10.5, first=0, left=0, right=0, align='l', slots=1, before=0, after=0, keep=0),
    'sep':      dict(cls='s-body',    fs=10.5, first=0, left=0, right=0, align='c', slots=1, before=1, after=1, keep=0),
    'secn':     dict(cls='s-secnum',  fs=9.5,  first=0, left=0, right=0, align='c', slots=1, before=1, after=0, keep=2),
    'secnum':   dict(cls='s-secnum',  fs=9.5,  first=0, left=0, right=0, align='c', slots=1, before=0, after=0, keep=2),
    'h1':       dict(cls='s-h1',      fs=17.0, first=0, left=0, right=0, align='c', slots=2, before=3, after=2, keep=2, top_keep=1),
    'h2':       dict(cls='s-h2',      fs=14.0, first=0, left=0, right=0, align='c', slots=1, before=2, after=1, keep=2),
    'h3':       dict(cls='s-h3',      fs=12.0, first=0, left=0, right=0, align='c', slots=1, before=1, after=0, keep=2),
    'h4':       dict(cls='s-h4',      fs=11.0, first=0, left=0, right=0, align='c', slots=1, before=1, after=0, keep=2),
    'h5':       dict(cls='s-h5',      fs=10.5, first=0, left=2, right=0, align='l', slots=1, before=0, after=0, keep=2),
    'h6':       dict(cls='s-h6',      fs=10.5, first=0, left=2, right=0, align='l', slots=1, before=0, after=0, keep=2),
    'h7':       dict(cls='s-h7',      fs=10.0, first=0, left=4, right=0, align='l', slots=1, before=0, after=0, keep=2),
    'h8':       dict(cls='s-h8',      fs=10.0, first=0, left=4, right=0, align='l', slots=1, before=0, after=0, keep=2),
    'h9':       dict(cls='s-h9',      fs=9.5,  first=0, left=4, right=0, align='l', slots=1, before=0, after=0, keep=2),
    'refhead':  dict(cls='s-refhead', fs=10.0, first=0, left=0, right=0, align='l', slots=1, before=1, after=0, keep=2),
    'ck':       dict(cls='s-quote',   fs=10.0, first=0, left=0, right=0, align='c', slots=1, before=0, after=0, keep=0),
    'toc0':     dict(cls='s-toc0',    fs=11.0, first=0, left=0, right=3, align='l', slots=1, before=2, after=0, keep=2),
    'mtoc':     dict(cls='s-toc2',    fs=10.5, first=-1, left=2.5, right=3, align='l', slots=1, before=0, after=0, keep=0),
    'mbook':    dict(cls='s-mbook',   fs=12.0, first=0, left=0, right=6, align='l', slots=1, before=2, after=0, keep=3),
    'mvol':     dict(cls='s-mvol',    fs=11.0, first=0, left=0.8, right=3, align='l', slots=1, before=1, after=0, keep=2),
    'mtocnote': dict(cls='s-mtocnote', fs=9.0, first=0, left=0, right=0, align='c', slots=1, before=0, after=1, keep=0),
    'mnote':    dict(cls='s-mnote',   fs=9.0, first=0, left=0, right=0, align='r', slots=1, before=0, after=0, keep=0),   # right-hand label of a book line (calibration only)
    'toc1':     dict(cls='s-toc1',    fs=10.5, first=-1, left=1, right=3, align='l', slots=1, before=1, after=0, keep=0),
    'toc1i':    dict(cls='s-toc1',    fs=10.5, first=-1, left=2, right=3, align='l', slots=1, before=1, after=0, keep=0),
    'toc2i':    dict(cls='s-toc2',    fs=10.5, first=-1, left=3.5, right=3, align='l', slots=1, before=0, after=0, keep=0),
    'toc3i':    dict(cls='s-toc3',    fs=10.0, first=-1, left=5.5, right=3, align='l', slots=1, before=0, after=0, keep=0),
    'toc2':     dict(cls='s-toc2',    fs=10.5, first=-1, left=2.5, right=3, align='l', slots=1, before=0, after=0, keep=0),
    'toc3':     dict(cls='s-toc3',    fs=10.0, first=-1, left=4.5, right=3, align='l', slots=1, before=0, after=0, keep=0),
    'tochead':  dict(cls='s-h1',      fs=17.0, first=0, left=0, right=0, align='c', slots=2, before=3, after=2, keep=2, top_keep=1),
}
# small-grid (notes / indexes) style overrides
STYLES_SMALL = {
    'h1':      dict(cls='s-h1', fs=17.0, first=0, left=0, right=0, align='c', slots=3, before=4, after=3, keep=3, top_keep=1),
    'note':    dict(cls='s-note', fs=8.5, first=-3, left=3, right=0, align='j', slots=1, before=0, after=0, keep=0),
    'notec':   dict(cls='s-note', fs=8.5, first=0, left=3, right=0, align='j', slots=1, before=0, after=0, keep=0),
    'notel':   dict(cls='s-note', fs=8.5, first=-3, left=3, right=0, align='l', slots=1, before=0, after=0, keep=0),
    'notev':   dict(cls='s-note', fs=8.5, first=0, left=6, right=0, align='l', slots=1, before=0, after=0, keep=0),
    'noter':   dict(cls='s-note', fs=8.5, first=0, left=3, right=1, align='r', slots=1, before=0, after=0, keep=0),
    'index':   dict(cls='s-index', fs=8.5, first=-1, left=1, right=0, align='l', slots=1, before=0, after=0, keep=0),
    'indexc':  dict(cls='s-index', fs=8.5, first=0, left=1, right=0, align='l', slots=1, before=0, after=0, keep=0),
    'idxhead': dict(cls='s-idxhead', fs=10.0, first=0, left=0, right=0, align='l', slots=1, before=1, after=0, keep=3),
    'idxnote': dict(cls='s-index', fs=8.5, first=0, left=0, right=0, align='j', slots=1, before=0, after=1, keep=0),
    'cip':     dict(cls='s-cip', fs=9.0, first=0, left=0, right=0, align='l', slots=1, before=0, after=0, keep=0),
    'cipj':    dict(cls='s-cip', fs=9.0, first=0, left=0, right=0, align='j', slots=1, before=0, after=0, keep=0),
    'cipc':    dict(cls='s-cip', fs=9.0, first=0, left=0, right=0, align='c', slots=1, before=0, after=0, keep=0),
}


def sty(block, grid='body'):
    """Effective style dict of a block: grid style table, overridden by per-block props."""
    g = GRIDS[grid]
    base = STYLES_SMALL.get(block['style']) if grid != 'body' and block['style'] in STYLES_SMALL else STYLES.get(block['style'])
    if base is None:
        base = STYLES_SMALL[block['style']]
    s = dict(base)
    for k in ('first', 'left', 'right', 'align', 'before', 'after', 'keep', 'slots', 'fs'):
        if k in block:
            s[k] = block[k]
    s['W'] = g['W']
    s['pitch'] = g['pitch']
    return s


@dataclass
class LB:
    """Layout block handed to the solver."""
    idx: int
    block: dict
    st: dict
    nl: list = field(default_factory=list)       # number of lines per variant
    pen: list = field(default_factory=list)      # penalty per variant (INF = forbidden)
    starts: list = field(default_factory=list)   # per variant: list of line start units
    nat: list = field(default_factory=list)
    brk: bool = False                            # forced page break before
    splittable: bool = True


def line_geom(st, j):
    """(x offset, width) in pt of line j of a block."""
    em = st['fs']
    left = st['left'] * em
    right = st['right'] * em
    first = st['first'] * em if j == 0 else 0
    return left + first, st['W'] - left - right - first


def build_specs(block, variants, grid='body'):
    st = sty(block, grid)
    em = st['fs']
    w = st['W'] - (st['left'] + st['right']) * em
    specs = []
    html = runs_html(block['runs'], strip=False)
    for v in variants:
        specs.append(dict(html=html, cls=st['cls'], width=w, indent=st['first'] * em, ls=v,
                          lh=st['pitch'] * st['slots']))
    return specs


LONE = set('。，、；：！？）】〕」』”’…—,.;:!?)]')


def variant_mag(vi):
    """VARIANTS = [0, -a, +a, -2a, +2a]  ->  magnitude 0,1,1,2,2"""
    return (vi + 1) // 2


def variant_penalty(block, st, starts, nat, vi):
    """Cost of using a variant: tiny deviation cost + looseness + forbidden / ugly endings."""
    pen = 2.5 * variant_mag(vi)
    text = runs_text(block['runs'])
    n = len(starts)
    if n > 1:
        tail = text[starts[-1]:].strip('\u2060 \n')
        # never leave a lone punctuation mark / footnote marker as a last line
        if len(tail) <= 1 and (not tail or tail in LONE):
            return INF
        if tail and len(tail) <= 8 and re.fullmatch(r'\u2060?[\[［]\d+[\]］]\u2060?', tail.replace(' ', '')):
            return INF
        if len(tail) == 1:
            pen += 10.0
        elif len(tail) == 2 and st['align'] != 'j':
            pen += 40.0
        if st['align'] == 'j':
            for j in range(n - 1):
                _, w = line_geom(st, j)
                slack = (w - nat[j]) / st['fs']
                if slack > 1.5:
                    pen += (slack - 1.5) * 4
    return pen


def gap_pen(g):
    return 0.0 if g == 0 else 200.0 * g + 500.0 * (g - 1) ** 2


def _top(pg, reserve):
    """Slots reserved at the top of logical page `pg` (a spanning heading over both columns of a two-column module)."""
    return reserve if pg < 2 else 0


def paginate(n, s, f0, g1, g2, splittable, N=N, pg=2, reserve=0):
    """Place n lines of `s` slots each, starting at slot f0 of logical page `pg` (capped at 2).

    Returns dict(pieces, gaps, f_end, pg_end, extra) or None.
      pieces: line counts, first entry = lines on the current page; gaps: unused slots at the end of each page
      f_end: absolute slots used on the last page (== capacity when exactly full); pg_end: its page index (capped)
    """
    room = N - f0
    if n * s <= room:
        return dict(pieces=[n], gaps=[0], f_end=f0 + n * s, pg_end=pg, extra=0.0)
    if not splittable or s != 1:
        return None
    k1 = room - g1
    if k1 < 1 or k1 >= n:
        return None
    pieces, gaps = [k1], [g1]
    r = n - k1
    used_g2 = False
    idx = 0
    while True:
        cap = N - _top(min(pg + 1 + idx, 2), reserve)
        capn = N - _top(min(pg + 2 + idx, 2), reserve)
        if r <= cap:
            pieces.append(r); gaps.append(0)
            break
        if (r - cap) <= capn and g2 and not used_g2:
            take = cap - g2
            pieces.append(take); gaps.append(g2); used_g2 = True
            r -= take
            idx += 1
            continue
        pieces.append(cap); gaps.append(0)
        r -= cap
        idx += 1
    if g2 and not used_g2:
        return None
    extra = 0.0
    if k1 < 2:
        extra += 50.0
    if pieces[-1] == 1:
        extra += 50.0
    if pieces[-1] == 2 and n > 6:
        extra += 6.0
    pg_end = min(pg + len(pieces) - 1, 2)
    return dict(pieces=pieces, gaps=gaps, f_end=_top(pg_end, reserve) + pieces[-1], pg_end=pg_end, extra=extra)


def _norm_end(res, after, N, reserve):
    """State (f, pg) after a block: exact fill or overflowing `after` space opens the next page."""
    f, pg = res['f_end'], res['pg_end']
    single = len(res['pieces']) == 1
    if f >= N:
        pg = min(pg + 1, 2)
        return _top(pg, reserve), pg
    if single and after and f + after < N:
        f += after                     # space after a block is dropped at the bottom of a page (it would be a blank last line)
    return f, pg


def bef_options(lb):
    """Allowed 'space before' values for a block with their cost: headings may take one blank slot more or less
    (never less than the block's own `minbefore`)."""
    opts = _bef_options(lb)
    if lb.block.get('noshrink'):                                   # e.g. table-of-contents groups: never squeezed below their blank line
        opts = [o for o in opts if o[0] >= lb.st['before']] or opts
    lo = lb.block.get('minbefore')
    if lo is not None:
        opts = [o for o in opts if o[0] >= lo] or [(lo, 0.0)]
    return opts


def _bef_options(lb):
    st = lb.st
    base = st['before']
    if lb.block.get('k') == 'h' and st.get('slots', 1) == 1 and not st.get('top_keep'):
        opts = [(base, 0.0), (base + 1, 6.0)]
        if base >= 2:
            opts.append((base - 1, 4.0))
        return opts
    if lb.block.get('style') == 'secnum':
        return [(base, 0.0), (base + 1, 10.0)]
    if lb.block.get('style') == 'idxhead':
        return [(base, 0.0), (base + 1, 5.0), (max(0, base - 1), 5.0)]
    if base >= 1 and not st.get('top_keep') and st.get('slots', 1) == 1:
        return [(base, 0.0), (base + 1, 5.0), (base - 1, 5.0)]
    return [(base, 0.0)]


def solve(lbs, N=N, reserve=0, tail_min=2):
    """DP over blocks; state = (slots used on the current page, logical page index capped at 2).

    reserve > 0 keeps `reserve` slots free at the top of logical pages 0 and 1 (the two columns of the first physical
    page of a two-column module carry a spanning heading there).  With reserve == 0 the page index is irrelevant.

    Returns dict(pages=[{items:[(block, lo, hi, slot0)], gap:int}], variants=[v per block], cost=float)
    """
    nb = len(lbs)
    top = lambda pg: _top(pg, reserve)
    need = [0] * (nb + 1)
    depth = [0] * (nb + 1)          # length of the keep chain starting at i (capped)
    for i in range(nb - 1, -1, -1):
        b = lbs[i]
        st = b.st
        own = b.nl[0] * st['slots'] + st['after']
        depth[i] = 1
        if st['keep'] and i + 1 < nb and not lbs[i + 1].brk:
            nx = lbs[i + 1]
            if nx.st['keep'] and depth[i + 1] < 4:
                own += nx.st['before'] + need[i + 1]
                depth[i] = depth[i + 1] + 1
            elif not nx.st['keep']:
                own += min(st['keep'], nx.nl[0]) * nx.st['slots']
        need[i] = own

    pg_init = 0 if reserve else 2
    dp = [dict() for _ in range(nb + 1)]
    dp[0][(top(pg_init), pg_init)] = (0.0, None, None)
    for i, b in enumerate(lbs):
        st = b.st
        s = st['slots']
        prev_keep = lbs[i - 1].st['keep'] if i > 0 and not b.brk else 0
        top_bef = st['before'] if st.get('top_keep') else 0
        bopts = bef_options(b)
        for (f, pg), (c0, _, _) in dp[i].items():
            opts = []                                   # (start slot, cost, gap before, broke, page of the start)
            if not b.brk:
                if f == top(pg):
                    if not b.block.get('nostart') or i == 0:
                        opts.append((f + top_bef, c0, 0, False, pg))
                else:
                    for bef, bc in bopts:
                        if f + bef < N:
                            opts.append((f + bef, c0 + bc, 0, False, pg))
            if (f > top(pg) or b.brk) and not (prev_keep and not b.brk) and not (b.block.get('nostart') and i > 0):
                g = (N - f) if f > top(pg) else 0
                pg2 = min(pg + 1, 2)
                opts.append((top(pg2) + top_bef, c0 + (0.0 if b.brk else gap_pen(g)), g, True, pg2))
            for f0, c1, g0, broke, pgs in opts:
                for vi, n in enumerate(b.nl):
                    vp = b.pen[vi]
                    if vp == INF:
                        continue
                    if st['keep'] and f0 + need[i] > N and f0 > top(pgs) + top_bef:
                        continue
                    if st['keep'] and f0 + b.nl[vi] * s > N:
                        continue
                    for g1 in ((0,) if not b.splittable else (0, 1, 2)):
                        for g2 in (0, 1):
                            res = paginate(n, s, f0, g1, g2, b.splittable, N, pgs, reserve)
                            if res is None:
                                continue
                            pieces = res['pieces']
                            if len(pieces) == 1 and (g1 or g2):
                                continue
                            if prev_keep and len(pieces) > 1 and pieces[0] < prev_keep:
                                continue
                            cost = c1 + vp + res['extra'] + sum(gap_pen(g) for g in res['gaps'])
                            _push(dp[i + 1], _norm_end(res, st['after'], N, reserve), cost, (f, pg),
                                  (vi, f0, broke, g0, g1, g2, pgs))
        if not dp[i + 1]:
            raise RuntimeError(f'no feasible layout at block {i}: {runs_text(b.block["runs"])[:30]!r}')

    best = None
    for (f, pg), (c, _, _) in dp[nb].items():
        used = f - top(pg)
        cc = c + (300.0 if 0 < used <= tail_min else 0.0)
        if best is None or cc < best[0]:
            best = (cc, (f, pg))
    cost, key = best
    choices = [None] * nb
    for i in range(nb, 0, -1):
        c, pk, ch = dp[i][key]
        choices[i - 1] = ch
        key = pk
    return replay(lbs, choices, cost, N, reserve)


def prev_keep_forbids_break(prev_keep, f):
    return False


def _push(d, key, c, pk, ch):
    if key not in d or c < d[key][0]:
        d[key] = (c, pk, ch)


def replay(lbs, choices, cost, N=N, reserve=0):
    pages = [dict(items=[], gap=0)]
    variants = []
    fresh = False                      # the previous block filled its page: the next block opens a new one
    for i, b in enumerate(lbs):
        vi, f0, broke, g0, g1, g2, pgs = choices[i]
        st = b.st
        s = st['slots']
        n = b.nl[vi]
        variants.append(vi)
        if broke:
            if pages[-1]['items']:
                pages[-1]['gap'] = g0 if not b.brk else 0
                pages.append(dict(items=[], gap=0))
        elif fresh and pages[-1]['items']:
            pages.append(dict(items=[], gap=0))
        fresh = False
        res = paginate(n, s, f0, g1, g2, b.splittable, N, pgs, reserve)
        pos = 0
        for pi, (cnt, gp) in enumerate(zip(res['pieces'], res['gaps'])):
            if pi > 0:
                pages.append(dict(items=[], gap=0))
            slot0 = f0 if pi == 0 else _top(len(pages) - 1, reserve)
            pages[-1]['items'].append((i, pos, pos + cnt, slot0))
            pages[-1]['gap'] = gp
            pos += cnt
        f_end, pg_end = res['f_end'], res['pg_end']
        single = len(res['pieces']) == 1
        if f_end >= N:
            fresh = True
    return dict(pages=pages, variants=variants, cost=cost)
