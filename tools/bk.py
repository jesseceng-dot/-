"""四本书的模块配置：巴菲特致股东的信·投资原则篇 / 财富、贫穷与政治 / 工作、消费主义和新穷人 / 股票大作手回忆录。

`book(b)` 返回 build.build 需要的 cfg（同黑格尔、康德、杜威各册）；页面为 16 开（BOOK_GEOM=k16）。
四本书各有一个工作目录（BOOK_SCRATCH），bk_make_all.py 逐本设置。
"""
import math
import os
import re
import shutil
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
    # ---- books 5-10: two EPUBs (5, 6) and four AZW3 (7-10)
    5: dict(scratch='q5', file='叫魂', title='叫魂', sub='1768年中国妖术大恐慌', author='〔美〕孔飞力 著', credits=['陈兼　刘昶　译'],
            publisher='上海三联书店', pdf_author='〔美〕孔飞力', cover='cover.jpg', cover_file='source/covers/05-叫魂.png', title_img=None, copyright=None, marker='sq', renum=True,
            head_clean=True, merge_dash_head=True, cls_cap=('caption',), cls_right=('year', 'year1', 'year2'), cls_quote=('call',),
            img_text={'char01.png': '饘'},
            front=[(2, 'text'), (3, 'text')],
            body=[[4, 5, 6, 7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18, 19], [20, 21, 22, 23], [24, 25, 26, 27],
                  [28, 29, 30, 31, 32, 33], [34, 35, 36, 37, 38, 39], [40, 41, 42, 43, 44, 45, 46, 47], [48, 49, 50, 51, 52]],
            back=[53, 54, 55, 56], tail=[], inplace=set()),
    6: dict(scratch='q6', file='狂热分子', title='狂热分子', sub='码头工人哲学家的沉思录', author='〔美〕埃里克·霍弗 著', credits=['梁永安　译'],
            publisher='广西师范大学出版社', pdf_author='〔美〕埃里克·霍弗', cover='cover1.jpeg', cover_file='source/covers/06-狂热分子.png', title_img=None, copyright=50, marker='sq',
            head_clean=True, merge_dash_head=True, strip_indent=True, skip_text=('【注释】',), renum=True,
            head_cls={'prefacetitle': 1, 'h2sub': 1}, head_sub=[(r'^0*(\d{1,3})(?=\D)', '\\1　')],
            cls_quote=('editornote',), cls_right=('signature', 'author'),
            part_split=r'^(第[一二三四五六七八九十]+部分)[\s　]*(.*)$', part_sub_cls=('h1note',),
            front=[(2, 'dedication'), (3, 'dedication'), (4, 'text'), (6, 'text'), (7, 'text')],
            body=[8, [9, 10], [11, 12], [13, 14], 15, [16, 17], [18, 19], [20, 21], [22, 23], [24, 25], [26, 27], [28, 29], [30, 31],
                  32, [33, 34], [35, 36], [37, 38], 39, [40, 41], [42, 43], [44, 45], [46, 47]],
            back=[(48, 'noindent')], tail=[], backcover='00001.jpeg', inplace=set()),
    7: dict(scratch='q7', file='漫步华尔街', title='漫步华尔街', sub='（原书第12版）', author='〔美〕伯顿·G.马尔基尔 著', credits=['张　伟　译'],
            publisher='机械工业出版社', pdf_author='〔美〕伯顿·G.马尔基尔', cover='cover00359.jpeg', title_img=None, copyright=0, copyright_skip=5,
            marker='sq', renum=True, img_text={'image00280.jpeg': ('R', 'it ov'), 'image00281.jpeg': ('U', 'it ov')},
            head_cls={'p6': (5, r'^\d+[.．]\s')}, cls_cap=('middle-img',), cls_right=('you1',), cls_quote=('ziti1',),
            cls_center=('p6',), cap_mode='tabfig', cap_after_re=r'^(①|②|③|资料来源|数据来源|注[：:])', label_re=r'^([图表][^\s　]+)',
            part_re=r'^第[一二三四]部分', part_split=r'^(第[一二三四]部分)[\s　]*(.*)$',
            front=[(2, 'text'), (3, 'dedication'), (4, 'text'), (5, 'text')],
            body=[list(range(6, 13)), list(range(13, 18)), list(range(18, 24)), list(range(24, 29)), list(range(29, 39)),
                  list(range(39, 47)), list(range(47, 53)), list(range(53, 59)), list(range(59, 67)), list(range(67, 73)),
                  list(range(73, 80)), list(range(80, 92)), list(range(92, 97)), list(range(97, 105)), list(range(105, 112))],
            back=[112, 113, 114, 115], tail=[], inplace=set()),
    8: dict(scratch='q8', file='失控', title='失控', sub='机器、社会与经济的新生物学', author='〔美〕凯文·凯利 著',
            credits=['陈新武　陈之宇　顾珮嵚　郝宜平', '卢蔚然　陆丁　王钦　小青', '袁璐　张鹃　张行舟　译', '赵嘉敏　审校'],
            publisher='新星出版社', pdf_author='〔美〕凯文·凯利', cover='cover00466.jpeg', title_img=None, copyright=2, marker='sq',
            head_clean=True, table_head=False, head_cls={'title1': 1, 'title2': 2}, head_keep={'title1': 'middle'},
            cls_right=('normaltext1',), cls_quote=('normaltext2',), cls_center=('title5', 'subtitle1'), cls_refhead=('subtitle2',),
            skip_text=('注释',), img_text={'image00464.jpeg': '‰'}, img_max_scale=0.6,
            orn={f'image{n:05d}.jpeg' for n in range(442, 466) if n != 464}, orn_size=(38.0, 38.0),
            front=[(3, 'text'), (4, 'text'), (5, 'dedication'), (6, 'text')], body=list(range(7, 31)),
            back=[31, 32, 33, 34], tail=[], inplace={'image00441.jpeg'}),
    9: dict(scratch='q9', file='血酬定律', title='血酬定律', sub='中国历史中的生存游戏', author='吴思 著', credits=[],
            publisher='', pdf_author='吴思', cover='cover00255.jpeg', cover_file='source/covers/09-血酬定律.png', title_img='image00191.jpeg', copyright_img='image00192.jpeg',
            marker='sq', note_by_marker=True, head_clean=True, strip_indent=True, head_sub=[(r'^\[\s*', '【')],
            part_re=r'^【[正杂]编】', part_split=r'^【([正杂]编)】()$',
            front=[(3, 'text'), (4, 'text')], body=list(range(5, 24)), back=[24, 25], endnotes=[26], endnotes_title='脚注',
            tail=[], inplace=set()),
    10: dict(scratch='q10', file='政治学通识', title='政治学通识', sub='', author='包刚升 著', credits=[],
             publisher='北京大学出版社', pdf_author='包刚升', cover='cover00344.jpeg', title_img=None, copyright=1, marker='sq',
             note_by_marker=True, head_clean=True, cls_quote=('kindle-cn-ref',), cls_right=('kindle-cn-signature',),
             cap_mode='tabfig', cap_after_re=r'^(备注|资料来源|注[：:]|数据来源)', label_re=r'^([图表][^\s　]+)',
             img_para={'image00316.jpeg': [
                 [run('N', c='it'), run('v', c='it msub'), run(' = 1 / Σ'), run('V', c='it'), run('i', c='it msub'), run('2', c='msup')],
                 [run('N', c='it'), run('s', c='it msub'), run(' = 1 / Σ'), run('S', c='it'), run('i', c='it msub'), run('2', c='msup')]]},
             front=[(2, 'kaibody')], body=list(range(3, 17)), back=[17], tail=[], inplace=set()),
    # ---- books 11-15: proof-read (corrections in bk_fixes.py), three AZW3 (11, 13, 14) and two EPUBs (12, 15)
    11: dict(scratch='q11', exp_sup=True, file='大国政治的悲剧', title='大国政治的悲剧', sub='（修订版）', author='〔美〕约翰·米尔斯海默 著',
             credits=['王义桅　唐小松　译'], publisher='上海人民出版社', pdf_author='〔美〕约翰·米尔斯海默', series='东方编译所译丛',
             cover='cover00437.jpeg', title_img=None, copyright=0, marker='sqcirc', note_cls=('kindle-cn-footnote',), head_clean=True,
             head_sub=[(r'^附[\s\u3000]*录[\s\u3000]*', '附录\u3000')], cls_cap=('kindle-cn-caption', 'kindle-cn-caption1'),
             cap_mode='tabfig', cap_after_re=r'^(注[：:]|资料来源)', label_re=r'^([图表][^\s　]+)', cls_hang=('kindle-cn-para-hang',),
             join_cont=r'（续表）', img_max_scale=0.3,
             front=[(1, 'kaibody'), (2, 'kaibody'), (3, 'kaibody'), (4, 'kaibody'), (5, 'kaibody')], body=list(range(7, 17)), back=[17, 18],
             tail=[], inplace={'image00403.jpeg'}),
    12: dict(scratch='q12', exp_sup=True, file='法律的概念', title='法律的概念', sub='（增訂三版）', author='H. L. A. 哈特 著',
             credits=['許家馨　李冠宜　譯'], publisher='商周出版', pdf_author='H. L. A. 哈特', cover='cover.jpg', title_img=None,
             copyright=None, marker='zhu', tc=True, cjk='TC', notes_title='註　釋', notes_toc='註釋', pgno_cls=('ta_c',),
             head_clean=True, head_demote={'李冠宜、許家馨': 'right'},
             front=[(1, 'text'), (2, 'text'), (3, 'text'), (4, 'text'), (5, 'text'), (list(range(6, 13)), 'text')],
             body=[list(range(13, 17)), list(range(17, 20)), list(range(20, 24)), list(range(24, 29)), list(range(29, 33)),
                   list(range(33, 37)), list(range(37, 42)), list(range(42, 46)), list(range(46, 50)), list(range(50, 56)),
                   list(range(56, 63))],
             back=[63, 64, 65], tail=[], inplace=set()),
    13: dict(scratch='q13', exp_sup=True, file='公正：该如何做是好？', title='公正', sub='该如何做是好？', author='〔美〕迈克尔·桑德尔 著',
             credits=['朱慧玲　译'], publisher='中信出版社', pdf_author='〔美〕迈克尔·桑德尔', cover='cover00199.jpeg', title_img=None,
             copyright=1, marker='keep', head_clean=True, head_split='／', front=[], body=list(range(3, 13)), back=[13], tail=[], inplace=set()),
    14: dict(scratch='q14', exp_sup=True, file='牛津通识读本：气候', title='气候', sub='', series='牛津通识读本', author='〔英〕马克·马斯林 著',
             credits=['朱邦芊　译'], publisher='译林出版社', pdf_author='〔英〕马克·马斯林', cover='cover00119.jpeg', title_img=None,
             copyright=1, marker='sq', head_cls={'heiti': 2, 'xiaobiao': 3}, cls_cap=('tuzhu-center',), cls_right=('bodytext-right',),
             front=[(3, 'text'), (4, 'text')], body=list(range(5, 15)), back=[], endnotes=[15], endnotes_title='注释',
             tail=[], inplace=set()),
    15: dict(scratch='q15', exp_sup=True, file='气候赌场', title='气候赌场', sub='全球变暖的风险、不确定性与经济学', author='〔美〕威廉·诺德豪斯 著',
             credits=['梁小民　译'], publisher='东方出版中心', pdf_author='〔美〕威廉·诺德豪斯', series='威廉·诺德豪斯著作系列',
             cover='image00246.jpeg', title_img=None, copyright=2, marker='paren', head_clean=True,
             head_sub=[(r'^(第\d+章)[|｜]?[\s\u3000]*', '\\1\u3000')], note_cls=('fnContent-1', 'fnContent-2'),
             cls_cap=('tuti', 'tuzhu', 'biaoti'), cap_mode='tabfig', label_re=r'^([图表][^\s　]+)',
             cls_right=('signContent-1-kaiti',), cls_quote=('bodyContent-2-kaiti', 'bodyContent-2-kaiti-top'),
             part_re=r'^PART', part_split=r'^(PART \d+) ([^A-Za-z]+?) ([A-Z].*)$',
             part_epi_cls=('bodyContent-1-kaiti', 'signContent-1-kaiti', 'bodyContent-1'),
             front=[(3, 'text'), (4, 'text'), (5, 'dedication'), (6, 'text'), (7, 'text'), (8, 'text')],
             body=[[10, 11]] + list(range(12, 17)) + [[17, 18]] + list(range(19, 26)) + [[26, 27]] + list(range(28, 32)) + [[32, 33]]
                  + list(range(34, 41)) + [[41, 42]] + list(range(43, 46)),
             back=[], tail=[], inplace=set()),
}
FILES = {b: f'{b:02d}-{CFG[b]["file"]}.pdf' for b in CFG}
TITLES = {b: CFG[b]['file'] for b in CFG}


