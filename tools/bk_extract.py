"""Generic XHTML (KindleUnpack output) -> item stream for single trade books (巴菲特致股东的信、财富贫穷与政治、工作消费主义和新穷人、股票大作手回忆录).

Item: dict(k, tag, cls, id, runs, ...)
    k = 'h'      heading (lvl 1-6, runs; 'orn' images inside a heading become a following 'img' item)
        'p'      paragraph; q=1 inside a <blockquote>, box=1 inside a bordered box
        'note'   note entry (endnote / footnote paragraph, its first run is the back-link marker)
        'img'    stand-alone image (src, fig=1 when it sits in a chart/figure container)
        'table'  text table (rows = [[runs, ...], ...], head = number of header rows)
        'li'     list item
The four books use different markup (h1/h2, p.fnote, div.fnote, aside, blockquote, div.roundsolid ...): everything is
flattened here, the meaning of the classes is decided per book in bk.py.
"""
import os
import re
from lxml import etree
from .model import run, merge_runs, collapse_ws, BR, OBJ
from .extract import ln, anchor_key, resolve_href, load_body, clean_runs
from .bk_fixes import SPECIAL as BF_SPECIAL

MARK_RE = re.compile(r'^[\[［(（〔]\s*\d+\s*[\]］)）〕]$|^\d{1,3}$|^[註注]\d{1,4}$')
NOTE_CLS = ('fnote', 'note1')
BLOCK = ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'ul', 'ol', 'li', 'blockquote', 'section', 'aside', 'img')                       # paragraph classes that are note entries
ITALIC_CLS = ('italic', 'kindle-cn-italic')
KAI_CLS = ('kaiti', 'kindle-cn-kai')
BOLD_CLS = ('kindle-cn-bold', 'bold')
SUP_CLS = ('math-super',)


_FIX = None
FIX_USED = {}
_SPAN_ID = None


def _fixes(part):
    """Corrections (bk_fixes) of this book that apply to `part`; the book is the scratch directory (q11 ...)."""
    global _FIX, _SPAN_ID
    if _FIX is None:
        from . import bk_fixes
        key = os.path.basename(os.environ.get('BOOK_SCRATCH', '').rstrip('/'))
        _FIX = bk_fixes.FIXES.get(key, [])
        _SPAN_ID = bk_fixes.SPAN_ANCHORS.get(key)
    n = int(part[4:]) if part.startswith('part') and part[4:].isdigit() else None
    return [f for f in _FIX if f[0] == '*' or f[0] == n or isinstance(f[0], (tuple, range)) and n in f[0]]


def fix_runs(runs, fixes):
    """Apply text corrections to one paragraph; a literal may run across runs (the result keeps the first run's format)."""
    for f in fixes:
        old, new = f[1], f[2]
        start = 0
        while True:
            text = ''.join('\0' if r.get('i') else r['t'] for r in runs)
            if isinstance(old, str):
                i = text.find(old, start)
                if i < 0:
                    break
                j, rep = i + len(old), new
            else:
                m = old.search(text, start)
                if not m or m.start() == m.end():
                    break
                i, j, rep = m.start(), m.end(), m.expand(new)
            FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
            start = i + len(rep)
            pos, out, done = 0, [], False
            for r in runs:
                L = 1 if r.get('i') else len(r['t'])
                a, b = pos, pos + L
                pos = b
                if b <= i or a >= j:
                    out.append(r)
                    continue
                if r.get('i'):
                    continue                                     # an inline image inside the replaced text
                head = r['t'][:max(0, i - a)]
                tail = r['t'][j - a:] if b > j else ''
                if not done:
                    out.append(dict(r, t=head + rep + tail))
                    done = True
                elif tail:
                    out.append(dict(r, t=tail))
            if not done:                                         # (only images were replaced)
                out.insert(next((k for k, r in enumerate(out) if sum(1 if x.get('i') else len(x['t']) for x in out[:k]) >= i), len(out)), run(rep))
            runs = [r for r in out if r.get('i') or r['t'] != '']
    return runs


