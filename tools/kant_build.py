"""Build one volume of the Kant collection:  python -m tools.kant_build 2 [--redo=part0030,notes1]"""
import os
import sys
from . import style, build, kant


def main(v, redo=()):
    cfg = kant.book(v)
    cfg['meta']['subject'] = kant.SERIES
    out = os.path.join(style.SCRATCH, 'out')
    os.makedirs(out, exist_ok=True)
    return build.build(cfg, os.path.join(out, f'k{v}.pdf'), redo)


if __name__ == '__main__':
    v = int(sys.argv[1])
    redo = tuple(a[7:].split(',') for a in sys.argv[2:] if a.startswith('--redo='))
    main(v, redo[0] if redo else ())