def meta(b):
    C = CFG[b]
    return dict(title=C['title'], sub=C['sub'], author=C['author'], credits=C['credits'], series=C.get('series', ''),
                publisher=C['publisher'], subject=C['file'])


# ---------------------------------------------------------------------------------------------- headings
CN = '一二三四五六七八九十百'
ORD_ONLY = re.compile(r'^第[%s\d]+[部章节篇讲]分?$' % CN)
BARE = re.compile(r'^(第[%s\d]+[部章节篇讲]分?|§\s*\d+[.．]?|[%s]+|\d+[.．]?|[IVX]+[.．]?)$' % (CN, CN))
NUM_PATTERNS = [
    (re.compile(r'^(第[%s\d]+[部章节篇讲]分?)(?![的分])[\s　 ]*(?=\S)' % CN), '　'),
    (re.compile(r'^(附录[%sA-Z]+)[\s　 ]*(?=\S)' % CN), '　'),
    (re.compile(r'^([一二三四五六七八九十]+)[\s　 ]+(?=\S)'), '　'),
    (re.compile(r'^(§\s*\d+[.．])[\s　]*(?=\S)'), ' '),
    (re.compile(r'^(\d+[.．])[\s　]*(?=\S)'), ' '),
]
NUM_PATTERNS.insert(3, (re.compile(r'^(\d+(?:\.\d+)+)[\s\u3000\xa0]*(?=\S)'), '\u3000'))       # '1.1　Title' (before the plain '1. Title' rule)
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


