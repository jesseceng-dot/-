"""《康德文集（注释版）》10 册：每册的模块配置（封面/书名页/版权页/目录/前言/序/正文/注释/书后插图）。

`book(v)` 返回 build.build 需要的 cfg（同黑格尔各册）。
"""
import re
import copy
from . import kant_extract as KE, kant_text as KT, kant_struct as KS, normalize, special, style
from .book import Mod, title_text
from .model import run, merge_runs, runs_text, BR, OBJ
from .books import page_module, first_title

P = KS.P
SERIES = '康德文集（注释版）'
AUTHOR = '〔德〕康德 著'
CREDIT = '李秋零　译注'
PUBLISHER = '中国人民大学出版社'
TITLES = {1: '康德三大批判合集', 2: '康德人类学文集', 3: '康德道德哲学文集', 4: '康德历史哲学文集', 5: '康德政治哲学文集',
          6: '康德美学文集', 7: '康德认识论文集', 8: '康德自然哲学文集', 9: '康德宗教哲学文集', 10: '康德教育哲学文集'}
COVERS = {1: 'image04121.jpeg', 2: 'image04134.jpeg', 3: 'image04136.jpeg', 4: 'image04145.jpeg', 5: 'image04146.jpeg',
          6: 'image04150.jpeg', 7: 'image04152.jpeg', 8: 'image04171.jpeg', 9: 'image04238.jpeg', 10: 'image04239.jpeg'}
FILES = {v: f'{v:02d}-{TITLES[v]}.pdf' for v in TITLES}
NOTE_MIN = 2400          # notes of consecutive short parts are gathered until they fill about two small-print pages


def meta(v):
    return dict(title=TITLES[v], sub='（注释版）', author=AUTHOR, credits=[CREDIT], series=SERIES, publisher=PUBLISHER)


# ---------------------------------------------------------------------------------------------- text blocks
def finish_blocks(els):
    """Elements of a unit -> typeset blocks (markers as superscripts, separators, figure placeholders left for plates)."""
    out = []
    for b in els:
        b = dict(b)
        if b['k'] == 'p':
            b['runs'] = mark_markers(b['runs'])
            st = b['style']
            if st == 'sep':
                b['runs'] = [run('※　　※　　※')]
                b['nohead'] = True
            elif st in ('center', 'ck', 'cap'):
                b['nomerge'] = True
                if st == 'cap':
                    b['style'] = 'ck'
            elif st == 'right':
                b['nomerge'] = True
        out.append(b)
    return out


def repair_link(r):
    """A marker / note entry whose link lost its fragment in the source ('part0069.xhtml' instead of '...#notef6')."""
    h, a = r.get('h', ''), r.get('a', '')
    if h and '#' not in h and a:
        if '#notef' in a:
            r = dict(r, h=a.replace('#notef', '#note'))
        elif '#note' in a:
            r = dict(r, h=a.replace('#note', '#notef'))
    return r


def mark_markers(runs):
    """Bracketed note markers: superscript, blue, never at the start of a line (word joiner)."""
    res = []
    for r in runs:
        r = repair_link(r)
        if (r.get('h') or r.get('a')) and KE.MARK_RE.match(r['t'].strip()) and not r.get('c'):
            t = r['t']
            if not t.startswith('⁠'):
                t = '⁠' + t
            r = dict(r, s=1, t=t)
            if r.get('h') and not r.get('a') and re.search(r'#b-\d+$', r['h']):
                r['a'] = r['h'].replace('#b-', '#a-')
        res.append(r)
    return res


def balance_headings(blocks):
    """Balanced line breaks for long centred headings (ordinal gaps were already set by kant_struct.regap_heading)."""
    from .layout import STYLES
    for b in blocks:
        if b['k'] != 'h':
            continue
        st = STYLES[b['style']]
        avail = 294 - (st['left'] + st['right']) * st['fs']
        if st['align'] == 'c' or b['rank'] <= 2:
            b['runs'] = normalize.balance_title(b['runs'], st['fs'], avail)
    return blocks


def wrap_lines(blocks):
    """Short centred / right lines that are too long for one line get balanced manual line breaks (as in the Hegel books)."""
    blocks = normalize.group_verse(blocks)
    blocks = normalize.wrap_short_lines(blocks)
    return normalize.keep_signatures(blocks)


