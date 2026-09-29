"""Unpack the AZW3 (KindleUnpack via the `mobi` package) into <scratch>/unpack/x/mobi8/OEBPS/{Text,Images,...}."""
import os
import shutil
import sys
import mobi
from . import style

def main(src=None):
    src = src or os.path.join(style.ROOT, 'source', 'hegel-collection.azw3')
    dst = os.path.join(style.SCRATCH, 'unpack', 'x')
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp, _ = mobi.extract(src)
    shutil.move(tmp, dst)
    print('unpacked to', dst)

if __name__ == '__main__':
    main(*sys.argv[1:])