def _cs(C, key):
    return set(C.get(key, ()))


def _img_text(C, runs):
    """Inline images: those with a transcription (C['img_text']) become text, all others are dropped."""
    m = C.get('img_text')
    if m is None or not any(r.get('i') for r in runs):
        return runs
    def sub(r):
        v = m[r['i']]
        t, c = v if isinstance(v, tuple) else (v, '')                  # text, or (text, run class)
        return dict({k: x for k, x in r.items() if k not in ('i', 'c')}, t=t, **({'c': c} if c else {}))
    return [sub(r) if r.get('i') else r for r in runs if not r.get('i') or r['i'] in m]


def exp_sup(runs):
    """A superscript without a link is an exponent (m², 10⁶), not a note mark: black raised digits."""
    return [dict({k: v for k, v in r.items() if k != 's'}, c=((r.get('c') or '') + ' msup').strip())
            if r.get('s') and not r.get('h') and not r.get('a') and not r.get('i') else r for r in runs]


def _head_runs(C, runs, keep=None):
    """Heading text of a source paragraph/heading: line breaks -> one space; `keep='middle'` keeps only the middle line of three."""
    if keep == 'middle':
        lines, cur = [[]], []
        for r in runs:
            if r['t'] in ('\n', '\u2028'):
                lines.append([])
            else:
                lines[-1].append(r)
        if len(lines) >= 3:
            runs = lines[1]
    merged = []
    for r in runs:                                                 # plain runs of a heading are one text (a page anchor may split them)
        if merged and not any(x.get(k) for x in (r, merged[-1]) for k in ('h', 's', 'i')) \
                and (r.get('c'), r.get('b')) == (merged[-1].get('c'), merged[-1].get('b')):
            merged[-1] = dict(merged[-1], t=merged[-1]['t'] + r['t'])
        else:
            merged.append(dict(r))
    runs = merged
    out = []
    for r in runs:
        if r['t'] in ('\n',):
            out.append(dict(r, t=' '))
        else:
            t = re.sub(r'(?<=[\u3400-\u9fff，：；、])\u2028(?=[\u3400-\u9fff“《（])', '', r['t'])   # a break inside a Chinese title
            out.append(dict(r, t=t.replace('\u2028', ' ').replace('\n', ' ')))
    return BT.fix_edges(merge_runs(out))


