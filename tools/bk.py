"""四本书的模块配置：巴菲特致股东的信·投资原则篇 / 财富、贫穷与政治 / 工作、消费主义和新穷人 / 股票大作手回忆录。

`book(b)` 返回 build.build 需要的 cfg（同黑格尔、康德、杜威各册）；页面为 16 开（BOOK_GEOM=k16）。
四本书各有一个工作目录（BOOK_SCRATCH），bk_make_all.py 逐本设置。
"""
import math
import os
import re
from . import bk_extract as BE, bk_text as BT, kant_struct as KS, special, style
from .book import Mod, title_text
from .kant import finish_blocks, balance_headings, wrap_lines, repair_link
from .dewey import make_toc as toc_blocks
from .model import run, merge_runs, runs_text, BR
from .books import page_module

P = lambda n: f'part{n:04d}'
NOTE_MIN = 2400          # notes of consecutive short chapters are gathered until they fill about two small-print pages

CFG = {
    1: dict(scratch='q1', file='巴菲特致股东的信', title='巴菲特致股东的信', sub='投资原则篇', author='〔美〕杰里米·米勒 著',
            credits=['郝旭奇　译'], publisher='中信出版集团', pdf_author='〔美〕杰里米·米勒', cover='cover00196.jpeg', title_img=None,
            copyright=27, marker='sq',
            front=[(2, 'dedication'), (3, 'kaitext'), (4, 'kaitext'), (5, 'text')], body=list(range(6, 20)),
            back=list(range(20, 27)), tail=[],
            inplace={'image00191.jpeg', 'image00192.jpeg', 'image00193.jpeg', 'image00194.jpeg', 'image00195.jpeg'}),
    2: dict(scratch='q2', file='财富、贫穷与政治', title='财富、贫穷与政治', sub='', author='〔美〕托马斯·索维尔 著',
            credits=['孙志杰　译'], publisher='浙江教育出版社', pdf_author='〔美〕托马斯·索维尔', cover='cover00223.jpeg', title_img=None,
            copyright=1, marker='plain', front=[], body=list(range(3, 9)), back=[9], tail=[], inplace=set()),
    3: dict(scratch='q3', file='工作、消费主义和新穷人', title='工作、消费主义和新穷人', sub='', author='〔英〕齐格蒙特·鲍曼 著',
            credits=['郭　楠　译'], publisher='上海社会科学院出版社', pdf_author='〔英〕齐格蒙特·鲍曼', cover='cover00111.jpeg',
            title_img='image00108.jpeg', copyright=1, marker='sq', front=[(2, 'text')], body=[4, 5, 6, 7, 8, 9, 10, 11, 12], back=[],
            tail=['image00109.jpeg', 'image00110.jpeg'], inplace=set()),
    4: dict(scratch='q4', file='股票大作手回忆录', title='股票大作手回忆录', sub='', author='〔美〕埃德温·勒菲弗 著',
            credits=['丁圣元　译'], publisher='凤凰出版社', pdf_author='〔美〕埃德温·勒菲弗', cover='cover00221.jpeg',
            title_img='image00200.jpeg', copyright=1, marker='paren', front=[(3, 'text'), (4, 'text')], body=list(range(5, 29)),
            back=[29, 30], tail=[], inplace={'image00219.jpeg', 'image00220.jpeg'}),
}
FILES = {b: f'{b:02d}-{CFG[b]["file"]}.pdf' for b in CFG}
TITLES = {b: CFG[b]['file'] for b in CFG}


def meta(b):
    C = CFG[b]
    return dict(title=C['title'], sub=C['sub'], author=C['author'], credits=C['credits'], series='', publisher=C['publisher'],
                subject=C['file'])


# ---------------------------------------------------------------------------------------------- headings
CN = '一二三四五六七八九十百'
ORD_ONLY = re.compile(r'^第[%s\d]+[部章节篇]分?$' % CN)
BARE = re.compile(r'^(第[%s\d]+[部章节篇]分?|§\s*\d+[.．]?|[%s]+|\d+[.．]?|[IVX]+[.．]?)$' % (CN, CN))
NUM_PATTERNS = [
    (re.compile(r'^(第[%s\d]+[部章节篇]分?)(?![的分])[\s　 ]*(?=\S)' % CN), '　'),
    (re.compile(r'^(附录[%s]+)[\s　 ]*(?=\S)' % CN), '　'),
    (re.compile(r'^([一二三四五六七八九十]+)[\s　 ]+(?=\S)'), '　'),
    (re.compile(r'^(§\s*\d+[.．])[\s　]*(?=\S)'), ' '),
    (re.compile(r'^(\d+[.．])[\s　]*(?=\S)'), ' '),
]
MARK_TAIL = re.compile(r'(?:⁠?[\[［(（]\d+[\]］)）])+$')
PART_RE = re.compile(r'^第[一二三四五六七八九十]+部分$')