def note_blocks(items, vol=None):
    """Note items of one part -> small-print blocks (number column + text, continuation lines, right-aligned source lines)."""
    out = []
    for it in items:
        runs = KT.fix_edges(KT.fix_runs(it['runs']))
        if not runs:
            continue
        first = runs[0]
        cls = it['cls']
        if (first.get('h') or first.get('a')) and KE.MARK_RE.match(first['t'].strip()):
            lead = 1
            while lead < len(runs) and (runs[lead].get('h') or runs[lead].get('a')) and KE.MARK_RE.match(runs[lead]['t'].strip()):
                lead += 1
            marks = [repair_link(dict(r, s=0)) for r in runs[:lead]]
            marks[0]['c'] = 'nn'
            rest = runs[lead:]
            if rest:
                rest[0] = dict(rest[0], t=rest[0]['t'].lstrip(' '))
            out.append(dict(k='p', style='note', runs=merge_runs(marks + rest)))
        elif cls == 'noteContent-r':
            out.append(dict(k='p', style='noter', runs=runs))
        else:
            out.append(dict(k='p', style='notec', runs=runs))
    return out


def notes_module(mid, groups, title='注　释'):
    """One endnotes module for several parts: heading, then (if more than one source) a small heading per source."""
    blocks = [dict(k='h', style='h1', rank=1, runs=[run(title)], id=mid + '#top')]
    for gi, (gtitle, items) in enumerate(groups):
        if len(groups) > 1:
            blocks.append(dict(k='p', style='idxhead', runs=[run(gtitle)], nostart=False))
        blocks += note_blocks(items)
    return Mod(mid=mid, zone='body', title='注释', blocks=blocks, grid='small1', toc_level=2, toc_title='注释')


# ---------------------------------------------------------------------------------------------- pages
def copyright_module(v):
    fp = KS.front_parts(v)
    lines = []
    if fp['copyright']:
        for it in KE.items(P(fp['copyright'])):
            if it['k'] == 'p' and it['cls'] == 'copyright-bodytext':
                t = re.sub(r'\s+', ' ', runs_text(it['runs'])).strip()
                lines.append(KT.fix_text(t))
    else:
        lines = [f'书名：{TITLES[v]}（注释版）', '作者：[德]康德', '译者：李秋零', f'出版社：{PUBLISHER}', '出版日期：2016-08']
    blocks = [dict(k='space', style='cip', runs=[], n=8)]
    blocks.append(dict(k='p', style='cipc', runs=[run('版　权　信　息', b=1)], novary=True, bold=1))
    blocks.append(dict(k='space', style='cip', runs=[], n=2))
    for t in lines:
        blocks.append(dict(k='p', style='cipc', runs=[run(t)], novary=True))
    return Mod(mid='copyright', zone='front', title='版权页', blocks=blocks, grid='small1', toc=False, head=False,
               folio=False, single=True)


def front_text_module(v, which):
    """前言（李秋零）/ 序（苗力田）: the same text opens every volume.  Returns (module, notes items)."""
    fp = KS.front_parts(v)
    n = fp[which]
    els, notes = KS.elements(KE.items(P(n)), v, n)
    unit = dict(kind='text', els=els, notes=[], parts=[n])
    blocks = KS.unit_blocks(unit, v)
    blocks = wrap_lines(finish_blocks(blocks))
    for b in blocks:
        if b['k'] == 'h':
            b['rank'] = 1
            b['style'] = 'h1'
    blocks = balance_headings(blocks)
    return Mod(mid=P(n), zone='front', title=title_text(blocks[0]['runs']) if blocks and blocks[0]['k'] == 'h' else which, blocks=blocks), notes


# ---------------------------------------------------------------------------------------------- plates
def collect_figs(units):
    """Number the figures of a volume in reading order; returns [(img name, ref anchor)]."""
    figs = []
    for u in units:
        for b in u['els']:
            if b['k'] == 'fig':
                figs.append(b['src'])
    return figs


