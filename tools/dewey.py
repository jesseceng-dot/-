"""《杜威著作精选11种》每册的模块配置（封面/书名页/版权页/目录/前置文/正文/注释/后记/书后插图/折页）。

`book(v)` 返回 build.build 需要的 cfg（同黑格尔、康德各册）。
"""
import math
import re
from . import dewey_extract as DE, dewey_text as DT, kant_struct as KS, normalize, special, style
from .book import Mod, title_text
from .kant import finish_blocks, mark_markers, balance_headings, wrap_lines, repair_link, plain_of
from .model import run, merge_runs, runs_text
from .books import page_module

P = lambda n: f'part{n:04d}'
SERIES = '杜威著作精选'
AUTHOR = '〔美〕约翰·杜威'
PUBLISHER = '华东师范大学出版社'
NOTE_MIN = 2400          # notes of consecutive short chapters are gathered until they fill about two small-print pages

# 每册的部件编号（来自电子书的目录 toc.ncx）。
#   cover 封面图部件；front_flap 前折页；title 书名页（整页图）；copyright 版权页（CIP）；front 前置文（主编序、序……）；
#   body 正文各章（含“第N部分”标题）；back 后记/附录；back_flap 后折页与封底（整页图）
VOL = {
    1: dict(title='学校与社会', cover=1, title_img=2, copyright=3, front=[4, 5, 6], body=range(8, 17), back=[17]),
    2: dict(title='明天的学校', cover=18, title_img=19, copyright=35, front=[20, 21], body=range(23, 34), back=[34]),
    3: dict(title='民主与教育', cover=36, title_img=37, copyright=68, front=[38, 39], body=range(41, 67), back=[67]),
    4: dict(title='作为经验的艺术', cover=69, title_img=70, copyright=90, front=[71, 72, 73], body=range(75, 89), back=[89]),
    5: dict(title='哲学的改造', cover=91, title_img=92, copyright=106, front=[93, 94], body=range(96, 104), back=[104, 105]),
    6: dict(title='经验与自然', cover=107, title_img=108, copyright=124, front=[109, 110], body=range(112, 122), back=[122, 123]),
    7: dict(title='确定性的寻求', sub='关于知行关系的研究', cover=125, title_img=126, copyright=141, front=[127], body=range(129, 140), back=[140]),
    8: dict(title='心理学', cover=142, title_img=143, copyright=173, front=[144, 145, 146], body=range(148, 170), back=[170, 171, 172]),
    9: dict(title='伦理学', cover=174, front_flap=175, title_img=176, copyright=208, front=[177, 178, 179], body=range(181, 207),
            back=[207], back_flap=[209, 210]),
    10: dict(title='我们如何思维', cover=211, front_flap=212, title_img=213, copyright=238, front=[214, 215, 216], body=range(218, 237),
             back=[237], back_flap=[239, 240]),
    11: dict(title='人性与行为', sub='社会心理学导论', cover=241, front_flap=242, title_img=243, copyright=244, front=[246, 247, 248],
             body=range(249, 275), back=[275, 276], back_flap=[277, 278]),
}
TITLES = {v: VOL[v]['title'] for v in VOL}
FILES = {v: f'{v:02d}-{TITLES[v]}.pdf' for v in VOL}
# 部件里紧接在标题后的图（章节页上的插图）留在原处，不后置到书后
INPLACE = {'image01797.jpeg'}


def part_img(n):
    for it in DE.items(P(n)):
        if it['k'] == 'img':
            return it['src']
    raise KeyError(n)


def meta(v):
    d = VOL[v]
    return dict(title=d['title'], sub=d.get('sub', ''), author=AUTHOR, credits=[], series=SERIES, publisher=PUBLISHER, subject=SERIES)


