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
import copy
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
_BACK_WORDS = re.compile(r'\s*(?:↩\s*)?返回正文\s*')            # the words of a note's link back to its mark


_FIX = None
FIX_USED = {}
_SPAN_ID = None

# Span classes of one book -> (bold: 1 / 0 = inherit, run classes added); key = the book's scratch directory.
RUN_CLS = {
    'q16': {                                                    # 哥德尔、艾舍尔、巴赫
        'dialog_name': (0, 'spk'), 'dialog_name1': (0, 'spk'),          # speakers of the dialogues (细黑)
        'emphasis': (0, 'hei'), 'emphasis1': (0, 'hei'), 'heiti': (0, 'hei'),   # 黑体: the book's own emphasis ("黑体字的定理")
        'kaiti_bold': (1, 'kai'), 'quote_text2': (0, 'kai'),
        'zw': (0, 'sm'), 'zw-c': (0, 'sm'), 'zw-c1': (0, 'sm'), 'zw1': (0, 'sm'), 'code_notes2': (0, 'sm'),
        'smalltext': (0, 'sm'), 'smalltext1': (0, 'sm'), 'smalltext5': (0, 'sm'),
        'smallxht': (0, 'hei sm'), 'kaiti_smalltext': (0, 'kai sm'), 'heiti_smalltext': (0, 'hei sm'),
        'underline': (0, 'ul'), 'bg-gray': (0, 'gbox'), 'bg': (0, 'gbox'), 'duokan-western-italic': (0, 'it'),
        'normal': (0, 'nohei'), 'preface_title1': (0, ''), 'view_title_span': (0, ''), 'geb-overview-label': (0, ''),
        'ed-figure-link': (0, 'nomark lnk'),                             # links to figures ('图10', '1．'): not note marks
    },
    'q22': {'yanse': (0, 'hei')},                               # 心智社会: the ebook's coloured terms (agents' names, labels) in 黑体
    'q23': {'jiacu': (0, 'hei')},                               # 美国大城市的死与生: the ebook's bold (the author's emphasis) in 黑体
}
# Tables of one book that are set as pictures (made by tools/snap.py from the ebook's own markup): bracket images
# spanning rows, many columns, diagram-like layouts.  Key = scratch directory, value = {(part number, table index)}.
SNAP = {
    'q16': {(16, 0), (16, 2), (22, 3), (30, 0), (31, 1), (31, 4), (31, 6), (42, 1), (46, 1), (46, 2), (46, 3), (46, 5),
            (46, 7), (46, 8), (46, 10)},
}
_RUNMAP = None


def _runmap():
    global _RUNMAP
    if _RUNMAP is None:
        _RUNMAP = RUN_CLS.get(os.path.basename(os.environ.get('BOOK_SCRATCH', '').rstrip('/')), {})
    return _RUNMAP


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


