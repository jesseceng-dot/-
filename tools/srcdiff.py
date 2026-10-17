"""Source paragraphs that did not reach the typeset book (when bk_report's source-only count holds ordinary text):

    BOOK_SCRATCH=<dir> python -m tools.srcdiff NN [part ...]

Every paragraph of the given parts (all parts of the book if none) is cut into 12-character pieces; a paragraph most of
whose pieces are missing from the typeset text is printed.  Transcribed inline pictures make some false hits (the
source has no text where the typeset book has the transcription): look at each."""
import re
import sys

from . import bk, bk_extract as BE
from .model import runs_text


def _norm(t):
    return re.sub(r'[\s⁠ ­]+', '', t)


def main(b, parts):
    cfg = bk.book(b)
    have = []
    for m in cfg['modules']:
        for bl in getattr(m, 'blocks', None) or ():
            have.append(runs_text(bl.get('runs') or []))
            for _, r in (bl.get('cap') or []) + (bl.get('cap_top') or []):
                have.append(runs_text(r))
    text = _norm('\n'.join(have))
    C = bk.CFG[b]
    if not parts:
        parts = [p for x in [n for n, _ in C['front']] + list(C['body']) + [x[0] if isinstance(x, tuple) else x for x in C['back']]
                 for p in bk._parts(x)]
    for n in parts:
        for it in BE.items(bk.P(n)):
            if it['k'] == 'table':
                t = ''.join(r['t'] for row in it['rows'] for cell in row for r in cell if not r.get('i'))
            else:
                t = ''.join(r['t'] for r in it.get('runs', []) if not r.get('i'))
            t = _norm(t)
            if len(t) < 12:
                continue
            pieces = [t[i:i + 12] for i in range(0, len(t) - 11, 12)]
            bad = sum(1 for p in pieces if p not in text)
            if bad > 0.6 * len(pieces):
                print(n, it['k'], it.get('cls'), f'{bad}/{len(pieces)}', t[:80])


if __name__ == '__main__':
    main(int(sys.argv[1]), [int(x) for x in sys.argv[2:]])
