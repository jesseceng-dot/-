"""Block styles, measuring, and the page-fill solver.

Vertical layout is a grid of NLINES slots per page.  Every block occupies a whole number of slots,
so all pages of running text carry exactly NLINES lines and their last baselines coincide.
The solver chooses, per paragraph, one of a few imperceptible letter-spacing variants so that the
number of lines each paragraph takes lets every page fill exactly, headings never end a page, and
no page ends with a single stray line.  Only if that is impossible is one page stretched slightly.
"""
from dataclasses import dataclass, field
from . import style
from .model import runs_html, runs_len, runs_text

INF = float('inf')
N = style.NLINES

# ---- grids ---------------------------------------------------------------------------------------
GRIDS = {
    # n slots per (logical) page, pitch in pt, cols per physical page, column width, gutter
    'body':   dict(n=27, pitch=17.0,   cols=1, W=294.0, gutter=0.0),
    'small1': dict(n=40, pitch=11.475, cols=1, W=294.0, gutter=0.0),
    'small2': dict(n=40, pitch=11.475, cols=2, W=139.0, gutter=16.0),
}

# style table: em-based indents use the style's own font size (fs, pt).
#   first = first-line indent (em), left/right = block indents (em), slots = grid lines per text line
STYLES = {
    #            css class   fs    first left right align slots before after keep
    'body':     dict(cls='s-body',    fs=10.5, first=2, left=0, right=0, align='j', slots=1, before=0, after=0, keep=0),
    'noindent': dict(cls='s-body',    fs=10.5, first=0, left=0, right=0, align='j', slots=1, before=0, after=0, keep=0),
    'quote':    dict(cls='s-quote',   fs=10.0, first=2, left=2, right=2, align='j', slots=1, before=0, after=0, keep=0),
    'verse':    dict(cls='s-quote',   fs=10.0, first=0, left=4, right=0, align='l', slots=1, before=0, after=0, keep=0),
    'center':   dict(cls='s-body',    fs=10.5, first=0, left=0, right=0, align='c', slots=1, before=0, after=0, keep=0),
    'right':    dict(cls='s-body',    fs=10.5, first=0, left=0, right=2, align='r', slots=1, before=0, after=0, keep=0),
    'left':     dict(cls='s-body',    fs=10.5, first=0, left=0, right=0, align='l', slots=1, before=0, after=0, keep=0),
    'sep':      dict(cls='s-body',    fs=10.5, first=0, left=0, right=0, align='c', slots=1, before=1, after=1, keep=0),
    'secnum':   dict(cls='s-secnum',  fs=9.5,  first=0, left=0, right=0, align='c', slots=1, before=0, after=0, keep=2),
    'h1':       dict(cls='s-h1',      fs=17.0, first=0, left=0, right=0, align='c', slots=2, before=3, after=2, keep=2, top_keep=1),
    'h2':       dict(cls='s-h2',      fs=14.0, first=0, left=0, right=0, align='c', slots=1, before=2, after=1, keep=2),
    'h3':       dict(cls='s-h3',      fs=12.0, first=0, left=0, right=0, align='c', slots=1, before=1, after=0, keep=2),
    'h4':       dict(cls='s-h4',      fs=11.0, first=0, left=0, right=0, align='c', slots=1, before=1, after=0, keep=2),
    'h5':       dict(cls='s-h5',      fs=10.5, first=0, left=2, right=0, align='l', slots=1, before=0, after=0, keep=2),
    'h6':       dict(cls='s-h6',      fs=10.5, first=0, left=2, right=0, align='l', slots=1, before=0, after=0, keep=2),
    'h7':       dict(cls='s-h7',      fs=10.0, first=0, left=4, right=0, align='l', slots=1, before=0, after=0, keep=2),
    'toc1':     dict(cls='s-toc1',    fs=10.5, first=-1, left=1, right=3, align='l', slots=1, before=1, after=0, keep=0),
    'toc2':     dict(cls='s-toc2',    fs=10.5, first=-1, left=2.5, right=3, align='l', slots=1, before=0, after=0, keep=0),
    'toc3':     dict(cls='s-toc3',    fs=10.0, first=-1, left=4.5, right=3, align='l', slots=1, before=0, after=0, keep=0),
    'tochead':  dict(cls='s-h1',      fs=17.0, first=0, left=0, right=0, align='c', slots=2, before=3, after=2, keep=2, top_keep=1),
}
# small-grid (notes / indexes) style overrides
STYLES_SMALL = {
    'h1':      dict(cls='s-h1', fs=17.0, first=0, left=0, right=0, align='c', slots=3, before=4, after=3, keep=3, top_keep=1),
    'note':    dict(cls='s-note', fs=8.5, first=-3, left=3, right=0, align='j', slots=1, before=0, after=0, keep=0),
    'index':   dict(cls='s-index', fs=8.5, first=-1, left=1, right=0, align='l', slots=1, before=0, after=0, keep=0),
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
    """Cost of using a variant: tiny deviation cost + looseness + forbidden endings."""
    pen = 2.5 * variant_mag(vi)
    text = runs_text(block['runs'])
    n = len(starts)
    if n > 1 and st['align'] == 'j':
        tail = text[starts[-1]:].strip()
        # never leave a lone punctuation mark / footnote marker as a last line
        if len(tail) <= 1 and (not tail or tail in LONE):
            return INF
        if tail and len(tail) <= 6 and tail.strip('0123456789[]［］()（）') == '':
            return INF
        for j in range(n - 1):
            _, w = line_geom(st, j)
            slack = (w - nat[j]) / st['fs']
            if slack > 1.5:
                pen += (slack - 1.5) * 4
    return pen


def gap_pen(g):
    return 0.0 if g == 0 else 200.0 * g + 500.0 * (g - 1) ** 2


def paginate(n, s, f0, g1, g2, splittable, N=N):
    """Place n lines of `s` slots each, starting at slot f0 of the current page.

    Returns (pieces, gaps, f1, extra_pen) or None.
      pieces: list of line counts, first entry = lines on the current page; gaps: unused slots at the end of each page
      f1: slots used on the last page (0 = exactly full).
    """
    room = N - f0
    if n * s <= room:
        f1 = f0 + n * s
        return [n], [0], (0 if f1 >= N else f1), 0.0
    if not splittable or s != 1:
        return None
    k1 = room - g1
    if k1 < 1 or k1 >= n:
        return None
    pieces, gaps = [k1], [g1]
    r = n - k1
    used_g2 = False
    while True:
        if r <= N:
            pieces.append(r); gaps.append(0)
            break
        if (r - N) <= N and g2 and not used_g2:
            take = N - g2
            pieces.append(take); gaps.append(g2); used_g2 = True
            r -= take
            continue
        pieces.append(N); gaps.append(0)
        r -= N
    if g2 and not used_g2:
        return None
    extra = 0.0
    if k1 < 2:
        extra += 50.0
    if pieces[-1] == 1:
        extra += 50.0
    if pieces[-1] == 2 and n > 6:
        extra += 6.0
    f1 = pieces[-1] if pieces[-1] < N else 0
    return pieces, gaps, f1, extra


def bef_options(lb):
    """Allowed 'space before' values for a block with their cost: headings may take one blank slot more or less."""
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
    return [(base, 0.0)]


def solve(lbs, N=N):
    """DP over blocks; state = slots used on the current page (0..N-1, 0 = fresh page).

    Returns dict(pages=[{items:[(block, lo, hi, slot0)], gap:int}], variants=[v per block], cost=float)
    """
    nb = len(lbs)
    # need[i]: slots (after the block's own before-space) that must be free on the page so that keep-chains stay together
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

    dp = [dict() for _ in range(nb + 1)]
    dp[0][0] = (0.0, None, None)
    for i, b in enumerate(lbs):
        st = b.st
        s = st['slots']
        prev_keep = lbs[i - 1].st['keep'] if i > 0 and not b.brk else 0
        top_bef = st['before'] if st.get('top_keep') else 0
        bopts = bef_options(b)
        for f, (c0, _, _) in dp[i].items():
            opts = []                                   # (start slot, cost, gap before, broke)
            if not b.brk:
                if f == 0:
                    if not b.block.get('nostart') or i == 0:
                        opts.append((top_bef, c0, 0, False))
                else:
                    for bef, bc in bopts:
                        if f + bef < N:
                            opts.append((f + bef, c0 + bc, 0, False))
            if (f > 0 or b.brk) and not (prev_keep and not b.brk) and not (b.block.get('nostart') and i > 0):
                g = (N - f) if f > 0 else 0
                opts.append((top_bef, c0 + (0.0 if b.brk else gap_pen(g)), g, True))
            for f0, c1, g0, broke in opts:
                for vi, n in enumerate(b.nl):
                    vp = b.pen[vi]
                    if vp == INF:
                        continue
                    if st['keep'] and f0 + need[i] > N and f0 > top_bef:
                        continue
                    if st['keep'] and f0 + b.nl[vi] * s > N:
                        continue
                    for g1 in ((0,) if not b.splittable else (0, 1, 2)):
                        for g2 in (0, 1):
                            res = paginate(n, s, f0, g1, g2, b.splittable, N)
                            if res is None:
                                continue
                            pieces, gaps, f1, extra = res
                            if len(pieces) == 1 and (g1 or g2):
                                continue
                            if prev_keep and len(pieces) > 1 and pieces[0] < prev_keep:
                                continue
                            cost = c1 + vp + extra + sum(gap_pen(g) for g in gaps)
                            if len(pieces) == 1 and f1 and st['after'] and f1 + st['after'] < N:
                                f1 += st['after']
                            elif len(pieces) == 1 and st['after'] and f1 + st['after'] >= N:
                                f1 = 0
                            _push(dp[i + 1], f1, cost, f, (vi, f0, broke, g0, g1, g2))
        if not dp[i + 1]:
            raise RuntimeError(f'no feasible layout at block {i}: {runs_text(b.block["runs"])[:30]!r}')

    best = None
    for f, (c, _, _) in dp[nb].items():
        cc = c + (300.0 if 0 < f <= 2 else 0.0)
        if best is None or cc < best[0]:
            best = (cc, f)
    cost, f = best
    choices = [None] * nb
    for i in range(nb, 0, -1):
        c, pf, ch = dp[i][f]
        choices[i - 1] = ch
        f = pf
    return replay(lbs, choices, cost, N)


def prev_keep_forbids_break(prev_keep, f):
    return False


def _push(d, f, c, pf, ch):
    if f not in d or c < d[f][0]:
        d[f] = (c, pf, ch)


def replay(lbs, choices, cost, N=N):
    pages = [dict(items=[], gap=0)]
    used = 0
    variants = []
    for i, b in enumerate(lbs):
        vi, f0, broke, g0, g1, g2 = choices[i]
        st = b.st
        s = st['slots']
        n = b.nl[vi]
        variants.append(vi)
        if broke:
            if pages[-1]['items']:
                pages[-1]['gap'] = g0 if not b.brk else 0
                pages.append(dict(items=[], gap=0))
        elif used == 0 and pages[-1]['items']:
            pages.append(dict(items=[], gap=0))
        pieces, gaps, f1, _ = paginate(n, s, f0, g1, g2, b.splittable, N)
        pos = 0
        for pi, (cnt, gp) in enumerate(zip(pieces, gaps)):
            if pi > 0:
                pages.append(dict(items=[], gap=0))
            slot0 = f0 if pi == 0 else 0
            pages[-1]['items'].append((i, pos, pos + cnt, slot0))
            pages[-1]['gap'] = gp
            pos += cnt
        used = f1
        if len(pieces) == 1 and f1 and st['after'] and f1 + st['after'] < N:
            used = f1 + st['after']
        elif len(pieces) == 1 and st['after'] and f1 + st['after'] >= N:
            used = 0
    return dict(pages=pages, variants=variants, cost=cost)
