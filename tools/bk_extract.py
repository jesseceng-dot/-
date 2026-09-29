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

MARK_RE = re.compile(r'^[\[［(（〔]\s*\d+\s*[\]］)）〕]$|^\d{1,3}$')
NOTE_CLS = ('fnote', 'note1')                       # paragraph classes that are note entries
ITALIC_CLS = ('italic', 'kindle-cn-italic')
KAI_CLS = ('kaiti', 'kindle-cn-kai')
BOLD_CLS = ('kindle-cn-bold', 'bold')
SUP_CLS = ('math-super',)


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
                walk(el, q=q, box=1 if 'roundsolid' in cls else box, fig=1 if 'chatu' in cls else fig,
                     note=1 if ('fnote' in cls or 'annotation' in cls) else note)
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
    return out