def fig_paragraphs(els, fig_no, mid_prefix):
    """Replace figure elements by centred 'see plate N' paragraphs (joined with a following caption such as '图1')."""
    out = []
    i = 0
    while i < len(els):
        b = els[i]
        if b['k'] != 'fig':
            out.append(b)
            i += 1
            continue
        group = []
        while i < len(els) and els[i]['k'] == 'fig':
            group.append(els[i])
            i += 1
        cap = None
        if i < len(els) and els[i]['k'] == 'p' and els[i]['style'] in ('cap', 'ck') and len(plain_of(els[i])) < 60 \
                and els[i].get('src', '').startswith('p.') and els[i]['runs'] and re.match(r'^图', plain_of(els[i])):
            cap = els[i]
            i += 1
        runs = []
        if cap is not None:
            runs.append(run(plain_of(cap) + '　'))
        for j, f in enumerate(group):
            n = fig_no(f['src'])
            if j:
                runs.append(run('　'))
            runs.append(run(f'见书后插图{n}', h=f'plate-{n}', a=f'figref-{n}', c='fig'))
        out.append(dict(k='p', style='center', runs=runs, novary=True, nosplit=True, nomerge=True, before=1, after=1, plate_ref=1))
    return out


def plain_of(b):
    return re.sub(r'\s+', ' ', runs_text(b['runs']))


def plate_modules(v, figs, caption):
    if not figs:
        return []
    divider = page_module('plates', 'back', special.plate_divider_html(
        '书后插图', '本册正文中的图表一律集中排在此处，每页一图；正文中以蓝色“见书后插图N”标示，点击可跳转，每页底部附返回链接。'),
        toc=True, toc_title='书后插图', toc_level=0, title='书后插图', folio=True)
    mods = [divider]
    for k, img in enumerate(figs, 1):
        def html(bb, page, k=k, img=img):
            return special.plates_page_html(k, img, bb, page, caption)
        m = page_module(f'plate-page{k}', 'back', html, toc=False, title=f'书后插图 {k}', folio=True, head=True)
        m.anchor = f'plate-{k}'
        mods.append(m)
    return mods


# ---------------------------------------------------------------------------------------------- toc
BARE = re.compile(r'^(第[一二三四五六七八九十百\d]+[a-z]?[节款条]|§\s*\d+|[一二三四五六七八九十]+|\d+|[（(][一二三四五六七八九十\d]+[)）])$')


def make_toc(mods, title='目　录'):
    """Contents: work / section dividers (bold), the modules under them (indented), and the headings of rank 2/3 inside."""
    from .model import run as R
    blocks = [dict(k='h', style='tochead', rank=1, runs=[R(title)], id='toc')]
    under = False
    for mod in mods:
        if mod.mid == 'toc':
            continue
        if mod.kind == 'page':
            if mod.toc and mod.toc_title:
                under = mod.mid != 'plates'
                blocks.append(dict(k='p', style='toc0', runs=[R(mod.toc_title, h=mod.mid)], h=mod.mid, toc_ref=(mod.mid, None)))
                if mod.mid == 'plates':
                    under = False
            continue
        if not mod.toc:
            continue
        ind = 'i' if under else ''
        label = mod.toc_title or mod.title
        if mod.toc_level == 1:
            blocks.append(dict(k='p', style='toc1' + ind, runs=[R(label, h=mod.mid)], h=mod.mid, toc_ref=(mod.mid, None)))
        else:
            blocks.append(dict(k='p', style='toc2' + ind, runs=[R(label, h=mod.mid)], h=mod.mid, toc_ref=(mod.mid, None)))
            continue
        cand = []
        for bi, b in enumerate(mod.blocks):
            if b['k'] != 'h' or bi == 0 or b.get('notoc'):
                continue
            t = title_text(b['runs'])
            if b['rank'] in (1, 2, 3) and not BARE.match(t.replace('\u3000', '').replace(' ', '')):
                cand.append((bi, b, t))
        if len(cand) > 45:
            cand = [c for c in cand if c[1]['rank'] <= 2]
        if len(cand) > 45:
            cand = [c for c in cand if c[1]['rank'] <= 1]
        mod.toc_heads = [(bi, b['rank']) for bi, b, t in cand]
        for bi, b, t in cand:
            if not b.get('id'):
                b['id'] = f'{mod.mid}#h{bi}'
            st = 'toc1' + ind if b['rank'] == 1 else f'toc{b["rank"]}{ind}'
            blocks.append(dict(k='p', style=st, runs=[R(t, h=b['id'])], h=b['id'], toc_ref=(mod.mid, bi)))
    return blocks