def _txt(it):
    return ''.join(r['t'] for r in it.get('runs', []) if not r.get('i'))


def _mark_fix(f, out):
    """Note marks the ebook got wrong:
        (part, 'RELINK', paragraph prefix, mark text, new text, href, anchor)   a mark that links to the wrong note
        (part, 'ADDMARK', paragraph prefix, text after which, new text, href, anchor)   a missing mark
        (part, 'NOTEBACK', note mark text, back-link href)   a note entry whose back-link is broken"""
    kind = f[1]
    if kind in ('HREF', 'ANCHOR'):                            # (part, 'HREF', paragraph prefix, link text, new href) / (part, 'ANCHOR', paragraph prefix, anchor)
        for it in out:
            if it['k'] != 'note' and _txt(it).startswith(f[2]) and it.get('runs'):
                if kind == 'ANCHOR':
                    if not it['runs'][0].get('a'):
                        it['runs'][0] = dict(it['runs'][0], a=f[3])
                        FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
                    return
                for k, r in enumerate(it['runs']):
                    if r['t'] == f[3] and r.get('h'):
                        it['runs'][k] = dict(r, h=f[4])
                        FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
                        return
        return
    if kind == 'RENUM':                                         # (part, 'RENUM', delta, part of note n, note-anchor fmt, mark-anchor fmt)
        delta, where, nfmt, afmt = f[2], f[3], f[4], f[5]
        for it in out:
            if it['k'] == 'note':
                continue
            for k, r in enumerate(it.get('runs', [])):
                m = re.fullmatch(r'\[(\d+)\]', r['t']) if r.get('s') and r.get('h') else None
                if m:
                    n = int(m.group(1)) + delta
                    it['runs'][k] = dict(r, t=f'[{n}]', h=nfmt.format(part=where(n), n=n), a=afmt.format(n=n))
                    FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
        return
    if kind == 'SHIFT':                                        # (part, 'SHIFT', from n, delta): renumber '(n)' marks and note labels from n on
        for it in out:
            for k, r in enumerate(it.get('runs', [])):
                m = re.fullmatch(r'\((\d+)\)', r['t']) if r.get('h') else None
                if m and int(m.group(1)) >= f[2]:
                    it['runs'][k] = dict(r, t='(%d)' % (int(m.group(1)) + f[3]))
                    FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
        return
    if kind == 'SPLIT':                                        # (part, 'SPLIT', paragraph prefix, split text, label, back-link href, anchor): a note the ebook ran into the previous one
        for i, it in enumerate(out):
            if not _txt(it).startswith(f[2]):
                continue
            for k, r in enumerate(it['runs']):
                j = r['t'].find(f[3])
                if j >= 0:
                    head = it['runs'][:k] + ([dict(r, t=r['t'][:j].rstrip())] if r['t'][:j].strip() else [])
                    tail = [dict(t=f[4], h=f[5], a=f[6]), dict(r, t=r['t'][j + len(f[3]):])] + it['runs'][k + 1:]
                    out[i:i + 1] = [dict(it, runs=head), dict(it, runs=[x for x in tail if x['t']])]
                    FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
                    return
        return
    if kind == 'PGNO':                                         # (part, 'PGNO', text + page number): a printed page number the ebook ran into the text
        for it in out:
            for k, r in enumerate(it.get('runs', [])):
                if r['t'].endswith(f[2]) and not r.get('c'):
                    m = re.search(r'([ivxlc]+|\d+)$', f[2])
                    head = dict(r, t=r['t'][:-len(m.group(1))])
                    it['runs'][k:k + 1] = [head, dict(t='〔%s〕' % m.group(1), c='pgno')]
                    FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
                    return
        return
    if kind == 'NOTEBACK':
        for it in out:
            if it['k'] == 'note' and it['runs'] and it['runs'][0]['t'] == f[2]:
                it['runs'][0] = dict(it['runs'][0], h=f[3])
                FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
                return
        return
    paras = [it for it in out if it['k'] != 'note' and _txt(it).startswith(f[2])]
    if len(paras) != 1:
        return
    it = paras[0]
    mark = dict(t=f[4], s=1, h=f[5], a=f[6])
    if kind == 'RELINK':
        for k, r in enumerate(it['runs']):
            if r.get('s') and r['t'] == f[3]:
                it['runs'][k] = dict(r, **mark)
                FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
                return
        return
    pos = 0
    for k, r in enumerate(it['runs']):                       # ADDMARK: split the run that holds the anchor text
        j = r['t'].find(f[3]) if not r.get('i') else -1
        if j >= 0:
            j += len(f[3])
            head, tail = dict(r, t=r['t'][:j]), dict(r, t=r['t'][j:])
            it['runs'][k:k + 1] = [x for x in (head, mark, tail) if x is mark or x['t']]
            FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
            return