# ---------------------------------------------------------------------------------------------- headings
ORD_ONLY = re.compile(r'^第[一二三四五六七八九十百\d]+[部章节篇]分?$')
BARE = re.compile(r'^(第[一二三四五六七八九十百\d]+[部章节篇]分?|§\s*\d+[.．]?|[一二三四五六七八九十]+|\d+[.．]?|[IVX]+[.．]?)$')
NUM_PATTERNS = [
    (re.compile(r'^(第[一二三四五六七八九十百\d]+[部章节篇]分?)(?![的分])[\s　 ]*(?=\S)'), '　'),
    (re.compile(r'^(§\s*\d+[.．])[\s　]*(?=\S)'), ' '),
    (re.compile(r'^(\d+[.．])[\s　]*(?=\S)'), ' '),
    (re.compile(r'^([IVX]+[.．])[\s　]*(?=[^\sIVX.．])'), ' '),
    (re.compile(r'^([IVX]+)[\s　]+(?=[^\sIVX.．])'), '　'),
]
MARK_TAIL = re.compile(r'(?:⁠?[\[［]\d+[\]］])+$')
PART_RE = re.compile(r'^第[一二三四五六七八九十]+部分')


def plain(runs):
    return re.sub(r'\s+', ' ', runs_text(runs)).strip()


def regap_heading(runs):
    """One solid gap between an ordinal (or label) and the title text; source line breaks inside a title removed."""
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
    return [dict(first, t=head + body)] + [dict(r, t=re.sub(' +', ' ', r['t'])) if not r.get('i') else dict(r) for r in runs[1:]]


# ---------------------------------------------------------------------------------------------- elements
def elements(items):
    """Items of one part -> (elements, note items).  Headings carry 'lvl'; figures are {'k': 'fig'}; captions style 'cap'."""
    els, notes = [], []
    prev = None
    for it in items:
        k = it['k']
        if k == 'note':
            notes.append(it)
            continue
        if k == 'img':
            els.append(dict(k='fig', src=it['src']))
            prev = 'fig'
            continue
        runs = DT.fix_edges(DT.fix_runs(it['runs']))
        if not runs:
            continue
        cls = it['cls']
        if k == 'h':
            t = plain(runs)
            if els and els[-1]['k'] == 'h' and plain(els[-1]['runs']) == t:
                continue                                   # the title typed twice (h1 + h2) in the source
            els.append(dict(k='h', lvl=float(it['lvl']), runs=runs, id=it['id'], src=f'h{it["lvl"]}.{cls}'))
            prev = 'h'
            continue
        b = dict(k='p', runs=runs, id=it['id'], src=f'p.{cls}')
        if cls == '':
            b['style'] = 'body'
        elif cls == 'block':
            t = plain(runs)
            latin = sum(1 for ch in t if ch.isascii() and ch.isalpha())
            b['style'] = 'quotel' if latin > 0.35 * len(t) else 'quote'      # bibliography lines in English: ragged right
        elif cls in ('right', 'block1'):
            b['style'] = 'right'
            b['nomerge'] = True
        elif cls == 'block2':
            b['style'] = 'center'
            b['nomerge'] = True
        elif cls == 'left':
            b['style'] = 'refhead'
        elif cls == 'img':
            b['style'] = 'cap'
        else:
            b['style'] = 'body'
        els.append(b)
        prev = 'p'
    return els, notes


def unit_blocks(els):
    """Duplicate titles dropped, headings regapped and ranked (rank 1 = the module's own title)."""
    els = [dict(b) for b in els]
    for b in els:
        if b['k'] == 'h':
            b['runs'] = regap_heading(b['runs'])
    KS.rank_headings(els)
    for b in els:
        if b['k'] == 'h' and BARE.match(MARK_TAIL.sub('', plain(b['runs'])).replace('　', '').replace(' ', '')):
            b['style'] = 'secn'
    return els


