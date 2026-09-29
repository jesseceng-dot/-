"""Compact structural outline of a part: headings and short/odd lines, body paragraphs collapsed."""
import sys, re
sys.path.insert(0, '/home/user/-')
from tools import extract


def show(part, maxlen=48, blocks=None):
    bl = blocks if blocks is not None else extract.parse_part(part)
    run = 0
    out = []
    for i, b in enumerate(bl):
        t = ''.join(r['t'] for r in b['runs']).replace('　', '␣').replace('\n', '⏎')
        flag = ''
        if b['runs'] and b['runs'][0].get('a') and re.match(r'[\[［]\d+[\]］]', b['runs'][0]['t']):
            flag = 'NOTE'
        short = len(t) <= maxlen
        if b['style'] in ('body', 'noindent') and not short and not flag:
            run += 1
            continue
        if flag and b['style'] in ('body', 'noindent', 'note'):
            run += 1
            continue
        if run:
            out.append(f'      … {run} para')
            run = 0
        out.append(f"{i:04d} {b['style']:8s} {b.get('src','')[:28]:28s} {t[:maxlen]}")
    if run:
        out.append(f'      … {run} para')
    return '\n'.join(out)


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print('=====', p)
        print(show(p))