def _apply_fixes(part, out):
    fx = _fixes(part)
    if not fx:
        return out
    for f in [f for f in fx if f[1] == 'MOVE']:                 # (part, 'MOVE', text of the item, text of the item it goes before)
        src = [k for k, it in enumerate(out) if _txt(it).startswith(f[2])]
        if len(src) == 1:
            it = out.pop(src[0])
            dst = [k for k, x in enumerate(out) if _txt(x).startswith(f[3])]
            if len(dst) == 1:
                out.insert(dst[0], it)
                FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
            else:
                out.insert(src[0], it)
    for f in [f for f in fx if f[1] in ('RENUM', 'SHIFT', 'SPLIT', 'PGNO', 'RELINK', 'ADDMARK', 'NOTEBACK', 'HREF', 'ANCHOR')]:
        _mark_fix(f, out)
    for f in [f for f in fx if f[1] == 'HEAD']:                 # (part, 'HEAD', paragraph prefix, level): a heading the ebook set as text
        for k, it in enumerate(out):
            if it['k'] == 'p' and _txt(it).startswith(f[2]):
                out[k] = dict(it, k='h', lvl=f[3], runs=[dict(r, b=0) for r in it['runs']])
                FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
                break
    fx = [f for f in fx if f[1] not in BF_SPECIAL]
    for it in out:
        if it.get('runs'):
            it['runs'] = fix_runs(it['runs'], fx)
        if it.get('rows'):
            it['rows'] = [[fix_runs(c, fx) for c in row] for row in it['rows']]
    return out


def _cls(c, add):
    if not c:
        return add
    return c if add in c.split() else c + ' ' + add


