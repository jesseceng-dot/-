"""Build everything: four book PDFs, the merged collection, and the QA numbers."""
import os
import sys
import shutil
from . import style, books, build, collection

NAMES = ['book1', 'book2', 'book3', 'book4']
FILES = {'book1': '01-小逻辑.pdf', 'book2': '02-黑格尔早期神学著作.pdf', 'book3': '03-精神现象学.pdf',
         'book4': '04-哲学史讲演录.pdf'}


def main(which=None, dest=None):
    out = os.path.join(style.SCRATCH, 'out')
    os.makedirs(out, exist_ok=True)
    for n in (which or NAMES):
        build.build(getattr(books, n)(), os.path.join(out, n + '.pdf'))
    if which is None or set(which) == set(NAMES):
        collection.build_collection(out)
    if dest:
        os.makedirs(dest, exist_ok=True)
        for n in NAMES:
            shutil.copy(os.path.join(out, n + '.pdf'), os.path.join(dest, FILES[n]))
        shutil.copy(os.path.join(out, '贺麟中译黑格尔经典著作.pdf'), os.path.join(dest, '00-贺麟中译黑格尔经典著作（合集）.pdf'))


if __name__ == '__main__':
    args = sys.argv[1:]
    dest = None
    if args and args[0].startswith('--dest='):
        dest = args.pop(0)[7:]
    main(args or None, dest)
