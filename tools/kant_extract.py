"""《康德文集（注释版）》AZW3（KindleUnpack 输出的 XHTML）-> 逐部件的“条目”列表。

条目（item）是一个 dict：
    k    'h'（标题标签 h1–h6）| 'p'（段落）| 'note'（注释）| 'img'（独立插图）| 'hr'
    tag / cls   原 XHTML 标签与 class（供每册规则判断层级和样式）
    runs        行内 run 列表（见 model.py），文本尚未清理
    id          块级锚点（部件#id）
第 1 册（三大批判）与第 2–10 册的 XHTML 写法不同（前者用 div.tocenter / div.note / (N) 角标，后者用 p.class 和 [N] 角标），
这里把两种写法统一成同一种条目流；语义判断（哪些短行是标题、哪一级）留给 kant.py。
"""
import os
import re
from lxml import etree
from .model import run, merge_runs, collapse_ws, BR, OBJ
from .extract import ln, anchor_key, resolve_href, load_body, clean_runs, TEXT_DIR      # noqa: F401  (re-exported)

MARK_RE = re.compile(r'^[\[［(（]\s*\d+\s*[\]］)）]$')
BOLD_CLS = ('bold', 'bold1', 'tostrong')
EMPH_CLS = ('emphasis-filled-dot', 'o')
SUB_CLS = ('math-sub',)
SHORT_MARK = {'ch', 'ck', 'bold', 'jz', 'juzhong', 'center', 'centerr', 'center1', 'cuti', 'z1', 'z22', 'z3', 'h7', 'h8',
              'yinwen-c', 'yinwen-c2', 'tuzhu-center', 'tuzhu-left', 'yinwen1', 'yinwen0'}
SUP_CLS = ('math-super', 'math-super-italic', 'noteSuper')


def inline(el, part, mark_breaks=False):
    """Runs for the content of `el`.  Note markers keep their link (h) and anchor (a); math superscripts are
    class 'msup', subscripts 'msub', emphasis-dot spans 'emp'."""
    out = []
    pending = [None]

    def emit(t, b, c, h, a):
        if not t:
            return
        if pending[0] and not a:
            a = pending[0]
            pending[0] = None
        if mark_breaks:
            t = re.sub(r'[ \t]*\n[ \t\r\n]*|[ \t]{2,}', '\u2028', t)     # a hard line break inside a heading of the source
        out.append(run(collapse_ws(t), b, 0, h, a, c=c))

    def rec(n, b, c, h, a, insup):
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
                    out[-1]['t'] = '\u2028'
                else:
                    out.append(run(BR))
            elif t in ('b', 'strong'):
                rec(ch, 1, c, h, a, insup)
            elif t == 'img':
                out.append(run(OBJ, b, 0, h, a, i=os.path.basename(ch.get('src') or ''), c=ch.get('class') or ''))
            elif t == 'a':
                if ch.get('href'):
                    href = resolve_href(part, ch.get('href'))
                    aid = anchor_key(part, ch.get('id')) if ch.get('id') else a
                    rec(ch, b, c, href or h, aid, insup)
                else:
                    if ch.get('id') and not re.match(r'^page\d+$', ch.get('id')):
                        aid = anchor_key(part, ch.get('id'))
                        if len(ch) == 0 and not (ch.text or '').strip():
                            pending[0] = aid
                        else:
                            rec(ch, b, c, h, aid, insup)
                    else:
                        rec(ch, b, c, h, a, insup)
            elif t == 'sup' or set(cls) & set(SUP_CLS):
                txt = ''.join(ch.itertext()).strip()
                if MARK_RE.match(txt) or h:
                    rec(ch, b, c, h, a, True)          # note marker: superscript, blue, linked (marked in normalize)
                elif txt:
                    rec(ch, b, 'msup', h, a, True)
                else:
                    pass
            elif set(cls) & set(SUB_CLS):
                rec(ch, b, 'msub', h, a, insup)
            elif set(cls) & set(EMPH_CLS):
                rec(ch, b, 'emp', h, a, insup)
            elif set(cls) & set(BOLD_CLS):
                rec(ch, 1, c, h, a, insup)
            else:
                rec(ch, b, c, h, a, insup)
            emit(ch.tail, b, c, h, a)

    rec(el, 0, '', '', '', False)
    # marker runs: text is '[N]' / '(N)' inside a sup -> flag as superscript
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

    def walk(nodes, align=None, in_note=False):
        for el in nodes:
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
                runs = clean_runs(inline(el, part))
                if imgs and not txt and 'zaozi' not in ''.join(i.get('class') or '' for i in imgs):
                    for im in imgs:
                        add('img', el, src=os.path.basename(im.get('src') or ''), runs=[])
                    continue
                if not runs:
                    continue
                k = 'note' if in_note or 'noteContent' in cls or 'noteContent-r' in cls or 'noteTitle' in cls else 'p'
                it = add(k, el, runs=runs)
                if align:
                    it['align'] = align
            elif t == 'div':
                if 'note' in cls:
                    walk(el, in_note=True)
                elif set(cls) & {'tocenter', 'toleft', 'toright'}:
                    walk(el, align={'tocenter': 'center', 'toleft': 'left', 'toright': 'right'}[[c for c in cls if c.startswith('to')][0]],
                         in_note=in_note)
                elif set(cls) & {'title_pic', 'title_table', 'note_pic', 'note_table'}:
                    txt = plain(el)
                    if txt:
                        add('p', el, runs=clean_runs(inline(el, part)), align='center', cap=1)
                elif 'img-center' in cls or 'pic' in cls or 'pic_table' in cls:
                    imgs = [c for c in el.iter() if isinstance(c.tag, str) and ln(c) == 'img']
                    for im in imgs:
                        add('img', el, src=os.path.basename(im.get('src') or ''), runs=[])
                    txt = plain(el)
                    if txt:
                        # a caption written inside the picture div ('图1'); the image itself is a separate item
                        cr = [r for r in clean_runs(inline(el, part)) if not r.get('i')]
                        cr = clean_runs(cr)
                        if cr:
                            add('p', el, runs=cr, align='center', cap=1)
                elif 'contents' in ' '.join(cls) or plain(el) == '返回总目录':
                    continue
                else:
                    if len(el) == 0 and not plain(el):
                        continue
                    walk(el, align, in_note)
            elif t in ('nav', 'ol', 'ul', 'li', 'hr', 'svg'):
                continue
            elif t == 'table':
                add('table', el, runs=[])
            else:
                runs = clean_runs(inline(el, part))
                if runs:
                    add('p', el, runs=runs)

    walk(body)
    return out
