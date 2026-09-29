"""Build one of the four trade books:  BOOK_SCRATCH=<dir> BOOK_GEOM=k16 python -m tools.bk_build 2 [--redo=part0004,notes1]"""
import os
import sys
from . import style, build, bk


def main(b, redo=()):
    cfg = bk.book(b)
    out = os.path.join(style.SCRATCH, 'out')
    os.makedirs(out, exist_ok=True)
    return build.build(cfg, os.path.join(out, f'b{b}.pdf'), redo)


if __name__ == '__main__':
    b = int(sys.argv[1])
    redo = tuple(a[7:].split(',') for a in sys.argv[2:] if a.startswith('--redo='))
    main(b, redo[0] if redo else ())
