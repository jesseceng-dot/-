"""Plain text of a book for proof-reading: one paragraph per line, 'part:idx k|text', in chunks of about N characters
(<scratch>/text/cNNN.txt), so that a book can be read through slice by slice and every correction located.

    BOOK_SCRATCH=<dir> python -m tools.proof_dump N [chunk-size]

Pictures inside a line show as 〈img〉, linked note marks as ⁽…⁾, line breaks as ⏎.
"""
import os, sys, glob
from . import bk_extract as BE, bk
b = int(sys.argv[1]); N = int(sys.argv[2]) if len(sys.argv) > 2 else 14000
C = bk.CFG[b]
parts = []
if C.get('copyright') is not None: parts.append(C['copyright'])
parts += [x for n, _ in C['front'] for x in bk._parts(n)]
for x in C['body']: parts += bk._parts(x)
parts += [x[0] if isinstance(x, tuple) else x for x in C['back']] + list(C.get('endnotes', ()))
out = os.path.join(os.environ['BOOK_SCRATCH'], 'text'); os.makedirs(out, exist_ok=True)
for f in glob.glob(out + '/*.txt'): os.remove(f)
chunk, size, k = [], 0, 1
def flush():
    global chunk, size, k
    if chunk:
        open(f'{out}/c{k:03d}.txt', 'w').write('\n'.join(chunk) + '\n'); k += 1; chunk, size = [], 0
for n in parts:
    for i, it in enumerate(BE.items(bk.P(n))):
        if it['k'] == 'img':
            line = f'{n}:{i} IMG {it["src"]}'
        elif it['k'] == 'table':
            line = f'{n}:{i} TABLE ' + ' ‖ '.join(' | '.join(''.join(r['t'] for r in c if not r.get('i')).replace('\n', '/') for c in row) for row in it['rows'])
        else:
            t = ''
            for r in it.get('runs', []):
                if r.get('i'): t += '〈img〉'
                elif r.get('s') and (r.get('h') or r.get('a')): t += '⁽' + r['t'] + '⁾'
                else: t += r['t']
            line = f'{n}:{i} {it["k"]}{it.get("lvl","")}|' + t.replace('\n', '⏎').replace(' ', '⏎')
        chunk.append(line); size += len(line)
        if size > N: flush()
flush()
print(k - 1, 'chunks')
