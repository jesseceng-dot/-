"""Text repairs for the four single trade books: punctuation typed as ASCII between Chinese characters, straight apostrophes,
spaces before closing marks, note markers normalised to '[n]' / '(n)'."""
import re
from .model import run, merge_runs, BR

_FW = {',': '，', ';': '；', ':': '：', '!': '！', '?': '？'}
_RE_ASCII_PUNCT = re.compile(r'(?<=[一-鿿”’）》])([,;:!?])(?=[一-鿿“‘（《])')
_RE_ASCII_PUNCT_END = re.compile(r'(?<=[一-鿿])([,;:!?])$')
_RE_APOS = re.compile(r"(?<=[A-Za-z])'(?=[A-Za-z]|\s|[）”，。；：])")
_RE_SPACE_CLOSE = re.compile(r'(?<=[A-Za-z0-9])[ 　]+(?=[）】》”’，。；：！？、])')
_RE_SPACE_OPEN = re.compile(r'(?<=[“‘（《])[ 　]+(?=[A-Za-z0-9一-鿿])')
CLOSE = '）】》”’，。；：！？、'


def fix_text(t):
    t = t.replace('\xa0', ' ')
    t = _RE_ASCII_PUNCT.sub(lambda m: _FW[m.group(1)], t)
    t = _RE_ASCII_PUNCT_END.sub(lambda m: _FW[m.group(1)], t)
    t = _RE_APOS.sub('’', t)
    t = _RE_SPACE_CLOSE.sub('', t)
    t = re.sub(r' {2,}', ' ', t)
    return t


def fix_runs(runs):
    out = []
    for r in runs:
        if r.get('i'):
            out.append(r)
            continue
        t = fix_text(r['t'])
        if t:
            out.append(dict(r, t=t))
    for i in range(len(out)):                            # a space at a run boundary before a closing mark
        if i and out[i]['t'].startswith(' ') and out[i]['t'].lstrip(' ')[:1] in CLOSE and not out[i - 1].get('i'):
            out[i] = dict(out[i], t=out[i]['t'].lstrip(' '))
        if i + 1 < len(out) and out[i + 1]['t'][:1] in CLOSE and not out[i].get('i'):
            out[i] = dict(out[i], t=out[i]['t'].rstrip(' '))
    return merge_runs([r for r in out if r['t'] != ''])


def fix_edges(runs):
    runs = [dict(r) for r in runs]
    while runs and runs[-1]['t'] in (BR, ' '):
        runs.pop()
    if runs and not runs[0].get('i'):
        runs[0]['t'] = runs[0]['t'].lstrip(' ')
    if runs and not runs[-1].get('i'):
        runs[-1]['t'] = runs[-1]['t'].rstrip(' ')
    return [r for r in runs if r['t'] != '']


NUM = re.compile(r'^[\[［(（〔]?\s*(\d+)\s*[\]］)）〕]?$')


def marker_text(t, fmt):
    m = NUM.match(t.strip())
    if not m:
        return None
    n = m.group(1)
    return f'({n})' if fmt == 'paren' else f'[{n}]'