def inline(el, part, mark_breaks=False):
    out = []
    pending = [None]

    def emit(t, b, c, h, a, s=0):
        if not t:
            return
        if pending[0] and not a:
            a = pending[0]
            pending[0] = None
        if mark_breaks:
            t = re.sub(r'[ \t]*\n[ \t\r\n]*|[ \t]{2,}', ' ', t)
        out.append(run(collapse_ws(t), b, s, h, a, c=c))

    def rec(n, b, c, h, a, s=0):
        emit(n.text, b, c, h, a, s)
        for ch in n:
            if not isinstance(ch.tag, str):
                emit(ch.tail, b, c, h, a, s)
                continue
            t = ln(ch)
            cls = (ch.get('class') or '').split()
            if t == 'br':
                if mark_breaks:
                    out.append(run(' '))
                else:
                    out.append(run(BR))
            elif t in ('b', 'strong'):
                rec(ch, 1, c, h, a, s)
            elif t in ('i', 'em', 'cite'):
                rec(ch, b, _cls(c, 'it'), h, a, s)
            elif t == 'img':
                out.append(run(OBJ, b, 0, h, a, i=os.path.basename(ch.get('src') or ''), c=ch.get('class') or ''))
            elif t == 'a' and 'duokan-footnote' in cls and not ''.join(ch.itertext()).strip():
                m = re.search(r'(\d+)$', ch.get('id') or '')
                if m and ch.get('href'):                          # an icon (image) as the note mark: the number comes from the id
                    out.append(run(m.group(1), b, 1, resolve_href(part, ch.get('href')), anchor_key(part, ch.get('id')), c=c))
            elif t == 'a':
                if ch.get('href'):
                    href = resolve_href(part, ch.get('href'))
                    aid = anchor_key(part, ch.get('id')) if ch.get('id') else a
                    rec(ch, b, c, href or h, aid, s)
                elif ch.get('id'):
                    aid = anchor_key(part, ch.get('id'))
                    if len(ch) == 0 and not (ch.text or '').strip():
                        pending[0] = aid
                    else:
                        rec(ch, b, c, h, aid, s)
                else:
                    rec(ch, b, c, h, a, s)
            elif t == 'sup':
                txt = ''.join(ch.itertext()).strip()
                if not txt and any(ln(x) == 'a' and 'duokan-footnote' in (x.get('class') or '') for x in ch.iter() if isinstance(x.tag, str)):
                    rec(ch, b, c, h, a, 1)
                elif MARK_RE.match(txt) or h:
                    rec(ch, b, c, h, a, 1)
                elif txt:
                    rec(ch, b, _cls(c, 'msup'), h, a, s)
            elif t == 'sub':
                rec(ch, b, _cls(c, 'msub'), h, a, s)
            elif set(cls) & set(SUP_CLS):
                rec(ch, b, c, h, a, 1)
            elif set(cls) & set(ITALIC_CLS):
                rec(ch, b, _cls(c, 'it'), h, a, s)
            elif set(cls) & set(KAI_CLS):
                rec(ch, b, _cls(c, 'kai'), h, a, s)
            elif set(cls) & set(BOLD_CLS):
                rec(ch, 1, c, h, a, s)
            elif ch.get('id') and _SPAN_ID and re.match(_SPAN_ID, ch.get('id')):
                aid = anchor_key(part, ch.get('id'))                # (a book whose cross-references target <span id=…>)
                if not ''.join(ch.itertext()).strip():
                    pending[0] = aid
                else:
                    rec(ch, b, c, h, a or aid, s)
            elif ch.get('id') and not a and any(isinstance(x.tag, str) and ln(x) == 'a' and x.get('href') for x in ch.iter() if x is not ch):
                rec(ch, b, c, h, anchor_key(part, ch.get('id')), s)     # <span id=…><a href=…>註9</a></span>: the id is the mark's anchor
            else:
                rec(ch, b, c, h, a, s)
            emit(ch.tail, b, c, h, a, s)

    rec(el, 0, '', '', '')
    return merge_runs(out)


def plain(el):
    return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()


def _imgs(el):
    return [c for c in el.iter() if isinstance(c.tag, str) and ln(c) == 'img']