def plain(runs):
    return re.sub(r'\s+', ' ', runs_text(runs)).strip()


def regap_heading(runs):
    """One solid gap between an ordinal and the title text; source line breaks inside a title removed."""
    if not runs:
        return runs
    first = runs[0]
    t = first['t']
    if len(runs) == 1 and ORD_ONLY.match(t.strip()):
        return [dict(first, t=t.strip())]
    head, body = '', t
    for pat, gap in NUM_PATTERNS:
        m = pat.match(t)
        if m:
            head, body = m.group(1) + gap, t[m.end():]
            break
    body = re.sub(' +', ' ', body)
    body = re.sub(r'\s+(?=——)', '', body)
    return [dict(first, t=head + body)] + [dict(r, t=re.sub(' +', ' ', r['t'])) if not r.get('i') else dict(r) for r in runs[1:]]


# ---------------------------------------------------------------------------------------------- markers
def mark_runs(runs, fmt):
    """Note markers (linked runs whose text is a bare note number) -> superscript '[n]' / '(n)', never at the start of a line."""
    out = []
    for r in runs:
        if (r.get('h') or r.get('a')) and not r.get('i'):
            mt = BT.marker_text(r['t'], fmt)
            if mt:
                r = repair_link(dict(r, t='⁠' + mt, s=1))
        out.append(r)
    return out


def latin_ratio(runs):
    t = plain(runs)
    return sum(1 for ch in t if ch.isascii() and ch.isalpha()) / max(1, len(t))


# ---------------------------------------------------------------------------------------------- elements
def _kai_only(runs):
    return bool(runs) and all('kai' in (r.get('c') or '').split() or not r['t'].strip() for r in runs)


def elements(C, items, kaitext=False):
    """Items of one part -> (elements, note items).  Headings carry 'lvl'; figures are {'k': 'fig'}; captions style 'cap'."""
    els, notes = [], []
    gap_before = False
    for it in items:
        k = it['k']
        if k == 'note':
            notes.append(it)
            continue
        if k == 'img':
            if it['src'] in C['tail']:
                continue                                    # the publisher's QR codes: kept as the last page of the book instead
            els.append(dict(k='orn' if it.get('orn') else 'fig', src=it['src']))
            continue
        if k == 'table':
            els.append(dict(k='table', rows=it['rows']))
            continue
        if k == 'p' and it.get('blank'):
            if els:
                gap_before = True                           # an empty paragraph = one blank line before the next paragraph
            continue
        runs = BT.fix_edges(BT.fix_runs(it['runs']))
        if not runs:
            continue
        cls = it['cls']
        if k == 'h':
            t = plain(runs)
            if t in ('注释', '注 释') or (els and els[-1]['k'] == 'h' and plain(els[-1]['runs']) == t):
                continue
            els.append(dict(k='h', lvl=float(it['lvl']), runs=runs, id=it['id'], src=f'h{it["lvl"]}.{cls}', cls=cls))
            continue
        if k == 'li':
            els.append(dict(k='p', style='noindent', runs=[run('•　')] + runs, id=it['id'], src='li'))
            continue
        b = dict(k='p', runs=runs, id=it['id'], src=f'p.{cls}')
        c = set(cls.split())
        t = plain(runs)
        if re.fullmatch(r'[—－-]{6,}', t):
            continue                                        # the dashed rule before the notes of book 4
        if c & {'tushuo', 'kindle-cn-picture-txt-withmanycharactors', 'kindle-cn-picture-txt-withfewcharactors'}:
            b['style'] = 'cap'
        elif c & {'right', 'Right', 'kindle-cn-para-right', 'Inscribe'}:
            b.update(style='right', nomerge=True)
        elif c & {'center', 'kindle-cn-para-center'}:
            b.update(style='center', nomerge=True)
        elif it.get('box'):
            b['style'] = 'quote'
        elif it.get('q'):
            b['style'] = 'quotel' if latin_ratio(runs) > 0.35 else 'quote'
            if c & {'noindent'}:
                b['style'] = 'noindent'
        elif c & {'noindent', 'kindle-cn-noindent'}:
            b['style'] = 'noindent'
        elif c & {'kindle-cn-kai'} or _kai_only(runs):
            b['style'] = 'quote'
        elif 'kaiti' in c or kaitext:
            b['style'] = 'kaibody'
        else:
            b['style'] = 'body'
        if gap_before and b['style'] in ('body', 'noindent', 'quote', 'quotel', 'kaibody', 'center', 'right'):
            b['before'] = 1
        gap_before = False
        els.append(b)
    return els, notes


