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
_LAT_END = re.compile(r'[A-Za-z0-9\u00c0-\u024f.,;:!?)\]’\']$')
_LAT_START = re.compile(r'^[A-Za-z0-9\u00c0-\u024f(\[‘“"]')


def _word_space(out, i):
    """out[i] is nothing but the space between two Latin words set in runs of their own (<i>A</i> <i>History</i>): it stays."""
    return (0 < i < len(out) - 1 and not out[i]['t'].strip(' ') and not out[i - 1].get('i') and not out[i + 1].get('i')
            and bool(_LAT_END.search(out[i - 1]['t'])) and bool(_LAT_START.search(out[i + 1]['t'])))


def fix_text(t):
    t = t.replace('\xa0', ' ')
    t = _RE_ASCII_PUNCT.sub(lambda m: _FW[m.group(1)], t)
    t = _RE_ASCII_PUNCT_END.sub(lambda m: _FW[m.group(1)], t)
    t = _RE_APOS.sub('’', t)
    t = _RE_SPACE_CLOSE.sub('', t)
    t = re.sub(r' {2,}', ' ', t)
    t = re.sub(r'(?<=\d)([–—~～])(?=\d)', '\\1\u2060', t)          # a range of numbers (pp.123–132) is not broken after its dash
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
        if i and out[i - 1]['t'].endswith(BR) and not out[i].get('i'):
            out[i] = dict(out[i], t=out[i]['t'].lstrip(' '))           # (no space at the start of a line after a forced break)
        if i and out[i]['t'].startswith(' ') and out[i]['t'].lstrip(' ')[:1] in CLOSE and not out[i - 1].get('i') \
                and not _word_space(out, i):
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


NUM = re.compile(r'^(?:[註注])?[\[［(（〔]?\s*(?:校(?=\d+[\]］]))?(\d+)\s*[\]］)）〕]?[．.]?$')     # ([校1]: a reviser's note, book 17)


def marker_text(t, fmt):
    m = NUM.match(t.strip())
    if not m:
        return None
    n = m.group(1)
    if fmt == 'zhu':
        return f'註{n}'
    if fmt == 'sqcirc':                                 # [n] author's notes; the ebook's bracketed / 0n marks are translator's notes: ①②③
        tt = t.strip()
        if tt.startswith(('[', '［')) or re.match(r'^0\d', tt):
            return chr(0x2460 + int(n) - 1) if 0 < int(n) <= 20 else f'({n})'
        return f'[{n}]'
    if fmt == 'keep':                                   # the ebook's own brackets: [n] author's notes, (n) translator's notes
        return f'({n})' if t.strip().startswith(('(', '（')) else f'[{n}]'
    if fmt == 'sq' and '校' in t:
        return f'[校{n}]'
    return f'({n})' if fmt == 'paren' else f'[{n}]'
