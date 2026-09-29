"""Measure -> solve -> render for one module (a chapter/section/front-matter item)."""
from . import style
from .layout import LB, sty, build_specs, variant_penalty, solve, INF
from .model import runs_len


def make_lbs(blocks, measurer, grid='body', variants=None, vary_min_chars=18):
    variants = variants if variants is not None else style.VARIANTS
    lbs = []
    specs, owner = [], []
    for i, b in enumerate(blocks):
        st = sty(b, grid)
        lb = LB(idx=i, block=b, st=st)
        lb.brk = bool(b.get('brk'))
        if b['k'] in ('img', 'space'):
            n = int(b.get('n', 1))
            lb.nl, lb.pen, lb.starts, lb.nat = [n], [0.0], [[0] * n], [[0.0] * n]
            lb.splittable = False
            lbs.append(lb)
            continue
        vary = (st['align'] == 'j' or b['style'] == 'index' or b['style'].startswith('toc')) and runs_len(b['runs']) >= (24 if b['style'].startswith('toc') else vary_min_chars) and not b.get('novary')
        lb.splittable = st['slots'] == 1 and st['keep'] == 0 and not b.get('nosplit')
        vs = variants if vary else variants[:1]
        for vi, s in enumerate(build_specs(b, vs, grid)):
            specs.append(s)
            owner.append((i, vi))
        lbs.append(lb)
    res = measurer.measure(specs) if specs else []
    for (i, vi), r in zip(owner, res):
        lb = lbs[i]
        assert len(lb.starts) == vi
        lb.starts.append(r['starts'])
        lb.nat.append(r['nat'])
        lb.nl.append(len(r['starts']))
        # sanity: measured height must equal lines * slots * LINE, otherwise a line box grew
        exp = len(r['starts']) * lb.st['slots'] * lb.st['pitch']
        if abs(r['h'] - exp) > 0.6:
            lb.block.setdefault('warn', []).append(f'height {r["h"]:.2f} != {exp:.2f}')
    for lb in lbs:
        if lb.block['k'] in ('img', 'space'):
            continue
        lb.pen = [variant_penalty(lb.block, lb.st, lb.starts[vi], lb.nat[vi], vi) for vi in range(len(lb.nl))]
        if all(p == INF for p in lb.pen):        # no acceptable variant: keep the layout going, the checker reports it
            lb.pen = [5000.0 + p for p in range(len(lb.pen))]
            lb.block['warn'] = lb.block.get('warn', []) + ['no variant avoids a lone marker/punctuation last line']
    return lbs


def typeset(blocks, measurer, grid='body', reserve=0, variants=None, tail_min=2):
    from .layout import GRIDS
    lbs = make_lbs(blocks, measurer, grid, variants)
    plan = solve(lbs, GRIDS[grid]['n'], reserve, tail_min)
    return lbs, plan