def unit_blocks(els):
    els = [dict(b) for b in els]
    for b in els:
        if b['k'] == 'h':
            b['runs'] = regap_heading(b['runs'])
    KS.rank_headings([b for b in els if b['k'] != 'space'])
    for b in els:
        if b['k'] == 'h' and BARE.match(MARK_TAIL.sub('', plain(b['runs'])).replace('　', '').replace(' ', '')):
            b['style'] = 'secn'
    return els


# ---------------------------------------------------------------------------------------------- tables, figures
def table_blocks(rows):
    """A small text table -> one paragraph per row, cells as fixed-width inline boxes (hanging indent for the last cell)."""
    widths = []
    ncol = max(len(r) for r in rows)
    for j in range(ncol):
        widths.append(max(sum(2 if ord(ch) > 0x2e80 else 1 for ch in plain(r[j])) / 2.0 for r in rows if j < len(r)) + 1.6)
    cls_of = lambda w: f'tw w{min([x for x in (3, 4, 5, 6, 7, 8, 10, 12) if x >= w], default=12)}'
    used = [int(cls_of(w).split('w')[-1]) for w in widths]
    out = []
    for ri, r in enumerate(rows):
        runs = []
        for j in range(ncol):
            cell = BT.fix_edges(BT.fix_runs(r[j])) if j < len(r) else []
            last = j == ncol - 1
            if last:
                runs += [dict(x, b=1) if ri == 0 else x for x in cell]
            else:
                runs += [dict(x, c=(x.get('c', '') + ' ' + cls_of(widths[j])).strip(), **({'b': 1} if ri == 0 else {})) for x in cell]
                if not cell:
                    runs.append(run('⁠', c=cls_of(widths[j])))
        indent = sum(used[:-1])
        out.append(dict(k='p', style='trow', runs=runs, novary=True, nomerge=True, first=-indent, left=indent + 1,
                        before=1 if ri == 0 else 0, after=1 if ri == len(rows) - 1 else 0))
    return out


def fig_label(text):
    m = re.match(r'^(图[^\s　]+)', text)
    return m.group(1) if m else ''


def fig_paragraphs(C, els, fig_no):
    """Figures inside chapters -> 'see plate N' paragraphs; figures of appendices (C['inplace']) stay in the text."""
    out = []
    i = 0
    while i < len(els):
        b = els[i]
        if b['k'] != 'fig':
            out.append(b)
            i += 1
            continue
        i += 1
        caps = []
        while i < len(els) and els[i]['k'] == 'p' and els[i]['style'] == 'cap':
            caps.append(re.sub(r'\s+', ' ', runs_text(els[i]['runs'])).strip())
            i += 1
        text = '　'.join(caps)
        if b['src'] in C['inplace']:
            out.append(dict(k='fig', src=b['src']))
            for cp in caps:
                out.append(dict(k='p', style='quotel', runs=[run(cp)], first=0, left=0, right=0, nomerge=True))
            continue
        n = fig_no(b['src'], text)
        lab = fig_label(text)
        runs = []
        if lab:
            runs.append(run(lab + '　'))
        runs.append(run(f'见书后插图{n}', h=f'plate-{n}', a=f'figref-{n}', c='fig'))
        out.append(dict(k='p', style='center', runs=runs, novary=True, nosplit=True, nomerge=True, before=1, after=1, plate_ref=1))
    return out


def image_blocks(src, max_h, width=None):
    """A figure that stays in the text: an image block scaled into the text width (at most max_h pt high)."""
    from PIL import Image
    w, h = Image.open(os.path.join(special.IMG_DIR, src)).size
    s = min((width or style.TEXT_W) / w, max_h / h)
    iw, ih = w * s, h * s
    n = math.ceil(ih / style.LINE)
    return [dict(k='space', style='center', runs=[], n=1),
            dict(k='img', style='center', runs=[], src=special.img_url(src), w=round(iw, 2), h=round(ih, 2), n=n),
            dict(k='space', style='center', runs=[], n=1)]


