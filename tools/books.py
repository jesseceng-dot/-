"""Book configurations: which parts form which module, in which zone, with which fixes."""
import re
from . import extract, normalize, special, style
from .book import Mod, title_text
from .model import run, merge_runs, BR
from .extract import ln, inline_runs, clean_runs, load_body, anchor_key

IMG = special.img_url


def first_title(blocks):
    if blocks and blocks[0]['k'] == 'h':
        return title_text(blocks[0]['runs'])
    return ''


def text_module(part, book_id, zone, title=None, fixes=(), grid='body', **kw):
    blocks = normalize.process_part(part, book_id, fixes)
    blocks = normalize.mark_markers(blocks)
    blocks = normalize.finish_headings(blocks)
    blocks = normalize.postprocess(blocks)
    t = title or first_title(blocks)
    return Mod(mid=part, zone=zone, title=t, blocks=blocks, grid=grid, **kw)


def page_module(mid, zone, html, **kw):
    kw.setdefault('toc', False)
    kw.setdefault('head', False)
    return Mod(mid=mid, zone=zone, kind='page', html=html, **kw)


def copyright_module(part, book_id, mid=None):
    """Copyright / CIP page: keep every original line (full-width padding included), laid out as one page."""
    body = load_body(part)
    blocks = []
    for el in body:
        if not isinstance(el.tag, str) or ln(el) != 'p':
            continue
        runs = clean_runs(inline_runs(el, part))
        has_img = any(r.get('i') for r in runs)
        if has_img:
            src = [r['i'] for r in runs if r.get('i')][0]
            blocks.append(dict(k='img', style='cipc', runs=[], src=IMG(src), w=58, h=72, n=7))
            continue
        if not runs:
            blocks.append(dict(k='space', style='cip', runs=[], n=1))
            continue
        runs = [dict(runs[0], t=re.sub(r'^([\u4e00-\u9fff])\u3000+([\u4e00-\u9fff])(?=：)', '\\1\u3000\u3000\\2', runs[0]['t']))] + runs[1:]
        txt = ''.join(r['t'] for r in runs)
        st = 'cipj' if len(txt) > 40 else ('cipc' if re.match(r'(豆瓣|微信号|发邮件)', txt) else 'cip')
        blocks.append(dict(k='p', style=st, runs=runs, novary=True))
    # collapse runs of blank lines to at most two
    out = []
    for b in blocks:
        if b['k'] == 'space' and out and out[-1]['k'] == 'space':
            out[-1]['n'] = min(out[-1]['n'] + 1, 2)
        else:
            out.append(b)
    return Mod(mid=mid or part, zone='front', title='版权页', blocks=out, grid='small1', toc=False, head=False, folio=False, single=True)


def index_module(part, book_id, zone, fixes=(), title=None):
    """Index: title, optional intro line, letter/stroke headings and hanging entries in the small grid."""
    raw = extract.parse_part(part)
    blocks = []
    for i, b in enumerate(raw):
        b = dict(b)
        t = normalize.text_of(b)
        if b['k'] == 'h':
            b = normalize.to_heading(b, 1)
        elif b['style'] == 'center' and len(t) <= 3:
            b['style'] = 'idxhead'
        elif b['style'] in ('noindent',) and len(t) <= 8 and 'b' in ''.join('b' if r.get('b') else '' for r in b['runs']):
            b['style'] = 'idxhead'
        elif b['style'] == 'body' and re.fullmatch(r'[一二三四五六七八九十]+画|[A-Za-z]', t):
            b['style'] = 'idxhead'
        elif b['style'] in ('body', 'noindent', 'right', 'quote'):
            b['style'] = 'index'
            if i == 1 and len(t) > 30 and '。' in t:
                b['style'] = 'idxnote'
            elif t.startswith('——'):
                b['style'] = 'indexc'
        b['runs'] = normalize.replace_greek(b['runs'])
        blocks.append(b)
    blocks = normalize.mark_markers(blocks)
    blocks = normalize.apply_fixes(blocks, fixes)
    t = title or first_title(blocks)
    return Mod(mid=part, zone=zone, title=t, blocks=blocks, grid='small1')


