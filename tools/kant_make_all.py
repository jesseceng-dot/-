"""Build the ten Kant volumes + the merged collection:  python -m tools.kant_make_all --dest=out/kant"""
import os
import sys
import shutil
from . import style, kant, kant_build, kant_collection


def main(vols=None, dest=None):
    out = os.path.join(style.SCRATCH, 'out')
    os.makedirs(out, exist_ok=True)
    for v in vols or range(1, 11):
        kant_build.main(v)
    if vols is None:
        kant_collection.build_collection(out)
    if dest:
        os.makedirs(dest, exist_ok=True)
        for v in vols or range(1, 11):
            shutil.copy(os.path.join(out, f'k{v}.pdf'), os.path.join(dest, kant.FILES[v]))
        if vols is None:
            shutil.copy(os.path.join(out, f'{kant_collection.TITLE}（合集）.pdf'), os.path.join(dest, f'00-{kant_collection.TITLE}（合集）.pdf'))


if __name__ == '__main__':
    args = sys.argv[1:]
    dest = None
    if args and args[0].startswith('--dest='):
        dest = args.pop(0)[7:]
    main([int(a) for a in args] or None, dest)
