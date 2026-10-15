"""The solved page plan of one module, block by block: which lines of which paragraph are on which page, the variant
chosen, the slots, keeps and splits -- to see why a page came out as it did (a widow, a gap, a heading moved).

    BOOK_SCRATCH=<dir> BOOK_GEOM=k16 BOOK_FONT_DIR=<dir>/fonts python -m tools.modplan N partNNNN [page-from page-to]
"""
import os, sys
from . import book as B, bk
from .measure import Measurer
from .model import runs_text
b, mid = int(sys.argv[1]), sys.argv[2]
m = Measurer()
cfg = bk.book(b)
mods = [x for x in cfg['modules'] if x.mid == mid]
bb = B.BookBuilder(dict(cfg, modules=mods), m)
bb.typeset_all()
m.close()
mod = mods[0]
lbs, plan = mod.lbs, mod.plan
for pi, p in enumerate(plan['pages']):
    if len(sys.argv) > 3 and not int(sys.argv[3]) <= pi <= int(sys.argv[4]):
        continue
    print(f'--- page {pi} gap {p["gap"]}')
    for bi, lo, hi, s0 in p['items']:
        lb = lbs[bi]; vi = plan['variants'][bi]
        print(f'  b{bi:3d} {lb.block["k"]:4s} {lb.block.get("style",""):8s} lines {lo}-{hi}/{lb.nl[vi]} slot0 {s0} slots {lb.st["slots"]} before {lb.st["before"]} keep {lb.st["keep"]} vi {vi} nl {lb.nl} split {lb.splittable} | {runs_text(lb.block["runs"])[:30]!r}')
