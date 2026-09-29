"""Build the eleven Dewey volumes + the merged collection:  python -m tools.dewey_make_all --dest=out/dewey"""
import os
import sys
import shutil
from . import style, dewey, dewey_build, dewey_collection


def main(vols=None, dest=None):
    out = os.path.join(style.SCRATCH, 'out')
    os.makedirs(out, exist_ok=True)
    for v in vols or range(1, 12):
        dewey_build.main(v)
    coll = f'00-{dewey_collection.TITLE}（合集）.pdf'
    if vols is None:
        dewey_collection.build_collection(out)
    if dest:
        os.makedirs(dest, exist_ok=True)
        for v in vols or range(1, 12):
            shutil.copy(os.path.join(out, f'd{v}.pdf'), os.path.join(dest, dewey.FILES[v]))
        if vols is None:
            shutil.copy(os.path.join(out, coll), os.path.join(dest, coll))


if __name__ == '__main__':
    args = sys.argv[1:]
    dest = None
    if args and args[0].startswith('--dest='):
        dest = args.pop(0)[7:]
    main([int(a) for a in args] or None, dest)