# ---------------------------------------------------------------------------------------------- figures
def fig_paragraphs(els, fig_no, plate_caps):
    """Stand-alone figures -> 'see plate N' paragraphs that keep the caption; figures that open a chapter stay where they are
    (an image block + caption).  `fig_no(src, caption)` numbers a plate; captions of plates are collected in plate_caps."""
    out = []
    i = 0
    while i < len(els):
        b = els[i]
        if b['k'] != 'fig':
            out.append(b)
            i += 1
            continue
        cap = None
        if i + 1 < len(els) and els[i + 1]['k'] == 'p' and els[i + 1]['style'] == 'cap':
            cap = els[i + 1]
        i += 2 if cap is not None else 1
        text = re.sub(r'\s*[\n\u2028]+\s*', '　', runs_text(cap['runs'])).strip() if cap is not None else ''
        if b['src'] in INPLACE:
            out.append(dict(k='fig', src=b['src']))
            if cap is not None:
                out.append(dict(cap, style='ck'))
            continue
        n = fig_no(b['src'], text)
        runs = []
        if text:
            runs.append(run(text + '　'))
        runs.append(run(f'见书后插图{n}', h=f'plate-{n}', a=f'figref-{n}', c='fig'))
        out.append(dict(k='p', style='center', runs=runs, novary=True, nosplit=True, nomerge=True, before=1, after=1, plate_ref=1))
    return out


def inplace_blocks(src):
    """A figure that stays in the text: an image block scaled into the text width (at most 230 pt high)."""
    from PIL import Image
    import os
    w, h = Image.open(os.path.join(special.IMG_DIR, src)).size
    s = min(style.TEXT_W / w, 230.0 / h)
    iw, ih = w * s, h * s
    n = math.ceil(ih / style.LINE)
    return [dict(k='space', style='center', runs=[], n=1),
            dict(k='img', style='center', runs=[], src=special.img_url(src), w=round(iw, 2), h=round(ih, 2), n=n),
            dict(k='space', style='center', runs=[], n=1)]


def plate_modules(figs):
    """One plate per page: caption 'Plate N　<figure caption>' at the top, the figure, a return link at the foot."""
    if not figs:
        return []
    divider = page_module('plates', 'back', special.plate_divider_html(
        '书后插图', '本册正文中的图表一律集中排在此处，每页一图；正文中以蓝色“见书后插图N”标示，点击可跳转，每页底部附返回链接。'),
        toc=True, toc_title='书后插图', toc_level=0, title='书后插图', folio=True)
    mods = [divider]
    for k, (img, cap) in enumerate(figs, 1):
        def html(bb, page, k=k, img=img, cap=cap):
            return special.plates_page_html(k, img, bb, page, cap)
        m = page_module(f'plate-page{k}', 'back', html, toc=False, title=f'书后插图 {k}', folio=True, head=True)
        m.anchor = f'plate-{k}'
        mods.append(m)
    return mods


# ---------------------------------------------------------------------------------------------- notes
def note_blocks(items):
    """Note items of one part -> small-print blocks (number column + text)."""
    out = []
    for it in items:
        runs = DT.fix_edges(DT.fix_runs(it['runs']))
        if not runs:
            continue
        first = runs[0]
        if (first.get('h') or first.get('a')) and DE.MARK_RE.match(first['t'].strip()):
            marks = [repair_link(dict(first, s=0, c='nn'))]
            rest = runs[1:]
            if rest:
                rest[0] = dict(rest[0], t=rest[0]['t'].lstrip(' '))
            out.append(dict(k='p', style='note', runs=merge_runs(marks + rest)))
        else:
            out.append(dict(k='p', style='notec', runs=runs))
    return out


def notes_module(mid, groups, zone='body', title='注　释'):
    """One endnotes module for several chapters: heading, then (if more than one source) a small heading per source."""
    blocks = [dict(k='h', style='h1', rank=1, runs=[run(title)], id=mid + '#top')]
    for gtitle, items in groups:
        if len(groups) > 1:
            blocks.append(dict(k='p', style='idxhead', runs=[run(gtitle)], nostart=False))
        blocks += note_blocks(items)
    return Mod(mid=mid, zone=zone, title='注释', blocks=blocks, grid='small1', toc_level=2, toc_title='注释')


