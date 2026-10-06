"""Build the four trade books (each in its own scratch dir, 16开 page):  python -m tools.bk_make_all --scratch=<dir> --dest=out/16k [1 2 3 4]"""
import os
import sys
import shutil
import subprocess
from . import bk


def main(scratch, vols=None, dest=None):
    procs = []
    for b in vols or sorted(bk.CFG):
        sd = os.path.join(scratch, bk.CFG[b]['scratch'])
        env = dict(os.environ, BOOK_SCRATCH=sd, BOOK_GEOM='k16', BOOK_FONT_DIR=os.path.join(sd, 'fonts'),
                   BOOK_CJK=bk.CFG[b].get('cjk', 'SC'))
        procs.append((b, subprocess.Popen([sys.executable, '-m', 'tools.bk_build', str(b)], env=env)))
    for b, p in procs:
        if p.wait():
            raise SystemExit(f'book {b} failed')
    if dest:
        os.makedirs(dest, exist_ok=True)
        for b in vols or sorted(bk.CFG):
            shutil.copy(os.path.join(scratch, bk.CFG[b]['scratch'], 'out', f'b{b}.pdf'), os.path.join(dest, bk.FILES[b]))


if __name__ == '__main__':
    args = sys.argv[1:]
    scratch = dest = None
    while args and args[0].startswith('--'):
        a = args.pop(0)
        if a.startswith('--scratch='):
            scratch = a[10:]
        elif a.startswith('--dest='):
            dest = a[7:]
    main(scratch, [int(a) for a in args] or None, dest)