def items(part):
    _fixes(part)
    body = load_body(part)
    out = []

    def add(k, el, **kw):
        cls = el.get('class') or ''
        it = dict(k=k, tag=ln(el), cls=cls, id=anchor_key(part, el.get('id')) if el.get('id') else '', **kw)
        out.append(it)
        return it

    def walk(nodes, q=0, box=0, fig=0, note=0):
        for el in nodes:
            if not isinstance(el.tag, str):
                continue
            t = ln(el)
            cls = (el.get('class') or '').split()
            if t in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                imgs = _imgs(el)
                runs = clean_runs([r for r in inline(el, part, mark_breaks=True) if not r.get('i')])
                if runs:
                    add('h', el, runs=runs, lvl=int(t[1]))
                for im in imgs:
                    add('img', el, src=os.path.basename(im.get('src') or ''), runs=[], orn=1)
            elif t == 'p':
                imgs = _imgs(el)
                txt = plain(el)
                if imgs and not txt:
                    for im in imgs:
                        add('img', el, src=os.path.basename(im.get('src') or ''), runs=[], fig=fig)
                    continue
                runs = clean_runs(inline(el, part))
                if not runs:
                    if 'konghang' in cls or 'empty' in cls:
                        add('p', el, runs=[], q=q, box=box, blank=1)
                    continue
                if note and runs and not runs[0].get('h') and not runs[0].get('a') and runs[0]['t'].strip('\u3000 ') == '' and len(runs) > 1:
                    runs = runs[1:]                                   # the ebook indents a note entry with ideographic spaces before its number
                add('note' if (note or set(cls) & set(NOTE_CLS)) else 'p', el, runs=runs, q=q, box=box)
            elif t == 'blockquote':
                walk(el, q=1, box=box, fig=fig, note=note)
            elif t == 'aside':
                if not any(ln(x) == 'p' for x in el.iter() if isinstance(x.tag, str)):
                    continue
                walk(el, q=q, box=box, fig=fig, note=1)
            elif t in ('div', 'section', 'body'):
                if any(c.startswith(('kindle-cn-toc', 'sgc-toc')) for c in cls):
                    continue
                if t == 'div' and plain(el) and not any(isinstance(x.tag, str) and ln(x) in BLOCK for x in el.iter() if x is not el):
                    runs = clean_runs(inline(el, part))             # a div that holds text directly (a note entry: <a>[n]</a>text)
                    if runs:
                        add('note' if (note or 'fnote' in cls) else 'p', el, runs=runs, q=q, box=box)
                    continue
                start = len(out)
                walk(el, q=q, box=1 if ('roundsolid' in cls or 'kx' in cls) else box, fig=1 if 'chatu' in cls else fig,
                     note=1 if ('fnote' in cls or 'annotation' in cls or '_idFootnote' in cls) else note)
                if '_idFootnote' in cls and el.get('id') and len(out) > start and out[start].get('runs') and not out[start]['runs'][0].get('a'):
                    out[start]['runs'][0] = dict(out[start]['runs'][0], a=anchor_key(part, el.get('id')))   # the entry's id sits on its <div>
            elif t in ('ul', 'ol') and 'duokan-footnote-content' in cls:
                for li in el:
                    if not (isinstance(li.tag, str) and ln(li) == 'li' and li.get('id')):
                        continue
                    m = re.search(r'(\d+)$', li.get('id'))
                    back = next((resolve_href(part, a.get('href')) for a in li.iter() if isinstance(a.tag, str) and ln(a) == 'a' and a.get('href')), '')
                    if '_end_' in li.get('id'):                        # (one entry of the ebook links to a non-existent anchor: derive the mark's id)
                        back = anchor_key(part, li.get('id').replace('_end_', '_start_'))
                    runs = clean_runs([dict(r, h='', a='') for r in inline(li, part)])
                    if runs and m:                                # the whole entry is one back-link in the ebook: marker = back-link, text plain
                        add('note', li, runs=[run(m.group(1), 0, 0, back, anchor_key(part, li.get('id')))] + runs, q=0, box=0)
            elif t in ('ul', 'ol'):
                if 'Level-1' in cls:
                    continue
                for li in el:
                    if isinstance(li.tag, str) and ln(li) == 'li':
                        runs = clean_runs(inline(li, part))
                        if runs:
                            add('li', li, runs=runs)
            elif t == 'table':
                rows = []
                for tr in el.iter():
                    if isinstance(tr.tag, str) and ln(tr) == 'tr':
                        cells = [clean_runs(inline(td, part)) for td in tr if isinstance(td.tag, str) and ln(td) in ('td', 'th')]
                        rows.append(cells)
                add('table', el, rows=rows, runs=[])
            elif t == 'img':
                add('img', el, src=os.path.basename(el.get('src') or ''), runs=[], fig=fig)
            elif t in ('hr', 'nav', 'svg', 'br'):
                continue
            else:
                runs = clean_runs(inline(el, part))
                if runs:
                    add('p', el, runs=runs, q=q, box=box)

    walk(body)
    return _apply_fixes(part, out)