# ---------------------------------------------------------------------------------------------- pages
def copyright_module(n):
    """版权页 / CIP: every original line, small print, one page."""
    blocks = [dict(k='space', style='cip', runs=[], n=4)]
    for it in DE.items(P(n)):
        if it['k'] != 'p':
            continue
        runs = DT.fix_edges(DT.fix_runs(it['runs']))
        if not runs:
            continue
        t = plain(runs)
        if t == '杜威著作精选':
            blocks.append(dict(k='space', style='cip', runs=[], n=2))
        first = t.startswith('图书在版编目')
        runs = [dict(r, t=re.sub(r'(?<=[A-Z\d])-(?=\d)', '-\u2060', r['t'])) for r in runs]      # 'G40-06' stays in one piece
        st = 'cipj' if len(t) > 40 else 'cip'
        if any(r.get('b') for r in runs) or first:
            runs = [dict(r, b=1) for r in runs]
        blocks.append(dict(k='p', style=st, runs=runs, novary=True))
    return Mod(mid='copyright', zone='front', title='版权页', blocks=blocks, grid='small1', toc=False, head=False,
               folio=False, single=True)


def make_toc(mods, title='目　录'):
    """Contents: the chapters (with the parts they belong to as bold lines) and the rank-2 headings inside them."""
    from .model import run as R
    blocks = [dict(k='h', style='tochead', rank=1, runs=[R(title)], id='toc')]
    under = False
    for mod in mods:
        if mod.mid == 'toc':
            continue
        if mod.kind == 'page':
            if mod.toc and mod.toc_title:
                under = mod.mid not in ('plates',) and getattr(mod, 'part', False)
                blocks.append(dict(k='p', style='toc0', runs=[R(mod.toc_title, h=mod.mid)], h=mod.mid, toc_ref=(mod.mid, None)))
            continue
        if not mod.toc:
            continue
        if getattr(mod, 'top', False):
            under = False
        ind = 'i' if under else ''
        label = mod.toc_title or mod.title
        if mod.toc_level == 1:
            blocks.append(dict(k='p', style='toc1' + ind, runs=[R(label, h=mod.mid)], h=mod.mid, toc_ref=(mod.mid, None)))
        else:
            blocks.append(dict(k='p', style='toc2' + ind, runs=[R(label, h=mod.mid)], h=mod.mid, toc_ref=(mod.mid, None)))
            continue
        cand = []
        for bi, b in enumerate(mod.blocks):
            if b['k'] != 'h' or bi == 0 or b.get('notoc') or b['rank'] != 2:
                continue
            t = title_text(b['runs'])
            if BARE.match(t.replace('　', '').replace(' ', '')):
                continue
            cand.append((bi, b, t))
        mod.toc_heads = [(bi, b['rank']) for bi, b, t in cand]
        for bi, b, t in cand:
            if not b.get('id'):
                b['id'] = f'{mod.mid}#h{bi}'
            blocks.append(dict(k='p', style='toc2' + ind, runs=[R(t, h=b['id'])], h=b['id'], toc_ref=(mod.mid, bi)))
    return blocks