# ---------------------------------------------------------------------------------------------- book
def title_of_unit(blocks):
    for b in blocks:
        if b['k'] == 'h':
            return title_text(b['runs'])
    return ''


def divider_page(u, v, k):
    hs = [b for b in u['els'] if b['k'] == 'h']
    lines = []
    for b in u['els']:
        t = plain_of(b)
        if b['k'] == 'h':
            lines.append((b['lvl'] if b['lvl'] < 6.5 else 99, t))
        else:
            lines.append((99, t))
    mid = f'div{u["parts"][0]}'
    title = lines[0][1] if lines else ''
    m = page_module(mid, 'body', special.divider_html(lines), toc=True, toc_title=title_text(hs[0]['runs']) if hs else title,
                    toc_level=0, title=title, folio=False, head=False)
    m.lines = [t for _, t in lines]
    m.src_parts = u['parts']
    return m


def book(v):
    KT.set_volume(v)
    fp = KS.front_parts(v)
    m = meta(v)
    units = KS.volume_units(v)
    figs = collect_figs(units)
    fig_index = {}
    fig_list = []

    def fig_no(src):
        # every occurrence gets its own plate (an image used twice in a volume is shown twice)
        fig_list.append(src)
        return len(fig_list)

    mods = [page_module('cover', 'cover', special.cover_html(COVERS[v]), folio=False),
            page_module('halftitle', 'front', special.half_title_html(TITLES[v]), folio=False),
            page_module('title', 'front', special.title_html(m), folio=False),
            copyright_module(v)]
    (pm, pn), (fm, fn) = front_text_module(v, 'preface'), front_text_module(v, 'foreword')
    front = [pm, fm]
    fgroups = [(pm.title, pn), (fm.title, fn)]
    fgroups = [g for g in fgroups if g[1]]
    if fgroups:
        fnm = notes_module('notes0', fgroups)
        fnm.zone = 'front'
        front.append(fnm)
    body = []
    pend, pend_chars = [], 0
    nk = 0
    used_mids = set()

    def flush():
        nonlocal pend, pend_chars, nk
        if pend:
            nk += 1
            body.append(notes_module(f'notes{nk}', pend))
            pend, pend_chars = [], 0

    for ui, u in enumerate(units):
        if u['kind'] == 'divider':
            flush()
            body.append(divider_page(u, v, ui))
            continue
        els = fig_paragraphs(u['els'], fig_no, f'u{ui}')
        u2 = dict(u, els=els)
        blocks = KS.unit_blocks(u2, v)
        blocks = wrap_lines(finish_blocks(blocks))
        blocks = balance_headings(blocks)
        mid = P(u['parts'][0])
        if mid in used_mids:
            mid += f'x{ui}'
        used_mids.add(mid)
        mod = Mod(mid=mid, zone='body', title=title_of_unit(blocks) or mid, blocks=blocks, toc_level=1)
        mod.src_parts = u['parts']
        body.append(mod)
        if u['notes']:
            nb = sum(len(runs_text(i['runs'])) for _, items in u['notes'] for i in items)
            pend.append((mod.title, [it for _, items in u['notes'] for it in items]))
            pend_chars += nb
        nxt_div = ui + 1 >= len(units) or units[ui + 1]['kind'] == 'divider'
        if pend and (pend_chars >= NOTE_MIN or nxt_div):
            flush()
    flush()
    plates = plate_modules(v, fig_list, '')
    allm = front + body + plates
    toc = Mod(mid='toc', zone='front', title='目录', blocks=make_toc(allm), toc=False, head=True)
    toc.tail_min = 5                     # a table of contents does not end on a page holding one or two entries
    mods += [toc] + allm
    return dict(id=f'k{v}', title=TITLES[v], meta=m, modules=mods, toc=toc, vol=v)
