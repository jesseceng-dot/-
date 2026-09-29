"""Build one volume of the Dewey selection:  python -m tools.dewey_build 2 [--redo=part0030,notes1]"""
import os
import sys
from . import style, build, dewey


def main(v, redo=()):
    cfg = dewey.book(v)
    cfg['meta']['subject'] = dewey.SERIES
    out = os.path.join(style.SCRATCH, 'out')
    os.makedirs(out, exist_ok=True)
    return build.build(cfg, os.path.join(out, f'd{v}.pdf'), redo)


if __name__ == '__main__':
    v = int(sys.argv[1])
    redo = tuple(a[7:].split(',') for a in sys.argv[2:] if a.startswith('--redo='))
    main(v, redo[0] if redo else ())