def fix_tree(part, el):
    """Apply the text corrections of `part` to the text nodes of an ebook element in place (a table set as a picture,
    tools/snap.py); a correction must lie within one text node here."""
    fx = [f for f in _fixes(part) if f[1] not in BF_SPECIAL]
    for node in el.iter():
        if not isinstance(node.tag, str):
            continue
        for attr in (('text',) if node is el else ('text', 'tail')):
            s = getattr(node, attr)
            if not s:
                continue
            for f in fx:
                old, new = f[1], f[2]
                if isinstance(old, str):
                    n = s.count(old)
                    s = s.replace(old, new) if n else s
                else:
                    s, n = old.subn(lambda m: m.expand(new), s)
                if n:
                    FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + n
            setattr(node, attr, s)
    return el


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
    for f in [f for f in fx if f[1] == 'MOVETAB']:              # (part, 'MOVETAB', table title, paragraph prefix): a table with its
        src = [k for k, it in enumerate(out) if it['k'] == 'p' and _txt(it) == f[2]     # title goes after that paragraph (a float
               and k + 1 < len(out) and out[k + 1]['k'] == 'table']                    # to the top of the next page)
        if len(src) == 1:
            grp = out[src[0]:src[0] + 2]
            del out[src[0]:src[0] + 2]
            dst = [k for k, x in enumerate(out) if x['k'] == 'p' and _txt(x).startswith(f[3])]
            if len(dst) == 1:
                out[dst[0] + 1:dst[0] + 1] = grp
                FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
            else:
                out[src[0]:src[0]] = grp
    for f in [f for f in fx if f[1] in ('RENUM', 'SHIFT', 'SPLIT', 'PGNO', 'RELINK', 'ADDMARK', 'NOTEBACK', 'HREF', 'ANCHOR')]:
        _mark_fix(f, out)
    for f in [f for f in fx if f[1] == 'NOTELINK']:             # (part, 'NOTELINK', note class, note): a part whose marks '[n]' and
        have = set()                                            # note entries '[n]text' are plain text: linked both ways
        for it in out:
            r0 = it['runs'][0] if it.get('runs') else {}
            m = re.match(r'\s*\[(\d+)\]', r0.get('t', '')) if f[2] in it['cls'].split() and not (r0.get('h') or r0.get('i')) else None
            if m:
                n = m.group(1)
                have.add(n)
                it['runs'][0:1] = [x for x in (run(f'[{n}]', 0, 0, f'{part}#nl-ref{n}', f'{part}#nl-note{n}'),
                                                dict(r0, t=r0['t'][m.end():])) if x['t']]
        seen = set()
        for it in out:
            if f[2] in it['cls'].split() or it['k'] not in ('p', 'li') or not it.get('runs'):
                continue
            new = []
            for r in it['runs']:
                pos = 0
                for m in (re.finditer(r'\[(\d+)\]', r['t']) if not (r.get('h') or r.get('a') or r.get('i')) else ()):
                    n = m.group(1)
                    if n in have and n not in seen:
                        seen.add(n)
                        new += [dict(r, t=r['t'][pos:m.start()]), run(m.group(0), r.get('b', 0), 1, f'{part}#nl-note{n}', f'{part}#nl-ref{n}')]
                        pos = m.end()
                new.append(dict(r, t=r['t'][pos:]) if pos else r)
            it['runs'] = [x for x in new if x['t'] or x.get('i')]
        if have:
            FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + len(seen)
    for f in [f for f in fx if f[1] == 'CELL']:                 # (part, 'CELL', first cell of the row, column, old, new): one table cell
        done = False
        for it in out:
            for row in it.get('rows') or []:
                if row and _txt(dict(runs=row[0])).strip() == f[2] and len(row) > f[3] and f[4] in _txt(dict(runs=row[f[3]])):
                    row[f[3]] = fix_runs(row[f[3]], [(None, f[4], f[5])])
                    FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
                    done = True
                    break
            if done:
                break
    for f in [f for f in fx if f[1] == 'JOIN']:                 # (part, 'JOIN', end of a paragraph, start of the next): one paragraph the ebook broke in two
        for k in range(len(out) - 1):
            a, b = out[k], out[k + 1]
            if a['k'] == 'p' and b['k'] == 'p' and _txt(a).endswith(f[2]) and _txt(b).startswith(f[3]):
                out[k:k + 2] = [dict(a, runs=a['runs'] + b['runs'])]
                FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
                break
    for f in [f for f in fx if f[1] == 'PARA']:                 # (part, 'PARA', paragraph prefix, text that starts a new paragraph
        for k, it in enumerate(out):                            #  [, speaker label at its start, set like the dialogue speakers])
            if it['k'] != 'p' or not _txt(it).startswith(f[2]):
                continue
            pos = 0
            for j, r in enumerate(it['runs']):
                i = r['t'].find(f[3]) if not r.get('i') else -1
                if i >= 0:
                    head = it['runs'][:j] + ([dict(r, t=r['t'][:i].rstrip())] if r['t'][:i].strip() else [])
                    tail = [dict(r, t=r['t'][i:])] + it['runs'][j + 1:]
                    if len(f) == 6 and tail[0]['t'].startswith(f[4]):
                        spk = len(f[4])
                        tail[:1] = [dict(r, t=f[4], c=_cls(r.get('c'), 'spk')), dict(r, t=tail[0]['t'][spk:])]
                    out[k:k + 1] = [dict(it, runs=head), dict(it, runs=tail, id='')]
                    FIX_USED[id(f)] = FIX_USED.get(id(f), 0) + 1
                    break
            break
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
    span_pend = [None]

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
            rm = _runmap()
            if t in ('span', 'b', 'i', 'em', 'strong') and set(cls) & set(rm):
                bold, add = rm[next(x for x in cls if x in rm)]
                c2 = c
                for x in add.split():
                    c2 = _cls(c2, x)
                rec(ch, 1 if (bold or t in ('b', 'strong')) else b, _cls(c2, 'it') if t in ('i', 'em') else c2, h, a, s)
            elif t == 'br':
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
            elif t == 'svg':                                    # a formula drawn in the text itself: keyed by its <title> (its LaTeX)
                title = next((''.join(x.itertext()).strip() for x in ch if isinstance(x.tag, str) and ln(x) == 'title'), '')
                out.append(run(OBJ, b, 0, h, a, i='svg:' + title, c=ch.get('class') or ''))
            elif t == 'a' and 'duokan-footnote' in cls and not ''.join(ch.itertext()).strip():
                m = re.search(r'(\d+)$', ch.get('id') or '')
                if m and ch.get('href'):                          # an icon (image) as the note mark: the number comes from the id
                    out.append(run(m.group(1), b, 1, resolve_href(part, ch.get('href')), anchor_key(part, ch.get('id')), c=c))
            elif t == 'a':
                if ch.get('href'):
                    href = resolve_href(part, ch.get('href'))
                    aid = anchor_key(part, ch.get('id')) if ch.get('id') else a
                    c2 = c
                    for x in cls:
                        for y in (rm.get(x, (0, ''))[1] or '').split():
                            c2 = _cls(c2, y)
                    if href.startswith(('http://', 'https://')):
                        c2 = _cls(c2, 'lnk')                          # a web address: blue, as it can be clicked
                    rec(ch, b, c2, href or h, aid, s)
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
                    span_pend[0] = aid
                else:
                    rec(ch, b, c, h, a or aid, s)
            elif ch.get('id') and not a and any(isinstance(x.tag, str) and ln(x) == 'a' and x.get('href') for x in ch.iter() if x is not ch):
                rec(ch, b, c, h, anchor_key(part, ch.get('id')), s)     # <span id=…><a href=…>註9</a></span>: the id is the mark's anchor
            else:
                rec(ch, b, c, h, a, s)
            emit(ch.tail, b, c, h, a, s)

    rec(el, 0, '', '', '')
    if pending[0] and pending[0] == span_pend[0]:
        out.append(run('\u2060', a=pending[0]))                # an anchor <span id> that ends its paragraph: kept on a word joiner
    return merge_runs(out)


