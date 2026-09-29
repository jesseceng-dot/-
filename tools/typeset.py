"""Measure -> solve -> render for one module (a chapter/section/front-matter item)."""
from . import style
from .layout import LB, sty, build_specs, variant_penalty, solve, INF
from .model import runs_len


def make_lbs(blocks, measurer, variants=None, vary_min_chars=40):
    variants = variants if variants is not None else style.VARIANTS
    lbs = []
    specs, owner = [], []
    for i, b in enumerate(blocks):
        st = sty(b)
        lb = LB(idx=i, block=b, st=st)
        lb.brk = bool(b.get('brk'))
        vary = st['align'] == 'j' and runs_len(b['runs']) >= vary_min_chars and not b.get('novary')
        lb.splittable = st['slots'] == 1 and st['keep'] == 0 and not b.get('nosplit')
        vs = variants if vary else variants[:1]
        for vi, s in enumerate(build_specs(b, vs)):
            specs.append(s)
            owner.append((i, vi))
        lbs.append(lb)
    res = measurer.measure(specs)
    for (i, vi), r in zip(owner, res):
        lb = lbs[i]
        assert len(lb.starts) == vi
        lb.starts.append(r['starts'])
        lb.nat.append(r['nat'])
        lb.nl.append(len(r['starts']))
        # sanity: measured height must equal lines * slots * LINE, otherwise a line box grew
        exp = len(r['starts']) * lb.st['slots'] * style.LINE
        if abs(r['h'] - exp) > 0.6:
            lb.block.setdefault('warn', []).append(f'height {r["h"]:.2f} != {exp:.2f}')
    for lb in lbs:
        lb.pen = [variant_penalty(lb.block, lb.st, lb.starts[vi], lb.nat[vi], vi) for vi in range(len(lb.nl))]
    return lbs


def typeset(blocks, measurer):
    lbs = make_lbs(blocks, measurer)
    plan = solve(lbs)
    return lbs, plan