def elements(C, items, kaitext=False):
    """Items of one part -> (elements, note items).  Headings carry 'lvl'; figures are {'k': 'fig'}; captions style 'cap'."""
    els, notes = [], []
    gap_before = False
    head_cls = C.get('head_cls', {})
    pg_pend = []
    in_box = False
    for it in items:
        k = it['k']
        if k == 'p' and set(it['cls'].split()) & _cs(C, 'note_cls'):
            it = dict(it, k='note')                         # footnote paragraphs marked by their class
            k = 'note'
        if k == 'p' and set(it['cls'].split()) & _cs(C, 'pgno_cls') and re.fullmatch(r'[ivxlcdm]{1,8}|\d{1,4}', plain(it['runs'])):
            mk = run('〔%s〕' % plain(it['runs']), c='pgno')     # a page number of the original edition: small, at the end of its paragraph
            if els and els[-1]['k'] == 'p' and els[-1].get('style') not in ('cap',):
                els[-1]['runs'] = els[-1]['runs'] + [mk]
            else:
                pg_pend.append(mk)
            continue
        if k == 'p' and C.get('note_by_marker') and it['runs'] and it['runs'][0].get('h') and BT.marker_text(it['runs'][0]['t'], 'sq') \
                and len(it['runs']) > 1:
            it = dict(it, k='note')                         # a paragraph that starts with a linked note number is a note entry
            k = 'note'
        if k == 'note':
            if ''.join(r['t'] for r in it['runs']).strip('\u3000 ') in C.get('skip_text', ()):
                continue                                    # a 'notes' label that the ebook sets as a note entry
            notes.append(it)
            continue
        if k == 'img' and it['src'] in C.get('img_para', {}):
            for ln_ in C['img_para'][it['src']]:                 # a display formula set as an image: transcribed to centred text lines
                els.append(dict(k='p', style='center', runs=ln_, id='', src='img_para', nomerge=True, novary=True))
            continue
        if k == 'img':
            if it['src'] in C['tail']:
                continue                                    # the publisher's QR codes: kept as the last page of the book instead
            els.append(dict(k='orn' if (it.get('orn') or it['src'] in C.get('orn', ())) else 'fig', src=it['src']))
            continue
        if k == 'table':
            els.append(dict(k='table', rows=it['rows']))
            continue
        if k == 'p' and it.get('blank'):
            if els:
                gap_before = True                           # an empty paragraph = one blank line before the next paragraph
            continue
        runs = BT.fix_edges(BT.fix_runs(_img_text(C, it['runs'])))
        if C.get('exp_sup'):
            runs = exp_sup(runs)
        if not runs:
            continue
        cls = it['cls']
        if it.get('box') and not in_box:
            gap_before = True                                # a box (方框) starts: one blank line above it
        elif in_box and not it.get('box'):
            gap_before = True
        in_box = bool(it.get('box'))
        if set(cls.split()) & _cs(C, 'cls_skip') or plain(runs) in C.get('skip_text', ()):
            continue
        if k == 'p' and set(cls.split()) & set(head_cls):          # headings that the ebook sets as paragraphs
            key = next(c for c in cls.split() if c in head_cls)
            spec = head_cls[key]
            lvl, hre = spec if isinstance(spec, tuple) else (spec, None)
            if it.get('box'):                                # the title / sub-titles of a box: small bold lines, not in the contents
                els.append(dict(k='p', style='refhead', runs=_head_runs(C, runs), id=it['id'], src=f'p.{cls}', nomerge=True,
                                **({'before': 1} if gap_before else {})))
                gap_before = False
                continue
            if hre is None or re.match(hre, plain(runs)):
                hr = _head_runs(C, runs, C.get('head_keep', {}).get(key))
                if hr and C.get('merge_dash_head') and plain(hr).startswith('——') and els and els[-1]['k'] == 'h':
                    els[-1]['runs'] = merge_runs(els[-1]['runs'] + hr)
                elif hr:
                    els.append(dict(k='h', lvl=float(lvl), runs=hr, id=it['id'], src=f'p.{cls}', cls=cls))
                continue
        if k == 'h' and C.get('head_clean'):
            runs = _head_runs(C, runs)
            if not runs:
                continue
        if k == 'h' and C.get('head_sub'):
            for pat, repl in C['head_sub']:
                runs = [dict(runs[0], t=re.sub(pat, repl, runs[0]['t']))] + runs[1:]
        if k == 'h' and plain(runs) in C.get('head_demote', {}):
            els.append(dict(k='p', style=C['head_demote'][plain(runs)], runs=runs, id=it['id'], src=f'h.{cls}', nomerge=True))
            continue
        if k == 'h':
            t = plain(runs)
            if t in ('注释', '注 释', '註釋', '註 釋', '注釋') or (els and els[-1]['k'] == 'h' and plain(els[-1]['runs']) == t):
                continue
            if C.get('merge_dash_head') and t.startswith('——') and els and els[-1]['k'] == 'h':
                els[-1]['runs'] = merge_runs(els[-1]['runs'] + runs)          # 'Title' + '——sub-title' set as two headings
                continue
            els.append(dict(k='h', lvl=float(it['lvl']), runs=runs, id=it['id'], src=f'h{it["lvl"]}.{cls}', cls=cls))
            continue
        if k == 'li':
            els.append(dict(k='p', style='noindent', runs=[run('•　')] + runs, id=it['id'], src='li'))
            continue
        if C.get('strip_indent') and runs and not runs[0].get('i'):
            runs = [dict(runs[0], t=runs[0]['t'].lstrip('\u3000 '))] + runs[1:]
            if not runs[0]['t']:
                runs = runs[1:]
            if not runs:
                continue
        b = dict(k='p', runs=runs, id=it['id'], src=f'p.{cls}')
        c = set(cls.split())
        t = plain(runs)
        if re.fullmatch(r'[—－-]{6,}', t):
            continue                                        # the dashed rule before the notes of book 4
        if c & ({'tushuo', 'kindle-cn-picture-txt-withmanycharactors', 'kindle-cn-picture-txt-withfewcharactors'} | _cs(C, 'cls_cap')):
            b['style'] = 'cap'
        elif c & ({'right', 'Right', 'kindle-cn-para-right', 'Inscribe'} | _cs(C, 'cls_right')):
            b.update(style='right', nomerge=True)
        elif c & ({'center', 'kindle-cn-para-center'} | _cs(C, 'cls_center')):
            b.update(style='center', nomerge=True)
        elif it.get('box'):
            b['style'] = 'quote'
        elif it.get('q'):
            b['style'] = 'quotel' if latin_ratio(runs) > 0.35 else 'quote'
            if c & {'noindent'}:
                b['style'] = 'noindent'
        elif c & ({'noindent', 'kindle-cn-noindent'} | _cs(C, 'cls_noindent')):
            b['style'] = 'noindent'
        elif c & ({'kindle-cn-kai'} | _cs(C, 'cls_quote')) or (_kai_only(runs) and not C.get('no_kai_quote')):
            b['style'] = 'quote'
        elif c & _cs(C, 'cls_quotel'):
            b['style'] = 'quotel'
        elif c & _cs(C, 'cls_refhead'):
            b['style'] = 'refhead'
        elif 'kaiti' in c or kaitext or c & _cs(C, 'cls_kai'):
            b['style'] = 'kaibody'
        else:
            b['style'] = 'body'
        if c & _cs(C, 'cls_hang'):                         # '● item' paragraphs: hanging indent under the bullet
            r0 = b['runs'][0]
            b['runs'] = [dict(r0, t=re.sub(r'^([●•■◆▲○◇□])[\s\u3000]*', '\\1\u3000', r0['t']))] + b['runs'][1:]
            b.update(style='noindent', first=-2, left=2)
        if gap_before and b['style'] in ('body', 'noindent', 'quote', 'quotel', 'kaibody', 'center', 'right'):
            b['before'] = 1
        gap_before = False
        if pg_pend and b['style'] not in ('cap',):
            b['runs'] = pg_pend + b['runs']
            pg_pend = []
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
def _cell_lines(cell):
    """A table cell -> its lines (the ebook breaks long cells with <br>)."""
    lines = [[]]
    for r in BT.fix_edges(BT.fix_runs(cell)) if cell else []:
        if r['t'] == BR or r['t'] == '\n':
            lines.append([])
        else:
            lines[-1].append(r)
    return [BT.fix_edges(l) for l in lines if l] or [[]]


