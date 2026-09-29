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
    blocks = normalize.finish_headings(blocks)
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
            blocks.append(dict(k='img', style='center', runs=[], src=IMG(src), w=62, h=77, n=5))
            continue
        if not runs:
            blocks.append(dict(k='space', style='left', runs=[], n=1))
            continue
        txt = ''.join(r['t'] for r in runs)
        st = 'noindent' if len(txt) > 34 else 'left'
        blocks.append(dict(k='p', style=st, runs=runs, novary=True))
    # collapse runs of blank lines to at most two
    out = []
    for b in blocks:
        if b['k'] == 'space' and out and out[-1]['k'] == 'space':
            out[-1]['n'] = min(out[-1]['n'] + 1, 2)
        else:
            out.append(b)
    return Mod(mid=mid or part, zone='front', title='版权页', blocks=out, toc=False, head=False, folio=False, single=True)


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
        b['runs'] = normalize.replace_greek(b['runs'])
        blocks.append(b)
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