def _drop(x):
    """Remove an element from the tree, keeping the text that follows it."""
    par, prev = x.getparent(), x.getprevious()
    if prev is not None:
        prev.tail = (prev.tail or '') + (x.tail or '')
    else:
        par.text = (par.text or '') + (x.tail or '')
    par.remove(x)


def _note_backlink(el):
    """A note entry whose way back is a separate '返回正文' link and whose anchor (the target of the mark in the text) an
    empty <span id>:  <p>[n]text<span id=x/><a href=#ref>返回正文</a></p>  or
    <p><span id=x/><a href=#ref id=y>[n]</a>text<a href=#ref>返回正文</a></p>  is rebuilt in place as
    <p><a href=#ref id=x>[n]</a>text</p>, the form of the other note entries: the number links back, the words go."""
    backs = [a for a in el.iter() if isinstance(a.tag, str) and ln(a) == 'a' and a.get('href')
             and not a.get('href').startswith(('http://', 'https://')) and _BACK_WORDS.fullmatch(''.join(a.itertext()))]
    if len(backs) != 1:
        return
    href = backs[0].get('href')
    _drop(backs[0])
    span = next((x for x in el.iter() if isinstance(x.tag, str) and ln(x) == 'span' and x.get('id') and len(x) == 0
                 and not (x.text or '').strip()), None)
    sid = span.get('id') if span is not None else None
    if span is not None:
        _drop(span)
    lead = el[0] if len(el) and isinstance(el[0].tag, str) and ln(el[0]) == 'a' and not (el.text or '').strip() else None
    if lead is not None and re.fullmatch(r'\s*\[\d+\]\s*', ''.join(lead.itertext())):
        lead.set('href', href)
        if sid:
            lead.set('id', sid)
        return
    m = re.match(r'\s*(\[\d+\])', el.text or '')
    if m:
        a = etree.Element('{%s}a' % etree.QName(el).namespace if etree.QName(el).namespace else 'a')
        a.text, a.tail = m.group(1), el.text[m.end():]
        a.set('href', href)
        if sid:
            a.set('id', sid)
        el.text = ''
        el.insert(0, a)


