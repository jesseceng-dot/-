"""《杜威著作精选11种》AZW3（KindleUnpack 输出的 XHTML）-> 逐部件的“条目”列表。

条目（item）与 kant_extract 相同：
    k    'h'（标题标签 h1–h4）| 'p'（段落）| 'note'（注释）| 'img'（独立插图）
    tag / cls   原 XHTML 标签与 class（每册规则据此判断样式）
    runs        行内 run 列表（见 model.py），文本尚未清理
    id          块级锚点（部件#id）
本书的标记很规整：标题是 h1–h4，注释是 p.note（页内 [n] 角标与注释互相链接），斜体是 <i>，着重（原书斜体，中译本处理为楷体）
是 span.kaiti，图是 p.center 里的 <img>，图注是紧随其后的 p.img。
"""
import os
import re
from lxml import etree
from .model import run, merge_runs, collapse_ws, BR, OBJ
from .extract import ln, anchor_key, resolve_href, load_body, clean_runs

MARK_RE = re.compile(r'^[\[［]\s*\d+\s*[\]］]$')


def _cls(c, add):
    """Combine run classes ('it', 'kai', 'msup', ...)."""
    if not c:
        return add
    if add in c.split():
        return c
    return c + ' ' + add


def inline(el, part, mark_breaks=False):
    """Runs for the content of `el`: <b> -> bold, <i> -> class 'it', span.kaiti -> class 'kai', <sup>/<sub> -> 'msup'/'msub'
    (note markers stay superscript + linked), empty <a id> anchors become the anchor of the next run."""
    out = []
    pending = [None]

    def emit(t, b, c, h, a):
        if not t:
            return
        if pending[0] and not a:
            a = pending[0]
            pending[0] = None
        if mark_breaks:
            t = re.sub(r'[ \t]*\n[ \t\r\n]*|[ \t]{2,}', ' ', t)
        out.append(run(collapse_ws(t), b, 0, h, a, c=c))

    def rec(n, b, c, h, a):
        emit(n.text, b, c, h, a)
        for ch in n:
            if not isinstance(ch.tag, str):
                emit(ch.tail, b, c, h, a)
                continue
            t = ln(ch)
            cls = (ch.get('class') or '').split()
            if t == 'br':
                if mark_breaks:
                    emit('\n', b, c, h, a)
                    out[-1]['t'] = ' '
                else:
                    out.append(run(BR))
            elif t in ('b', 'strong'):
                rec(ch, 1, c, h, a)
            elif t in ('i', 'em'):
                rec(ch, b, _cls(c, 'it'), h, a)
            elif t == 'img':
                out.append(run(OBJ, b, 0, h, a, i=os.path.basename(ch.get('src') or ''), c=ch.get('class') or ''))
            elif t == 'a':
                if ch.get('href'):
                    href = resolve_href(part, ch.get('href'))
                    aid = anchor_key(part, ch.get('id')) if ch.get('id') else a
                    rec(ch, b, c, href or h, aid)
                elif ch.get('id'):
                    aid = anchor_key(part, ch.get('id'))
                    if len(ch) == 0 and not (ch.text or '').strip():
                        pending[0] = aid
                    else:
                        rec(ch, b, c, h, aid)
                else:
                    rec(ch, b, c, h, a)
            elif t == 'sup':
                txt = ''.join(ch.itertext()).strip()
                if MARK_RE.match(txt) or h:
                    rec(ch, b, c, h, a)             # note marker: superscript, blue, linked (marked in dewey.mark_markers)
                elif txt:
                    rec(ch, b, _cls(c, 'msup'), h, a)
            elif t == 'sub':
                rec(ch, b, _cls(c, 'msub'), h, a)
            elif 'kaiti' in cls:
                rec(ch, b, _cls(c, 'kai'), h, a)
            else:
                rec(ch, b, c, h, a)
            emit(ch.tail, b, c, h, a)

    rec(el, 0, '', '', '')
    res = []
    for r in out:
        if r['t'] and MARK_RE.match(r['t'].strip()) and (r.get('h') or r.get('a')) and not r.get('c'):
            r = dict(r, s=1)
        res.append(r)
    return merge_runs(res)


def plain(el):
    return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()


def items(part):
    """Flat item list of one part file."""
    body = load_body(part)
    out = []

    def add(k, el, **kw):
        cls = el.get('class') or ''
        it = dict(k=k, tag=ln(el), cls=cls, id=anchor_key(part, el.get('id')) if el.get('id') else '', **kw)
        out.append(it)
        return it

    for el in body:
        if not isinstance(el.tag, str):
            continue
        t = ln(el)
        cls = (el.get('class') or '').split()
        if t in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            runs = clean_runs(inline(el, part, mark_breaks=True))
            if runs:
                add('h', el, runs=runs, lvl=int(t[1]))
        elif t == 'p':
            imgs = [c for c in el.iter() if isinstance(c.tag, str) and ln(c) == 'img']
            txt = plain(el)
            if imgs and not txt and not any('inline' in (i.get('class') or '') for i in imgs):
                for im in imgs:
                    add('img', el, src=os.path.basename(im.get('src') or ''), runs=[])
                continue
            runs = clean_runs(inline(el, part))
            if not runs:
                continue
            add('note' if 'note' in cls else 'p', el, runs=runs)
        elif t in ('hr', 'ul', 'ol', 'nav', 'svg'):
            continue
        elif t == 'div':
            if any(c.startswith('kindle-cn-toc') for c in cls):
                continue
            runs = clean_runs(inline(el, part))
            if runs:
                add('p', el, runs=runs)
        else:
            runs = clean_runs(inline(el, part))
            if runs:
                add('p', el, runs=runs)
    return out