def plate_modules(figs):
    if not figs:
        return []
    divider = page_module('plates', 'back', special.plate_divider_html(
        '书后插图', '正文中的图表集中排在此处，每页一图；正文中以蓝色“见书后插图N”标示，点击可跳转，每页底部附返回链接。'),
        toc=True, toc_title='书后插图', toc_level=0, title='书后插图', folio=True)
    mods = [divider]
    for k, (img, cap) in enumerate(figs, 1):
        def html(bb, page, k=k, img=img, cap=cap):
            return special.plates_page_html(k, img, bb, page, cap)
        m = page_module(f'plate-page{k}', 'back', html, toc=False, title=f'书后插图 {k}', folio=True, head=True)
        m.anchor = f'plate-{k}'
        m.lines = [cap]                                         # (for the text-fidelity report)
        mods.append(m)
    return mods


# ---------------------------------------------------------------------------------------------- notes
def note_blocks(items, fmt):
    out = []
    for it in items:
        runs = BT.fix_edges(BT.fix_runs(it['runs']))
        if not runs:
            continue
        first = runs[0]
        if (first.get('h') or first.get('a')) and BT.marker_text(first['t'], fmt):
            mt = BT.marker_text(first['t'], fmt)
            marks = [repair_link(dict(first, t=mt, s=0, c='nn'))]
            rest = runs[1:]
            if rest:
                rest[0] = dict(rest[0], t=rest[0]['t'].lstrip(' '))
            st = 'notel' if latin_ratio(rest) > 0.4 else 'note'
            out.append(dict(k='p', style=st, runs=merge_runs(marks + rest)))
        else:
            out.append(dict(k='p', style='notec', runs=runs))
    return out


def notes_module(mid, groups, fmt, zone='body', title='注　释'):
    blocks = [dict(k='h', style='h1', rank=1, runs=[run(title)], id=mid + '#top')]
    for gtitle, items in groups:
        if len(groups) > 1:
            blocks.append(dict(k='p', style='idxhead', runs=[run(gtitle)], nostart=False))
        blocks += note_blocks(items, fmt)
    return Mod(mid=mid, zone=zone, title='注释', blocks=blocks, grid='small1', toc_level=2, toc_title='注释')


# ---------------------------------------------------------------------------------------------- pages
def copyright_module(n):
    blocks = [dict(k='space', style='cip', runs=[], n=4)]
    for it in BE.items(P(n)):
        if it['k'] != 'p':
            continue
        runs = BT.fix_edges(BT.fix_runs(it['runs']))
        if not runs:
            continue
        t = plain(runs)
        runs = [dict(r, t=re.sub(r'(?<=[A-Z\d])-(?=\d)', '-⁠', r['t'])) for r in runs]
        if t.startswith(('图书在版编目', '版权信息')) or any(r.get('b') for r in runs) and len(t) < 8:
            runs = [dict(r, b=1) for r in runs]
            if len(blocks) > 1:
                blocks.append(dict(k='space', style='cip', runs=[], n=1))
        blocks.append(dict(k='p', style='cipj' if len(t) > 40 else 'cip', runs=runs, novary=True))
    return Mod(mid='copyright', zone='front', title='版权页', blocks=blocks, grid='small1', toc=False, head=False,
               folio=False, single=True)


def part_first_img(n):
    for it in BE.items(P(n)):
        if it['k'] == 'img':
            return it['src']
    raise KeyError(n)


def qr_html(imgs):
    """Publisher's QR codes of the last page (kept from the ebook): the images side by side."""
    from PIL import Image
    out = ''
    w = 130.0
    gap = 34.0
    x0 = (style.PAGE_W - len(imgs) * w - (len(imgs) - 1) * gap) / 2
    for k, name in enumerate(imgs):
        iw, ih = Image.open(os.path.join(special.IMG_DIR, name)).size
        h = w * ih / iw
        out += (f'<img src="{special.img_url(name)}" style="position:absolute;left:0;top:0;width:{w}pt;height:{h:.1f}pt;'
                f'transform:translate({x0 + k * (w + gap):.1f}pt,{style.TOP + 60 * style.SY:.1f}pt)">')
    return out