def _inline_one(x, part):
    """Runs of one element by itself (its tail left out): a link that sits beside the paragraph of an <aside>."""
    w = etree.Element('span')
    c = copy.deepcopy(x)
    c.tail = None
    w.append(c)
    return inline(w, part)


def plain(el):
    return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()


def _imgs(el):
    return [c for c in el.iter() if isinstance(c.tag, str) and ln(c) == 'img']


def items(part):
    _fixes(part)
    body = load_body(part)
    out = []

    dstack = []                                                    # classes of the <div>s around the current element
    grp = [0, 0]                                                   # (number of <div>s seen, the one the walk is in)
    ntab = [0]
    key = os.path.basename(os.environ.get('BOOK_SCRATCH', '').rstrip('/'))
    snap = SNAP.get(key, set())
    pno = int(part[4:]) if part[4:].isdigit() else -1

    def add(k, el, **kw):
        cls = el.get('class') or ''
        it = dict(k=k, tag=ln(el), cls=cls, id=anchor_key(part, el.get('id')) if el.get('id') else '', **kw)
        if dstack:
            it['dcls'] = ' '.join(dstack)
        if k == 'img':
            it['grp'] = grp[1]
        out.append(it)
        return it

    def walk(nodes, q=0, box=0, fig=0, note=0):
        for el in nodes:
            if not isinstance(el.tag, str):
                continue
            t = ln(el)
            cls = (el.get('class') or '').split()
            if t in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                imgs = [im for im in _imgs(el) if not set((im.get('class') or '').split()) & {'footnote', 'latex-inline'}]   # (a note icon is the mark, not a picture)
                runs = clean_runs([r for r in inline(el, part, mark_breaks=True)
                                   if not r.get('i') or 'latex-inline' in (r.get('c') or '').split()
                                   or r['i'].startswith('svg:')])   # (a letter set as a formula picture: '附录A', '6.4 B-脑')
                if runs:
                    add('h', el, runs=runs, lvl=int(t[1]))
                for im in imgs:
                    add('img', el, src=os.path.basename(im.get('src') or ''), runs=[], orn=1)
            elif t == 'p':
                _note_backlink(el)
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
                kids = [x for x in el.iter() if isinstance(x.tag, str)]
                num = next((x for x in kids if 'note-number' in (x.get('class') or '').split()), None)
                back = next((x for x in kids if ln(x) == 'a' and ('backlink' in (x.get('class') or '').split()
                             or _BACK_WORDS.fullmatch(''.join(x.itertext())) and not (x.get('href') or '').startswith('http'))), None)
                para = next(x for x in kids if ln(x) == 'p')
                m = re.match(r'\s*(\[[^\]\s]{1,6}\])', ''.join(para.itertext())) if num is None else None
                if (num is not None or m) and back is not None and el.get('id'):
                    # <aside id=fn-n><p><span.note-number>[n]</span><span.note-text>…</span>[<a.evidence-link>…]<a.backlink>返回正文</a>
                    # or <aside id=edit-note-n><p>[校n] text</p><a href=http…>核查来源：…</a><a href=#ref>返回正文</a>:
                    # the number becomes the marker, linked back to the reference; the back-link's own words go
                    label = ''.join(num.itertext()).strip() if num is not None else m.group(1)
                    to = resolve_href(part, back.get('href'))
                    runs = [r for r in clean_runs(inline(para, part) + [x for a in el if isinstance(a.tag, str) and ln(a) == 'a'
                                                                          for x in _inline_one(a, part)])
                            if not (r.get('h') == to and r['t'].strip() == ''.join(back.itertext()).strip())]
                    if runs and runs[0]['t'].lstrip().startswith(label):
                        runs[0] = dict(runs[0], t=runs[0]['t'].lstrip()[len(label):].lstrip())
                    rest = []
                    for r in runs:
                        if (r.get('h') or '').startswith('http'):            # the reviser's evidence: a link to its source
                            lead = '　' if r['t'].lstrip().startswith('核查') else '　核查依据：'
                            rest += [run(lead), dict(r, t=r['t'].strip(), c=_cls(r.get('c'), 'lnk'))]
                        elif r['t']:
                            rest.append(r)
                    add('note', el, runs=[run(label, 0, 0, to, anchor_key(part, el.get('id')))] + rest, q=0, box=0)
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
                dstack.extend(cls)
                grp[0] += 1
                outer, grp[1] = grp[1], grp[0]
                walk(el, q=q, box=1 if ('roundsolid' in cls or 'kx' in cls) else box, fig=1 if 'chatu' in cls else fig,
                     note=1 if ('fnote' in cls or 'annotation' in cls or '_idFootnote' in cls) else note)
                grp[1] = outer
                del dstack[len(dstack) - len(cls):]
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
                lists(el, 0)
            elif t == 'table':
                k = ntab[0]
                ntab[0] += 1
                if (pno, k) in snap:                                # set as a picture of the ebook's own table
                    fix_tree(part, el)                              # (tools/snap.py applies the same corrections)
                    grp[0] += 1
                    outer, grp[1] = grp[1], grp[0]
                    add('img', el, src=f'snap_{part}_{k}.png', runs=[], fig=fig, snap=1)
                    grp[1] = outer
                    continue
                cap = next((x for x in el if isinstance(x.tag, str) and ln(x) == 'caption'), None)
                if cap is not None and clean_runs(inline(cap, part)):
                    add('p', cap, runs=clean_runs(inline(cap, part)), q=q, box=box)['cls'] = 'table-caption'   # the table's title, above it
                rows, spans, heads = [], [], []
                for tr in el.iter():
                    if isinstance(tr.tag, str) and ln(tr) == 'tr':
                        tds = [td for td in tr if isinstance(td.tag, str) and ln(td) in ('td', 'th')]
                        rows.append([clean_runs(inline(td, part)) for td in tds])
                        spans.append([int(td.get('colspan') or 1) for td in tds])
                        heads.append(bool(tds) and all(ln(td) == 'th' for td in tds))
                add('table', el, rows=rows, runs=[], spans=spans, heads=heads)
            elif t == 'img':
                add('img', el, src=os.path.basename(el.get('src') or ''), runs=[], fig=fig)
            elif t in ('hr', 'nav', 'svg', 'br'):
                continue
            else:
                runs = clean_runs(inline(el, part))
                if runs:
                    add('p', el, runs=runs, q=q, box=box)

    def lists(el, depth):
        """<ul>/<ol> items; a nested list (inside an item) becomes items one level deeper."""
        kind = next((x for x in (el.get('class') or '').split() if x in ('square', 'square1', 'circle', 'disc')), '')
        for li in el:
            if not (isinstance(li.tag, str) and ln(li) == 'li'):
                continue
            subs = [x for x in li if isinstance(x.tag, str) and ln(x) in ('ul', 'ol')]
            if subs:
                for x in subs:                                      # the item's own text (without the nested lists) first
                    li.remove(x)
                runs = clean_runs(inline(li, part))
                for x in subs:
                    li.append(x)
                if runs:
                    add('li', li, runs=runs, depth=depth, bullet=kind)
                for x in subs:
                    lists(x, depth + 1)
                continue
            runs = clean_runs(inline(li, part))
            if runs:
                add('li', li, runs=runs, depth=depth, bullet=kind)

    walk(body)
    return _apply_fixes(part, out)