def notes_module(part, book_id, zone, title='注　释', mid=None):
    """Endnotes: number column (a back-link to the marker) + text, small grid."""
    body = load_body(part)
    blocks = [dict(k='h', style='h1', rank=1, runs=[run(title)], id=(mid or part) + '#top')]
    for el in body:
        if not isinstance(el.tag, str):
            continue
        runs = clean_runs(inline_runs(el, part))
        if not runs:
            continue
        first = runs[0]
        if first.get('a') and re.match(r'^[\[［]\d+[\]］]$', first['t']):
            first = dict(first, c='nn')
            runs = [first] + runs[1:]
        blocks.append(dict(k='p', style='note', runs=normalize.replace_greek(runs)))
    return Mod(mid=mid or part, zone=zone, title=title.replace('　', ''), blocks=blocks, grid='small1')


def toc_mod(mods, title='目　录'):
    from .book import make_toc
    return Mod(mid='toc', zone='front', title='目录', blocks=make_toc(mods, title), toc=False, head=True)


# ------------------------------------------------------------------------------------------------ Book 1
def book1():
    P = lambda n: f'part{n:04d}'
    meta = dict(title='小逻辑', author='〔德〕黑格尔 著', credits=['贺　麟　译'], series='贺麟全集',
                publisher='上海人民出版社')
    mods = [
        page_module('cover', 'cover', special.cover_html('image01995.jpeg'), folio=False),
        page_module('halftitle', 'front', special.half_title_html('小逻辑'), folio=False),
        page_module('title', 'front', special.title_html(meta), folio=False),
        copyright_module(P(2), 'b1'),
    ]
    front = [(3, {}), (4, {}), (5, {}), (6, {}), (7, {}), (8, {}), (9, {}), (10, {})]
    body = [11, 12, 13, 14, 15]
    body_mods = []
    front_mods = [text_module(P(n), 'b1', 'front', **kw) for n, kw in front]
    body_mods = [text_module(P(n), 'b1', 'body') for n in body]
    back = [index_module(P(16), 'b1', 'back'), index_module(P(17), 'b1', 'back'),
            notes_module(P(18), 'b1', 'back')]
    toc = toc_mod(front_mods + body_mods + back)
    mods = mods + [toc] + front_mods + body_mods + back
    return dict(id='b1', title='小逻辑', meta=meta, modules=mods, toc=toc)


# ------------------------------------------------------------------------------------------------ shared helpers
def chapter(part, book_id, zone, fixes=(), ranks=(), notes=True, toc_level=1, title=None, styles=(), **kw):
    """A text module plus (optionally) the endnotes that the source file carries after the chapter text."""
    blocks = normalize.process_part(part, book_id, fixes, ranks=ranks, styles=styles)
    blocks = normalize.mark_markers(blocks)
    main, raw = normalize.split_notes(blocks) if notes else (blocks, [])
    main = normalize.postprocess(normalize.finish_headings(main))
    t = title or first_title(main)
    mods = [Mod(mid=part, zone=zone, title=t, blocks=main, toc_level=toc_level, **kw)]
    if raw:
        nb = normalize.note_blocks(normalize.repair_note_links(raw, part))
        nb = [dict(k='h', style='h1', rank=1, runs=[run('注　释')], id=part + 'n#top')] + nb
        mods.append(Mod(mid=part + 'n', zone=zone, title=t + '·注释', toc_title='注释', blocks=nb, grid='small1',
                        toc_level=2))
    return mods


def colophon_module(part, zone, mid=None):
    body = load_body(part)
    blocks = []
    for el in body:
        if not isinstance(el.tag, str) or ln(el) != 'p':
            continue
        runs = clean_runs(inline_runs(el, part))
        if runs:
            blocks.append(dict(k='p', style='cipc', runs=normalize.replace_greek(runs), novary=True))
    blocks = [dict(k='space', style='cipc', runs=[], n=24)] + blocks
    return Mod(mid=mid or part, zone=zone, title='版本说明', blocks=blocks, grid='small1', toc=False, head=False,
               folio=False, single=True)