# ---------------------------------------------------------------------------------------------- book
def book(b):
    C = CFG[b]
    m = meta(b)
    mods = [page_module('cover', 'cover', special.cover_html(C['cover']), folio=False)]
    if C['title_img']:
        mods.append(page_module('title', 'front', special.cover_html(C['title_img']), folio=False))
    else:
        mods.append(page_module('title', 'front', special.title_html(m), folio=False))
    mods.append(copyright_module(C['copyright']))
    fig_list = []

    def fig_no(src, cap):
        fig_list.append((src, cap))
        return len(fig_list)

    front, body, back = [], [], []
    pend, pend_chars = [], 0
    counter = [0]
    fmt = C['marker']

    def flush(zone_list, zone):
        nonlocal pend, pend_chars
        if pend:
            counter[0] += 1
            zone_list.append(notes_module(f'notes{counter[0]}', pend, fmt, zone=zone))
            pend, pend_chars = [], 0

    def add_unit(n, zone_list, zone, els, notes, top=False, kaitext=False, toc=True):
        nonlocal pend_chars
        els = fig_paragraphs(C, els, fig_no)
        blocks = []
        for e in unit_blocks(els):
            if e['k'] == 'fig':
                blocks += image_blocks(e['src'], style.TEXT_H - 11 * style.LINE)      # leaves room for the heading above and a source line below
            elif e['k'] == 'orn':
                blocks += [dict(k='img', style='orn', runs=[], src=special.img_url(e['src']), w=70.0, h=9.9, n=1)]
            elif e['k'] == 'table':
                blocks += table_blocks(e['rows'])
            else:
                blocks.append(e)
        blocks = wrap_lines(finish_blocks(blocks))
        for x in blocks:
            if x['k'] in ('p', 'h') and x.get('runs'):
                x['runs'] = mark_runs(x['runs'], fmt)
        blocks = balance_headings(blocks)
        for x in blocks:
            if x['k'] == 'h':
                rs = x['runs']
                for i in range(len(rs) - 1):
                    if rs[i]['t'] == '\n' and rs[i + 1].get('s'):
                        rs[i], rs[i + 1] = rs[i + 1], rs[i]
        title = next((title_text(x['runs']) for x in blocks if x['k'] == 'h'), '')     # no heading (a statement page): no bookmark
        mod = Mod(mid=P(n), zone=zone, title=title, blocks=blocks, toc_level=1, toc=toc and any(x['k'] == 'h' for x in blocks))
        mod.src_part = n
        mod.top = top
        zone_list.append(mod)
        if notes:
            pend.append((title, notes))
            pend_chars += sum(len(runs_text(i['runs'])) for i in notes)

    for n, kind in C['front']:
        els, notes = elements(C, BE.items(P(n)), kaitext=(kind == 'kaitext'))
        if kind == 'dedication':
            lines = [(99, plain(e['runs'])) for e in els if e['k'] == 'p']
            dm = page_module('dedication', 'front', special.divider_html(lines), toc=False, title='献词', folio=False, head=False)
            dm.lines = [t for _, t in lines]
            dm.src_parts = [n]
            front.append(dm)
            continue
        add_unit(n, front, 'front', els, notes, top=True, kaitext=(kind == 'kaitext'))
    flush(front, 'front')
    for n in C['body']:
        els, notes = elements(C, BE.items(P(n)))
        if els and els[0]['k'] == 'h' and PART_RE.match(plain(els[0]['runs'])):
            title_s = plain(regap_heading(els[0]['runs']))
            div = page_module(f'div{n}', 'body', special.divider_html([(1.0, title_s)]), toc=True, toc_title=title_s,
                              toc_level=0, title=title_s, folio=False, head=False)
            div.part = True
            div.lines = [title_s]
            div.src_parts = [n]
            flush(body, 'body')
            body.append(div)
            els = els[1:]
            if not els:
                continue
        add_unit(n, body, 'body', els, notes)
        if pend_chars >= NOTE_MIN:
            flush(body, 'body')
    flush(body, 'body')
    for n in C['back']:
        els, notes = elements(C, BE.items(P(n)))
        add_unit(n, back, 'back', els, notes, top=True)
        flush(back, 'back')
    plates = plate_modules(fig_list)
    allm = front + body + back + plates
    toc_bl = toc_blocks(allm)
    for x in toc_bl:
        if x.get('style', '').startswith('toc'):
            x['noshrink'] = True
    toc = Mod(mid='toc', zone='front', title='目录', blocks=toc_bl, toc=False, head=True)
    toc.tail_min = 5
    tail = []
    if C['tail']:
        tail.append(page_module('qr', 'back', qr_html(C['tail']), folio=False))
    mods += [toc] + allm + tail
    return dict(id=f'b{b}', title=C['title'], meta=dict(m, author=C['pdf_author']), modules=mods, toc=toc, vol=b)