def _w(runs):
    return sum(2 if ord(ch) > 0x2e80 else 1 for ch in plain(runs)) / 2.0


def table_blocks(rows, head=True):
    """A small text table -> one paragraph per line of a row, cells as fixed-width inline boxes (hanging indent for the
    last cell).  A row with one cell only (a source line under the table) becomes a small paragraph after the table."""
    ncol = max(len(r) for r in rows)
    tail = []
    while rows and ncol > 1 and sum(1 for c in rows[-1] if plain(c)) == 1 and len(rows[-1]) < ncol:
        tail.insert(0, next(c for c in rows[-1] if plain(c)))
        rows = rows[:-1]
    grid = [[_cell_lines(r[j]) if j < len(r) else [[]] for j in range(ncol)] for r in rows]
    widths = [max(_w(l) for g in grid for l in g[j]) + 1.2 for j in range(ncol)]
    sizes = (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 22, 24, 26, 28)
    cls_of = lambda w: f'tw w{min([x for x in sizes if x >= w], default=28)}'
    used = [int(cls_of(w).split('w')[-1]) for w in widths]
    if head and len(rows) > 1 and ncol > 1 and plain(rows[0][-1]) == plain(rows[1][-1]):
        head = False                                       # the same last-column value in the first two rows: a list, not a header row
    out = []
    indent = sum(used[:-1])
    for ri, g in enumerate(grid):
        nl = max(len(c) for c in g)
        for li in range(nl):
            runs = []
            for j in range(ncol):
                cell = g[j][li] if li < len(g[j]) else []
                bold = ri == 0 and head
                if j == ncol - 1:
                    runs += [dict(x, b=1) if bold else x for x in cell]
                else:
                    runs += [dict(x, c=(x.get('c', '') + ' ' + cls_of(widths[j])).strip(), **({'b': 1} if bold else {})) for x in cell]
                    if not cell:
                        runs.append(run('\u2060', c=cls_of(widths[j])))
            out.append(dict(k='p', style='trow', runs=runs, novary=True, nomerge=True, first=-indent, left=indent + 1,
                            before=1 if ri == 0 and li == 0 else 0, after=1 if ri == len(grid) - 1 and li == nl - 1 and not tail else 0,
                            **({'keep': 1} if li < nl - 1 else {})))
    for k, cell in enumerate(tail):
        out.append(dict(k='p', style='quotel', runs=BT.fix_edges(BT.fix_runs(cell)), first=0, left=0, right=0, nomerge=True,
                        after=1 if k == len(tail) - 1 else 0))
    return out