def ads_module(mid, zone, part):
    import html as _h
    s = open(extract.os.path.join(extract.TEXT_DIR, part + '.xhtml'), encoding='utf8').read()
    urls = [_h.unescape(u) for u in re.findall(r'href="(http[^"]*)"', s)]
    imgs = ['image02004.jpeg', 'image02005.jpeg', 'image02006.jpeg', 'image02007.jpeg', 'image02008.jpeg', 'image02009.jpeg']
    caps = ['小逻辑', '伦理学·知性改进论', '文化与人生', '哲学史演讲录', '马克思博士论文\n黑格尔辩证法和哲学一般的批判', '黑格尔·黑格尔学述']
    items = list(zip(imgs, [c.replace('\n', '') for c in caps], urls))
    return page_module(mid, zone, special.ads_html(items), folio=False, head=False)


def book_meta_mods(cover, meta, mid_prefix):
    return [
        page_module(mid_prefix + 'cover', 'cover', special.cover_html(cover), folio=False),
        page_module(mid_prefix + 'halftitle', 'front', special.half_title_html(meta['title']), folio=False),
        page_module(mid_prefix + 'title', 'front', special.title_html(meta), folio=False),
    ]


# ------------------------------------------------------------------------------------------------ Book 2
def book2():
    P = lambda n: f'part{n:04d}'
    meta = dict(title='黑格尔早期神学著作', author='〔德〕黑格尔 著', credits=['贺　麟　译'], series='贺麟全集',
                publisher='上海人民出版社')
    head = book_meta_mods('image02003.jpeg', meta, 'b2') + [copyright_module(P(20), 'b2')]
    front = [text_module(P(21), 'b2', 'front', fixes=[('style', 1, 'right')]),
             text_module(P(22), 'b2', 'front'),
             text_module(P(23), 'b2', 'front')]
    body = []
    body += chapter(P(24), 'b2', 'body',
                    fixes=[('rank', 21, 3), ('rank', 121, 3), ('style', (152, 153), 'quote')],
                    ranks=[(r'^[ⅠⅡⅢⅣⅤ]$', 4)])
    body += chapter(P(25), 'b2', 'body')
    body += chapter(P(26), 'b2', 'body',
                    fixes=[('rank', 241, 4), ('rank', 269, 2), ('style', (69, 70), 'quote'), ('style', (200, 201), 'quote'),
                           ('style', (290, 297), 'quote')])
    body += chapter(P(27), 'b2', 'body', fixes=[('join', 44, 45, ''), ('join', 73, 74, '')])
    body += chapter(P(28), 'b2', 'body', fixes=[('style', (6, 7), 'quote')])
    back = chapter(P(29), 'b2', 'back',
                   ranks=[(r'^A[.．]', 2), (r'^[一二三四五六七八九十]+$', 3), (r'^[BCD][.．][^。，；：]{1,8}$', 4)],
                   fixes=[('rank', 72, 3), ('gap', 72), ('rank', 94, 3), ('gap', 94), ('rank', 116, 3), ('gap', 116),
                          ('rank', 123, 3), ('gap', 123), ('rank', 131, 3), ('gap', 131), ('rank', 139, 3), ('gap', 139)])
    back += [colophon_module(P(30), 'back'), ads_module('b2ads', 'back', P(31))]
    allm = front + body + back
    toc = toc_mod(allm)
    return dict(id='b2', title='黑格尔早期神学著作', meta=meta, modules=head + [toc] + allm, toc=toc)


GAP = '　'


