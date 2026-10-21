"""Build one of the four trade books:  BOOK_SCRATCH=<dir> BOOK_GEOM=k16 python -m tools.bk_build 2 [--redo=part0004,notes1]"""
import os
import sys
import json
from . import style, build, bk


def blank_foot_figures(cfg):
    """In-text figures that leave the foot of a page blank: the figures of a page that holds nothing else and that the
    solver could not fill (a chapter's last page aside: a chapter may end anywhere).  Headings and the 'see plate N' lines
    of figures moved before do not count as text (book 71: an appendix of figures under its heading); C['fig_gap_any']
    (book 71): the figures of any page left short, also among text that the solver could not bring up to fill it."""
    C = bk.CFG.get(cfg.get('vol'), {})
    out = []
    for mod in cfg['modules']:
        if mod.kind != 'text' or not mod.plan:
            continue
        pages = mod.plan['pages']
        for pi, p in enumerate(pages[:-1]):
            lbs = [mod.lbs[it[0]] for it in p['items']]
            blocks = [lb.block for lb in lbs]
            nx = pages[pi + 1]['items'][0] if pages[pi + 1]['items'] else None
            if C.get('fig_gap_any') and p['gap'] and p['items'] and nx and mod.lbs[nx[0]].block.get('fig_src'):
                out.append(mod.lbs[nx[0]].block['fig_src'])  # (the figure that opens the next page, too big for this one)
            if p['gap'] and any(x['k'] == 'img' for x in blocks) and (C.get('fig_gap_any') or
                    all(x['k'] == 'img' or x['k'] == 'h' and lb.st.get('keep') or x.get('plate_ref') for lb, x in zip(lbs, blocks))):
                out += [x['fig_src'] for x in blocks if x.get('fig_src')]
    return out


def plates_for_blank_feet(b):
    """(books whose figures stay in the text) A figure that would leave the foot of a page blank goes to the back of the
    book, one per page, with links both ways (bk.plate_figs reads the list written here).  Starting from every figure in
    the text: typeset, move the figures found, typeset again until none is left (only the chapters concerned change)."""
    from . import book as B
    from .measure import Measurer
    path = os.path.join(style.SCRATCH, 'plate_figs.json')
    found = []
    for _ in range(8):
        json.dump(found, open(path, 'w', encoding='utf8'))
        build.calibrate_all()
        m = Measurer()
        cfg = bk.book(b)
        B.BookBuilder(cfg, m).typeset_all()
        m.close()
        new = [x for x in blank_foot_figures(cfg) if x not in found]
        if not new:
            break
        print('to the back (would leave a page foot blank):', ', '.join(new), flush=True)
        found += new
    return found


def main(b, redo=()):
    from . import snap
    snap.ensure(bk.CFG[b]['scratch'])                     # pictures of the tables that are set as images (book 16)
    if bk.CFG[b].get('fig_inline'):
        plates_for_blank_feet(b)
    cfg = bk.book(b)
    out = os.path.join(style.SCRATCH, 'out')
    os.makedirs(out, exist_ok=True)
    return build.build(cfg, os.path.join(out, f'b{b}.pdf'), redo)


if __name__ == '__main__':
    b = int(sys.argv[1])
    redo = tuple(a[7:].split(',') for a in sys.argv[2:] if a.startswith('--redo='))
    main(b, redo[0] if redo else ())