def fig_label(text, pat=r'^(图[^\s　]+)'):
    m = re.match(pat, text)
    return m.group(1) if m else ''


def join_images(srcs):
    """Two or more images of one table (the ebook splits it with a '(continued)' line) stacked into one image file."""
    from PIL import Image
    name = 'join_' + '_'.join(re.sub(r'\D', '', x)[-5:] for x in srcs) + '.jpeg'
    dst = os.path.join(special.IMG_DIR, name)
    if not os.path.exists(dst):
        ims = [Image.open(os.path.join(special.IMG_DIR, x)).convert('RGB') for x in srcs]
        W = max(im.width for im in ims)
        gap = max(12, W // 40)
        out = Image.new('RGB', (W, sum(im.height for im in ims) + gap * (len(ims) - 1)), 'white')
        y = 0
        for im in ims:
            out.paste(im, ((W - im.width) // 2, y))
            y += im.height + gap
        out.save(dst, quality=93)
    return name


def join_continued(C, els):
    """fig, '（续表）', fig -> one fig of the stacked images."""
    jre = C.get('join_cont')
    if not jre:
        return els
    out = []
    for e in els:
        if e['k'] == 'fig' and len(out) >= 2 and out[-1]['k'] == 'p' and re.fullmatch(jre, plain(out[-1]['runs'])) \
                and out[-2]['k'] == 'fig':
            out.pop()
            prev = out.pop()
            out.append(dict(prev, src=join_images(prev.get('parts', [prev['src']]) + [e['src']]),
                            parts=prev.get('parts', [prev['src']]) + [e['src']]))
            continue
        out.append(e)
    return out


def fig_paragraphs(C, els, fig_no):
    """Figures inside chapters -> 'see plate N' paragraphs; figures of appendices (C['inplace']) stay in the text."""
    els = join_continued(C, els)
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
        mode = C.get('cap_mode', 'after')                            # where the ebook puts a caption: after / before / tabfig (tables above, figures below)
        is_cap = lambda x: x['k'] == 'p' and x.get('style') == 'cap'
        above = lambda x: plain(x['runs']).startswith(('表', '（', '('))   # table titles and '(continued)' lines stand above their image
        if mode in ('before', 'tabfig'):
            while out and is_cap(out[-1]) and (mode == 'before' or above(out[-1])):
                caps.insert(0, re.sub(r'\s+', ' ', runs_text(out.pop()['runs'])).strip())
        while mode != 'before' and i < len(els) and is_cap(els[i]) and (mode == 'after' or not above(els[i])):
            caps.append(re.sub(r'\s+', ' ', runs_text(els[i]['runs'])).strip())
            i += 1
        if C.get('cap_after_re'):                                    # source / note lines right under a figure belong to it
            while i < len(els) and els[i]['k'] == 'p' and re.match(C['cap_after_re'], plain(els[i]['runs'])):
                caps.append(re.sub(r'\s+', ' ', runs_text(els[i]['runs'])).strip())
                i += 1
        text = '　'.join(caps)
        if b['src'] in C['inplace']:
            out.append(dict(k='fig', src=b['src']))
            for cp in caps:
                out.append(dict(k='p', style='quotel', runs=[run(cp)], first=0, left=0, right=0, nomerge=True))
            continue
        n = fig_no(b['src'], text)
        lab = fig_label(text, C.get('label_re', r'^(图[^\s　]+)'))
        runs = []
        if lab:
            runs.append(run(lab + '　'))
        runs.append(run(f'见书后插图{n}', h=f'plate-{n}', a=f'figref-{n}', c='fig'))
        out.append(dict(k='p', style='center', runs=runs, novary=True, nosplit=True, nomerge=True, before=1, after=1, plate_ref=1))
    return out


def image_blocks(src, max_h, width=None, max_scale=None):
    """A figure that stays in the text: an image block scaled into the text width (at most max_h pt high)."""
    from PIL import Image
    w, h = Image.open(os.path.join(special.IMG_DIR, src)).size
    s = min((width or style.TEXT_W) / w, max_h / h, max_scale or 1e9)
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
                rest[0] = dict(rest[0], t=rest[0]['t'].lstrip(' \u3000'))
                if fmt == 'zhu':
                    rest[0] = dict(rest[0], t=re.sub(r'^[：:][\s\u3000]*', '', rest[0]['t']))     # '註9：text'
                rest = [r for r in rest if r['t'] or r.get('i')]
            st = 'notel' if latin_ratio(rest) > 0.4 else 'note'
            out.append(dict(k='p', style=st, runs=merge_runs(marks + rest)))
        else:
            out.append(dict(k='p', style='notec', runs=runs))
    return out


def notes_module(mid, groups, fmt, zone='body', title='注　释', toc_level=2, toc_title='注释'):
    blocks = [dict(k='h', style='h1', rank=1, runs=[run(title)], id=mid + '#top')]
    for gtitle, items in groups:
        if len(groups) > 1:
            blocks.append(dict(k='p', style='idxhead', runs=[run(gtitle)], nostart=False))
        blocks += note_blocks(items, fmt)
    return Mod(mid=mid, zone=zone, title=toc_title, blocks=blocks, grid='small1', toc_level=toc_level, toc_title=toc_title)


def renumber(els, notes):
    """The ebooks restart note numbers in every file: number the notes of a unit 1.. in the order of their marks."""
    anchors = {}
    for it in notes:
        r0 = it['runs'][0] if it['runs'] else {}
        if r0.get('a'):
            anchors[r0['a']] = it
    order = {}
    for e in els:
        for r in e.get('runs') or []:
            if r.get('h') in anchors and not r.get('i') and r['h'] not in order:
                order[r['h']] = len(order) + 1
    for a in anchors:
        order.setdefault(a, len(order) + 1)                      # notes without a mark keep their place at the end
    els = [dict(e, runs=[dict(r, t=str(order[r['h']])) if r.get('h') in anchors and not r.get('i') else r for r in e['runs']])
           if e.get('runs') else e for e in els]
    out = []
    for a, it in anchors.items():
        out.append((order[a], dict(it, runs=[dict(it['runs'][0], t=str(order[a]))] + it['runs'][1:])))
    return els, [it for _, it in sorted(out, key=lambda x: x[0])]


# ---------------------------------------------------------------------------------------------- pages
def copyright_module(n, skip=0):
    blocks = [dict(k='space', style='cip', runs=[], n=4)]
    for it in BE.items(P(n))[skip:]:
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
def _parts(x):
    return list(x) if isinstance(x, (list, tuple)) else [x]


def part_divider(C, els):
    """A heading 'Part N' (+ sub-title lines that follow it) that becomes a page of its own: (lines, toc title, remaining elements)."""
    pr = re.compile(C.get('part_re') or PART_RE.pattern)
    if not (els and els[0]['k'] == 'h' and pr.match(plain(els[0]['runs']))):
        return None
    head = plain(regap_heading(els[0]['runs']))
    rest = els[1:]
    m = re.match(C['part_split'], head) if C.get('part_split') else None
    if not m:
        return [(1.0, head)], head, rest
    lines = [(1.0, m.group(1))]
    title = m.group(1)
    if m.group(2):
        lines.append((2.0, m.group(2)))
        title += '　' + m.group(2)
    if m.lastindex and m.lastindex >= 3 and m.group(3):
        lines.append((3.0, m.group(3)))                          # an English sub-title line (page only, not in the contents)
    sub = _cs(C, 'part_sub_cls')
    while rest and rest[0]['k'] == 'p' and set(rest[0]['src'][2:].split()) & sub:
        lines.append((3.0, plain(rest[0]['runs'])))
        title += '　' + plain(rest[0]['runs'])
        rest = rest[1:]
    epi = _cs(C, 'part_epi_cls')                                  # the epigraph of the part, set small under the title
    if epi and rest and rest[0]['k'] == 'p' and set(rest[0]['src'][2:].split()) & epi:
        lines.append((97, ''))
        while rest and rest[0]['k'] == 'p' and set(rest[0]['src'][2:].split()) & epi:
            lines.append((99, plain(rest[0]['runs'])))
            rest = rest[1:]
    return lines, title, rest


def book(b):
    C = CFG[b]
    m = meta(b)
    cover = C['cover']
    if C.get('cover_file'):                                          # a cover image supplied separately (source/covers/…) replaces the ebook's
        src = os.path.join(style.ROOT, C['cover_file'])
        cover = 'cover_custom' + os.path.splitext(src)[1]
        dst = os.path.join(special.IMG_DIR, cover)
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            shutil.copy(src, dst)
    mods = [page_module('cover', 'cover', special.cover_html(cover), folio=False)]
    if C['title_img']:
        mods.append(page_module('title', 'front', special.cover_html(C['title_img']), folio=False))
    else:
        mods.append(page_module('title', 'front', special.title_html(m), folio=False))
    if C.get('copyright_img'):
        mods.append(page_module('copyright', 'front', special.cover_html(C['copyright_img']), folio=False))
    elif C.get('copyright') is not None:
        mods.append(copyright_module(C['copyright'], C.get('copyright_skip', 0)))
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
            zone_list.append(notes_module(f'notes{counter[0]}', pend, fmt, zone=zone, title=C.get('notes_title', '注　释'),
                                          toc_title=C.get('notes_toc', '注释')))
            pend, pend_chars = [], 0

    def gather(ns, kaitext=False):
        els, notes = [], []
        for n in _parts(ns):
            e, nt = elements(C, BE.items(P(n)), kaitext=kaitext)
            els += e
            notes += nt
        return els, notes

    def add_unit(ns, zone_list, zone, els, notes, top=False, kaitext=False, toc=True):
        nonlocal pend_chars
        n = _parts(ns)[0]
        if C.get('renum') and notes:
            els, notes = renumber(els, notes)
        els = fig_paragraphs(C, els, fig_no)
        blocks = []
        osz = C.get('orn_size', (70.0, 9.9))
        for e in unit_blocks(els):
            if e['k'] == 'fig':
                blocks += image_blocks(e['src'], style.TEXT_H - 11 * style.LINE, max_scale=C.get('img_max_scale'))      # leaves room for the heading above and a source line below
            elif e['k'] == 'orn':
                blocks += [dict(k='img', style='orn', runs=[], src=special.img_url(e['src']), w=osz[0], h=osz[1],
                                n=math.ceil(osz[1] / style.LINE))]
            elif e['k'] == 'table':
                blocks += table_blocks(e['rows'], C.get('table_head', True))
            else:
                blocks.append(e)
        blocks = wrap_lines(finish_blocks(blocks))
        for x in blocks:
            if x['k'] in ('p', 'h') and x.get('runs'):
                x['runs'] = mark_runs(x['runs'], fmt)
        title = next((title_text(x['runs']) for x in blocks if x['k'] == 'h'), '')     # no heading (a statement page): no bookmark
        if C.get('head_split'):                                    # 'Title／Sub-title' chapter headings: the sub-title on a line of its own
            for x in blocks:
                if x['k'] == 'h' and x.get('style') == 'h1' and any(C['head_split'] in r['t'] for r in x['runs']):
                    out = []
                    for r in x['runs']:
                        parts = r['t'].split(C['head_split'])
                        for k, t in enumerate(parts):
                            if k:
                                out.append(run('\n'))
                            if t:
                                out.append(dict(r, t=t))
                    x['runs'] = out
                    x['nobalance'] = True
        keep = [x for x in blocks if x.get('nobalance')]
        saved = [x['runs'] for x in keep]
        blocks = balance_headings(blocks)
        for x, r in zip(keep, saved):
            x['runs'] = r
        for x in blocks:
            if x['k'] == 'h':
                rs = x['runs']
                for i in range(len(rs) - 1):
                    if rs[i]['t'] == '\n' and rs[i + 1].get('s'):
                        rs[i], rs[i + 1] = rs[i + 1], rs[i]
        mod = Mod(mid=P(n), zone=zone, title=title, blocks=blocks, toc_level=1, toc=toc and any(x['k'] == 'h' for x in blocks))
        mod.src_part = n
        mod.src_parts = _parts(ns)
        mod.top = top
        mod.unnest = zone == 'back'
        zone_list.append(mod)
        if notes:
            pend.append((title, notes))
            pend_chars += sum(len(runs_text(i['runs'])) for i in notes)

    for n, kind in C['front']:
        els, notes = gather(n, kaitext=(kind == 'kaitext'))
        if kind == 'dedication':
            lines = [(99, plain(e['runs'])) for e in els if e['k'] == 'p']
            dm = page_module('dedication' if not any(x.mid == 'dedication' for x in front) else f'dedication{n}', 'front',
                             special.divider_html(lines), toc=False, title='献词', folio=False, head=False)
            dm.lines = [t for _, t in lines]
            dm.src_parts = _parts(n)
            front.append(dm)
            continue
        if kind == 'kaibody':                                      # a whole page in the ebook's Kai type: full-width Kai body text
            els = [dict(e, style='kaibody') if e['k'] == 'p' and e.get('style') in ('quote', 'body') else e for e in els]
        add_unit(n, front, 'front', els, notes, top=True, kaitext=(kind == 'kaitext'))
    flush(front, 'front')
    for n in C['body']:
        els, notes = gather(n)
        pd = part_divider(C, els)
        if pd:
            lines, title_s, els = pd
            n0 = _parts(n)[0]
            div = page_module(f'div{n0}', 'body', special.divider_html(lines), toc=True, toc_title=title_s,
                              toc_level=0, title=title_s, folio=False, head=False)
            div.part = True
            div.lines = [t for _, t in lines]
            div.src_parts = _parts(n)
            flush(body, 'body')
            body.append(div)
            if not els:
                continue
        add_unit(n, body, 'body', els, notes)
        if pend_chars >= NOTE_MIN:
            flush(body, 'body')
    flush(body, 'body')
    for n in C['back']:
        kind = 'text'
        if isinstance(n, tuple):
            n, kind = n
        els, notes = gather(n)
        if kind == 'noindent':
            els = [dict(e, style='noindent') if e['k'] == 'p' and e.get('style') == 'body' else e for e in els]
        add_unit(n, back, 'back', els, notes, top=True)
        flush(back, 'back')
    for n in C.get('endnotes', ()):                            # notes of the whole book gathered in the last part of the ebook
        notes = [dict(it, k='note') for it in BE.items(P(n)) if it['k'] in ('p', 'note') and it.get('runs')]     # (continuation paragraphs too)
        if notes:
            nm = notes_module('notes_end', [(C['endnotes_title'], notes)], fmt, zone='back', title=C['endnotes_title'],
                              toc_level=1, toc_title=C['endnotes_title'])
            nm.top = True
            nm.unnest = True
            back.append(nm)
    plates = plate_modules(fig_list)
    allm = front + body + back + plates
    toc_bl = toc_blocks(allm, '目　錄' if C.get('tc') else '目　录')
    for x in toc_bl:
        if x.get('style', '').startswith('toc'):
            x['noshrink'] = True
    toc = Mod(mid='toc', zone='front', title='目錄' if C.get('tc') else '目录', blocks=toc_bl, toc=False, head=True)
    toc.tail_min = 5
    tail = []
    if C['tail']:
        tail.append(page_module('qr', 'back', qr_html(C['tail']), folio=False))
    if C.get('backcover'):
        tail.append(page_module('backcover', 'back', special.cover_html(C['backcover']), folio=False))
    mods += [toc] + allm + tail
    return dict(id=f'b{b}', title=C['title'], meta=dict(m, author=C['pdf_author']), modules=mods, toc=toc, vol=b)