# ------------------------------------------------------------------------------------------------ plates
def plate_modules(part, book_id, zone, images, heading_fix=(), toc_title='页码对照表'):
    """The section that used to carry big images/tables: heading + blue 'see plate N' links (same page),
    plus one back-of-book plate page per image (image scaled to the text block, return link at the bottom)."""
    raw = extract.parse_part(part)
    head = [b for b in raw if b['k'] == 'h'][0]
    head = normalize.to_heading(head, 1)
    runs = []
    n = len(images)
    for k in range(1, n + 1):
        if runs:
            runs.append(run('　' if (k - 1) % 3 else '\n'))
        runs.append(run(f'见书后插图{k}', h=f'plate-{k}', a=f'figref-{k}', c='fig'))
    blocks = normalize.finish_headings([head]) + [dict(k='p', style='center', runs=runs, novary=True, nosplit=True, before=2)]
    sec = Mod(mid=part, zone=zone, title=first_title(blocks), blocks=blocks)
    mods = []
    divider = page_module(part + 'plates', zone,
                          special.plate_divider_html('书后插图', '本书正文中的大幅插图与表格一律集中排在此处，每页一图；正文中以蓝色“见书后插图N”标示，点击可跳转，各页底部附返回链接。'),
                          toc=True, toc_title='书后插图', toc_level=1, title='书后插图', folio=True)
    mods.append(divider)
    for k, img in enumerate(images, 1):
        def html(bb, page, k=k, img=img):
            return special.plate_html(k, img, f'figref-{k}', f'插图 {k}　{toc_title}', bb, page)
        m = page_module(f'plate-{k}', zone, html, toc=True, toc_title=f'插图{k}', toc_level=2, title=f'插图{k}', folio=True)
        m.anchor = f'plate-{k}'
        mods.append(m)
    return sec, mods


def volume_page(mid, zone, title, vol, volume_label):
    return page_module(mid, zone, special.volume_title_html(title, vol), folio=False, toc=False, toc_title=vol,
                       title=vol, volume=volume_label)


# ------------------------------------------------------------------------------------------------ Book 3
def book3():
    P = lambda n: f'part{n:04d}'
    meta = dict(title='精神现象学', author='〔德〕黑格尔 著', credits=['贺　麟　王玖兴　译'], series='贺麟全集',
                publisher='上海人民出版社')
    head = book_meta_mods('image02010.jpeg', meta, 'b3') + [copyright_module(P(33), 'b3')]
    up_front = [text_module(P(34), 'b3', 'front', fixes=[('drop', 0)]),
                text_module(P(35), 'b3', 'front'),
                text_module(P(36), 'b3', 'front')]
    up_body = [text_module(P(n), 'b3', 'body') for n in (37, 38, 39, 40, 41)]
    up_back = [text_module(P(42), 'b3', 'body'), text_module(P(43), 'b3', 'body')]
    dn_front = [text_module(P(44), 'b3', 'body', fixes=[('drop', 0)])]
    dn_body = [text_module(P(n), 'b3', 'body') for n in (45, 46, 47)]
    dn_back = [index_module(P(48), 'b3', 'body'), index_module(P(49), 'b3', 'body')]
    sec, plates = plate_modules(P(50), 'b3', 'body', [f'image{n:05d}.jpeg' for n in range(2011, 2020)])
    dn_back += [sec, text_module(P(51), 'b3', 'body'), notes_module(P(52), 'b3', 'body')]
    dn_back += plates
    v1 = volume_page('b3v1', 'front', '精神现象学', '上卷', '上卷')
    v2 = volume_page('b3v2', 'body', '精神现象学', '下卷', '下卷')
    for m in up_front + up_body + up_back:
        m.volume = '上卷'
    for m in dn_front + dn_body + dn_back:
        m.volume = '下卷'
    allm = [v1] + up_front + up_body + up_back + [v2] + dn_front + dn_body + dn_back
    toc = toc_mod(allm)
    return dict(id='b3', title='精神现象学', meta=meta, modules=head + [toc] + allm, toc=toc)


# ------------------------------------------------------------------------------------------------ Book 4
def idxs(part, pat, maxlen=80):
    bl = extract.parse_part(part)
    return [i for i, b in enumerate(bl) if re.search(pat, normalize.text_of(b)) and len(normalize.text_of(b)) <= maxlen]