# ---------------------------------------------------------------------------------------------- book
def book(v):
    V = VOL[v]
    m = meta(v)
    mods = [page_module('cover', 'cover', special.cover_html(part_img(V['cover'])), folio=False)]
    if V.get('front_flap'):
        mods.append(page_module('flap0', 'front', special.cover_html(part_img(V['front_flap'])), folio=False))
    mods.append(page_module('title', 'front', special.cover_html(part_img(V['title_img'])), folio=False))
    mods.append(copyright_module(V['copyright']))

    fig_list = []

    def fig_no(src, cap):
        fig_list.append((src, cap))
        return len(fig_list)

    front, body, back = [], [], []
    pend, pend_chars = [], 0
    counter = [0]

    def flush(zone_list, zone):
        nonlocal pend, pend_chars
        if pend:
            counter[0] += 1
            nm = notes_module(f'notes{counter[0]}', pend, zone=zone)
            zone_list.append(nm)
            pend, pend_chars = [], 0

    def add_unit(n, zone_list, zone, els, notes, top=False, part=False):
        nonlocal pend_chars
        els = fig_paragraphs(els, fig_no, [])
        blocks = []
        for b in unit_blocks(els):
            if b['k'] == 'fig':
                blocks += inplace_blocks(b['src'])
            else:
                blocks.append(b)
        blocks = wrap_lines(finish_blocks(blocks))
        for b in blocks:
            if b['k'] == 'h':
                b['runs'] = mark_markers(b['runs'])
        blocks = balance_headings(blocks)
        for b in blocks:
            if b['k'] == 'h':                                # a note marker never starts a line: move the forced break behind it
                rs = b['runs']
                for i in range(len(rs) - 1):
                    if rs[i]['t'] == '\n' and rs[i + 1].get('s'):
                        rs[i], rs[i + 1] = rs[i + 1], rs[i]
        title = next((title_text(b['runs']) for b in blocks if b['k'] == 'h'), P(n))
        mod = Mod(mid=P(n), zone=zone, title=title, blocks=blocks, toc_level=1)
        mod.src_part = n
        mod.top = top
        zone_list.append(mod)
        if notes:
            pend.append((title, notes))
            pend_chars += sum(len(runs_text(i['runs'])) for i in notes)

    # front matter (主编序、序、前言、作者说明 ...)
    for n in V['front']:
        els, notes = elements(DE.items(P(n)))
        if not any(e['k'] == 'h' for e in els):                 # the dedication of 《作为经验的艺术》: one page of centred lines
            lines = [(99, plain(e['runs'])) for e in els]
            dm = page_module(f'dedication', 'front', special.divider_html([(3.0, lines[0][1])] + lines[1:]), toc=False,
                             title='献词', folio=False, head=False)
            dm.lines = [t for _, t in lines]
            dm.src_parts = [n]
            front.append(dm)
            continue
        add_unit(n, front, 'front', els, notes, top=True)
    flush(front, 'front')
    # body: chapters, with a divider page for every "第N部分"
    for n in V['body']:
        els, notes = elements(DE.items(P(n)))
        if els and els[0]['k'] == 'h' and PART_RE.match(plain(els[0]['runs'])):
            head = els[0]
            title = regap_heading(head['runs'])
            title_s = title_text(title)
            div = page_module(f'div{n}', 'body', special.divider_html([(1.0, title_s)]), toc=True, toc_title=title_s,
                              toc_level=0, title=title_s, folio=False, head=False)
            div.part = True
            div.lines = [title_s]
            div.src_parts = [n]
            if pend:
                flush(body, 'body')
            body.append(div)
            els = els[1:]
            if not els:
                continue
        add_unit(n, body, 'body', els, notes)
        if pend_chars >= NOTE_MIN:
            flush(body, 'body')
    flush(body, 'body')
    # back matter (译后记、附录、校后记)
    for n in V['back']:
        els, notes = elements(DE.items(P(n)))
        add_unit(n, back, 'back', els, notes, top=True)
        flush(back, 'back')
    plates = plate_modules(fig_list)
    allm = front + body + back + plates
    toc = Mod(mid='toc', zone='front', title='目录', blocks=make_toc(allm), toc=False, head=True)
    toc.tail_min = 5
    tail = []
    for key in ('back_flap',):
        for j, n in enumerate(V.get(key, [])):
            tail.append(page_module(f'flap{j + 1}', 'back', special.cover_html(part_img(n)), folio=False))
    mods += [toc] + allm + tail
    return dict(id=f'd{v}', title=V['title'], meta=m, modules=mods, toc=toc, vol=v)
