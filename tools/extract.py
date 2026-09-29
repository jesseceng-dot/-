"""XHTML (unpacked from the AZW3) -> normalized blocks.  Generic rules first; book-specific fixes live in normalize.py."""
import re
import os
from lxml import etree
from .model import run, merge_runs, collapse_ws, BR, OBJ

TEXT_DIR = os.path.join(os.environ.get('BOOK_SCRATCH',
                        '/tmp/claude-0/-home-user--/243b6d09-d8f0-55ab-9830-1d98f5b584ee/scratchpad'),
                        'unpack/x/mobi8/OEBPS/Text')
XHTML = '{http://www.w3.org/1999/xhtml}'


def ln(e):
    return etree.QName(e).localname


def anchor_key(part, frag):
    return f'{part}#{frag}' if frag else part


def resolve_href(part, href):
    """'part0018.xhtml#bz3' -> 'part0018#bz3'"""
    if not href:
        return ''
    if href.startswith('http'):
        return href
    f, _, frag = href.partition('#')
    f = os.path.basename(f)[:-6] if f.endswith('.xhtml') else part
    return anchor_key(f, frag)


def inline_runs(el, part, b=0, s=0):
    """Runs for the content of element el (its text, children, tails)."""
    out = []

    def add_text(t, b, s, h='', a=''):
        if t:
            out.append(run(collapse_ws(t), b, s, h, a))

    def rec(n, b, s, h='', a=''):
        add_text(n.text, b, s, h, a)
        for c in n:
            if not isinstance(c.tag, str):
                add_text(c.tail, b, s, h, a)
                continue
            t = ln(c)
            if t == 'br':
                out.append(run(BR))
            elif t == 'b' or t == 'strong':
                rec(c, 1, s, h, a)
            elif t == 'img':
                out.append(run(OBJ, b, s, h, a, i=os.path.basename(c.get('src') or '')))
            elif t == 'a':
                href = resolve_href(part, c.get('href'))
                aid = anchor_key(part, c.get('id')) if c.get('id') else a
                rec(c, b, s, href or h, aid)
            elif t == 'span':
                cls = c.get('class') or ''
                rec(c, b, 1 if 'math-super' in cls else s, h, a)
            elif t == 'sup':
                rec(c, b, 1, h, a)
            else:
                rec(c, b, s, h, a)
            add_text(c.tail, b, s, h, a)

    rec(el, b, s)
    return out


def clean_runs(runs):
    """Trim leading/trailing spaces and trailing forced breaks; drop empty runs."""
    runs = [r for r in runs if r['t'] != '']
    while runs and runs[-1]['t'] == BR:
        runs.pop()
    while runs and runs[0]['t'] == BR:
        runs.pop(0)
    if runs:
        runs[0] = dict(runs[0], t=runs[0]['t'].lstrip(' '))
        runs[-1] = dict(runs[-1], t=runs[-1]['t'].rstrip(' '))
    return merge_runs(runs)


def load_body(part):
    path = os.path.join(TEXT_DIR, part + '.xhtml')
    t = etree.parse(path, etree.XMLParser(recover=True, huge_tree=True))
    return t.getroot().find('.//' + XHTML + 'body')


HEAD_LEVEL = {'h1': 'h1', 'h2': 'h1', 'h3': 'h2', 'h4': 'h3', 'h5': 'h4', 'h6': 'h5'}
CLASS_STYLE = {
    'bodycontent-text': 'body',
    'bodycontent-text_yinwen': 'quote',
    'bodycontent-text_yinwen1': 'quote',
    'bodycontent-text_noindent': 'noindent',
    'bodycontent-text_right': 'right',
    'bodycontent-text_center': 'center',
    'bodycontent-text_center-1': 'center',
    'bodycontent-text-bold': 'noindent',
    'zhusi': 'note',
}


def parse_part(part):
    """Generic conversion: list of blocks (dicts) in document order."""
    body = load_body(part)
    blocks = []
    for el in body:
        if not isinstance(el.tag, str):
            continue
        t = ln(el)
        cls = (el.get('class') or '').split()
        eid = anchor_key(part, el.get('id')) if el.get('id') else ''
        if t in HEAD_LEVEL:
            runs = clean_runs(inline_runs(el, part))
            if runs:
                blocks.append(dict(k='h', style=HEAD_LEVEL[t], runs=runs, id=eid, src=f'{t}.{" ".join(cls)}'))
        elif t == 'p':
            runs = clean_runs(inline_runs(el, part))
            if not runs:
                continue
            st = 'body'
            for c in cls:
                if c in CLASS_STYLE:
                    st = CLASS_STYLE[c]
            txt = ''.join(r['t'] for r in runs)
            if st == 'center' and re.fullmatch(r'§\s*\d+', txt):
                st = 'secnum'
            blocks.append(dict(k='p', style=st, runs=runs, id=eid, src=f'p.{" ".join(cls)}'))
        # div / svg / images / toc handled by book-specific code
    return blocks
