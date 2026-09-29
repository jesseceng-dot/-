"""Targeted hyphenation of long Latin-script words at the end of otherwise loose lines.

Only lines whose justification slack exceeds LOOSE em and whose next line starts with a long foreign word are touched:
a soft hyphen (U+00AD) is inserted at a syllable boundary of that single word, then the module is re-typeset.
"""
import re
import pyphen
from .model import runs_text

LOOSE = 3.0
WORD = re.compile(r'[A-Za-zÄÖÜäöüßéèêáàâóòíìúùçñ]{8,}')
LEAD = '（“‘《〔[(「'
DIC = {'de': pyphen.Pyphen(lang='de_DE'), 'en': pyphen.Pyphen(lang='en_US'), 'it': pyphen.Pyphen(lang='it')}
GERMAN = re.compile(r'(ung|heit|keit|lich|isch|schaft|ismus|verhältnis|urteil|sein|bestimmung|begriff)\b|[äöüß]', re.I)
LATIN = re.compile(r'(us|um|is|ae|orum|io|tas|ens|ans)\b', re.I)


def _w(ch):
    from .normalize import _w as w
    return w(ch)


def pick_dic(word):
    if GERMAN.search(word):
        return DIC['de']
    if LATIN.search(word) and not re.search(r'(ing|tion|ness|ment|ly|ed|al)\b', word):
        return DIC['it']
    return DIC['en']


def hyphenate_blocks(mod, log=None):
    """Insert soft hyphens; returns number of words touched."""
    if mod.kind != 'text' or not mod.plan or mod.grid != 'body':
        return 0
    n = 0
    for lb in mod.lbs:
        b = lb.block
        if b['k'] != 'p' or lb.st['align'] != 'j':
            continue
        vi = mod.plan['variants'][lb.idx]
        starts = lb.starts[vi]
        text = runs_text(b['runs'])
        edits = []
        for j in range(len(starts) - 1):
            wj = lb.st['W'] - (lb.st['left'] + lb.st['right'] + (lb.st['first'] if j == 0 else 0)) * lb.st['fs']
            slack = (wj - lb.nat[vi][j]) / lb.st['fs']
            if slack <= LOOSE:
                continue
            pos = starts[j + 1]
            k = pos
            while k < len(text) and text[k] in LEAD:
                k += 1
            m = WORD.match(text, k)
            if not m or '­' in m.group(0):
                continue
            word = m.group(0)
            lead_w = sum(_w(c) for c in text[pos:k])
            best = None
            for p in pick_dic(word).positions(word):
                if p < 3 or len(word) - p < 3:
                    continue
                need = lead_w + sum(_w(c) for c in word[:p]) + 0.4
                if need <= slack - 0.15:
                    best = p
            if best:
                edits.append((k + best, word, best))
        if not edits:
            continue
        # apply edits from the back so offsets stay valid
        runs = [dict(r) for r in b['runs']]
        for off, word, p in sorted(edits, reverse=True):
            pos = 0
            for r in runs:
                if pos <= off < pos + len(r['t']):
                    o = off - pos
                    r['t'] = r['t'][:o] + '­' + r['t'][o:]
                    break
                pos += len(r['t'])
            n += 1
            if log is not None:
                log.append((mod.mid, word[:p] + '-' + word[p:]))
        b['runs'] = runs
    return n
