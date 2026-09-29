"""Content model: paragraphs are lists of runs; a run is a small dict.

    {"t": text, "b": 1 (bold), "s": 1 (superscript), "h": link target id, "a": anchor id, "i": inline image}

Text offsets ("units") count code points; a forced line break is a run with t == "\\n" (one unit),
an inline image is a run with an "i" key and t == "\\ufffc" (one unit).
"""
import html as _html
import re
from .style import LINK_BASE

BR = '\n'
OBJ = '￼'


def run(t, b=0, s=0, h='', a='', i='', c=''):
    r = {'t': t}
    if b: r['b'] = 1
    if s: r['s'] = 1
    if h: r['h'] = h
    if a: r['a'] = a
    if i: r['i'] = i
    if c: r['c'] = c
    return r


def runs_text(runs):
    return ''.join(r['t'] for r in runs)


def runs_len(runs):
    return sum(len(r['t']) for r in runs)


def _wrap(r, inner):
    if r.get('c'):
        inner = f'<span class="{r["c"]}">{inner}</span>'
    if r.get('b'):
        inner = f'<b>{inner}</b>'
    if r.get('s'):
        inner = f'<span class="sup">{inner}</span>'
    if r.get('h'):
        inner = f'<a href="{LINK_BASE}{_html.escape(r["h"])}">{inner}</a>'
    return inner


def runs_html(runs, start=0, end=None, strip=True, final=False):
    """HTML for units [start, end) of a run list."""
    out = []
    pos = 0
    total = runs_len(runs)
    if end is None:
        end = total
    for r in runs:
        t = r['t']
        n = len(t)
        lo, hi = max(start, pos), min(end, pos + n)
        if lo < hi:
            seg = t[lo - pos:hi - pos]
            out.append((r, seg))
        pos += n
        if pos >= end:
            break
    if strip and out:
        # drop leading / trailing plain spaces at line boundaries (they collapse in the browser anyway)
        r0, s0 = out[0]
        s0 = s0.lstrip(' ')
        out[0] = (r0, s0)
        r1, s1 = out[-1]
        s1 = s1.rstrip(' ')
        out[-1] = (r1, s1)
    if final and out:
        # soft hyphens: a visible hyphen where the line ends, invisible elsewhere (each line is set on its own)
        fixed = []
        for k, (r, seg) in enumerate(out):
            last = k == len(out) - 1
            if seg.endswith('\u00ad') and last:
                seg = seg[:-1] + '-'
            seg = seg.replace('\u00ad', '')
            fixed.append((r, seg))
        out = fixed
    parts = []
    for r, seg in out:
        if not seg:
            continue
        if seg == BR:
            parts.append('<br>')
        elif r.get('i'):
            parts.append(_wrap(r, f'<img class="inl" src="{_html.escape(r["i"])}">'))
        else:
            parts.append(_wrap(r, _html.escape(seg, quote=False)))
    return ''.join(parts)


def collapse_ws(s):
    """Collapse ASCII whitespace but keep ideographic spaces (U+3000) and NBSP untouched."""
    return re.sub(r'[ \t\r\n\f]+', ' ', s)


def merge_runs(runs):
    """Merge adjacent runs with identical attributes."""
    out = []
    for r in runs:
        if not r['t']:
            continue
        if out and {k: v for k, v in out[-1].items() if k != 't'} == {k: v for k, v in r.items() if k != 't'} \
                and r['t'] != BR and out[-1]['t'] != BR and not r.get('i'):
            out[-1] = dict(out[-1], t=out[-1]['t'] + r['t'])
        else:
            out.append(dict(r))
    return out