def book4():
    P = lambda n: f'part{n:04d}'
    meta = dict(title='哲学史讲演录', author='〔德〕黑格尔 著', credits=['贺　麟　王太庆　译'], series='贺麟全集',
                publisher='上海人民出版社')
    head = book_meta_mods('image02020.jpeg', meta, 'b4') + [copyright_module(P(54), 'b4')]
    vols = []

    def vol(label, mid, front, body, back):
        for m in front + body + back:
            m.volume = label
        return [volume_page(mid, 'body' if mid != 'b4v1' else 'front', '哲学史讲演录', label, label)] + front + body + back

    B4 = 'b4'
    # ---- volume 1
    f1 = [text_module(P(55), B4, 'front', fixes=[('drop', 0), ('style', 2, 'right')]),
          text_module(P(56), B4, 'front')]
    f1 += chapter(P(57), B4, 'front', fixes=[('style', 1, 'center'), ('style', 2, 'noindent')])
    f1 += [text_module(P(58), B4, 'front')]
    b1 = []
    b1 += chapter(P(59), B4, 'body')
    b1 += chapter(P(60), B4, 'body', fixes=[('style', 73, 'body'), ('merge', 85, 86)])
    b1 += chapter(P(61), B4, 'body')
    b1 += chapter(P(62), B4, 'body')
    v63 = []
    for lo, hi in ((143, 146), (148, 151), (198, 201), (221, 224), (330, 332)):
        v63 += [('style', (lo, hi), 'verse'), ('set', (lo, hi), {'left': 2})]
    b1 += chapter(P(63), B4, 'body', fixes=[('style', idxs(P(63), r'^\u3000+\d+'), 'quote'), ('lstrip', idxs(P(63), r'^\u3000+\d+'))] + v63)
    k1 = [index_module(P(65), B4, 'body'), text_module(P(66), B4, 'body')]
    # ---- volume 2
    f2 = [text_module(P(67), B4, 'body', fixes=[('drop', 0)])]
    b2 = (chapter(P(68), B4, 'body', fixes=[('style', (150, 151), 'verse'), ('set', (150, 151), {'left': 2})]) +
          chapter(P(69), B4, 'body', fixes=[('style', (8, 11), 'verse')]))
    k2 = [index_module(P(70), B4, 'body'), text_module(P(71), B4, 'body')]
    # ---- volume 3
    f3 = [text_module(P(72), B4, 'body', fixes=[('drop', 0)])]
    b3 = []
    for n in (73, 74, 75, 76, 77, 78):
        b3 += chapter(P(n), B4, 'body')
    k3 = [index_module(P(79), B4, 'body'), text_module(P(80), B4, 'body')]
    # ---- volume 4
    f4 = [text_module(P(81), B4, 'body', fixes=[('drop', 0)])]
    b4 = []
    b4 += chapter(P(82), B4, 'body')
    b4 += chapter(P(83), B4, 'body', fixes=[('style', [33, 36, 38], 'center')])
    b4 += chapter(P(84), B4, 'body', fixes=[('style', (177, 178), 'verse'), ('merge', 189, 190)])
    b4 += chapter(P(85), B4, 'body')
    b4 += chapter(P(86), B4, 'body', fixes=[('style', (210, 212), 'center')])
    b4 += chapter(P(87), B4, 'body', ranks=LETTER_RANKS, styles=LETTER_STYLES,
                  fixes=[('style', 4, 'right'), ('style', 163, 'right')])
    k4 = [index_module(P(88), B4, 'body'), index_module(P(89), B4, 'body'),
          text_module(P(90), B4, 'body', fixes=[('style', (7, 8), 'right')]),
          colophon_module(P(91), 'body'), ads_module('b4ads', 'body', P(92))]
    allm = (vol('第一卷', 'b4v1', f1, b1, k1) + vol('第二卷', 'b4v2', f2, b2, k2) +
            vol('第三卷', 'b4v3', f3, b3, k3) + vol('第四卷', 'b4v4', f4, b4, k4))
    toc = toc_mod(allm)
    return dict(id='b4', title='哲学史讲演录', meta=meta, modules=head + [toc] + allm, toc=toc)


LETTER_RANKS = [(r'^\d+\.\s*致', 3), (r'^[A-Z]\.', 9)]
LETTER_STYLES = [
    (r'^[〔]?\d{4}年.{0,14}[于日月底末〕]$', 'right'),
    (r'^\d{4}年\d+月\d+日于', 'right'),
    (r'^(爱尔拉赫附近树格村)$', 'right'),
    (r'^(我的亲爱的！|尊敬的先生和朋友！|尊敬的阁下：|我最亲爱的老朋友！|最敬爱的朋友!)$', 'noindent'),
    (r'^〔摘要〕$', 'center'),
    (r'^(黑格尔关于哲学史书信十六封|苗力田　选译)$', 'center'),
]
