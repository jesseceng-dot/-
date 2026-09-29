"""《康德文集（注释版）》：部件 -> 块（标题层级、短行样式、注释拆分）-> 模块单元（分隔页 / 正文 / 注释组）。

标题层级的原则：
  * 源文件里的 h1–h6 标签、以及 p.h7/h8/z1/z22/z3/ch/bold/jz/cuti/center1/yinwen-c 等“短行”类，
    按 (标签或 class、文字模式) 给每个标题一个“源层级”数（越小越高）；
  * 每个模块内把出现过的源层级从高到低压成连续的 1、2、3……级（第 1 级 = 模块标题），因此同一模块内同一类标题永远同级、
    上下级次序与原书一致，也不会出现“跳级”。
个别作品里同一种编号出现在不同层级（例如《未来形而上学导论》里的“一、”在“第N节”之上），在 OVERRIDES 里按部件单列。
"""
import re
import copy
from . import kant_extract as KE, kant_text as KT
from .model import run, merge_runs, runs_text, BR, OBJ
from .extract import ln

CN = '一二三四五六七八九十百零〇'
SHORT_CLS = {'ch', 'ck', 'bold', 'jz', 'juzhong', 'center', 'centerr', 'center1', 'cuti', 'z1', 'z22', 'z3', 'h7', 'h8',
             'yinwen-c', 'yinwen-c2', 'tuzhu-center', 'tuzhu-left', 'yinwen1', 'yinwen0', 'bodytext-right', 'right'}
NAME_CLS = {'center', 'centerr', 'juzhong', 'jz', 'yinwen1', 'ck', 'ch', 'bold'}
BARE_NUM = re.compile(r'^(第[一二三四五六七八九十百\d]+[a-z]?[节款条]|§\d+|[一二三四五六七八九十]+|\d+|[（(][一二三四五六七八九十\d]+[)）])$')
SEP_RE = re.compile(r'^[※\*][\s　※\*]*$')
ORD_ONLY = re.compile(r'^第[%s\d]+[部编卷篇章节款条期]分?$' % CN)
MARK_TAIL = re.compile(r'(?:⁠?[\[［(（]\d+[\]］)）])+$')

# ---- semantic levels for short-line classes (lower = higher in the hierarchy) ---------------------------------
# (regex on the plain text, level).  Levels 1–6 belong to h1–h6 tags; p-class headings live between 6 and 11.
PATTERNS = [
    (r'^第[%s]+部分?(?:[\s　]|$)(?!.*页)' % CN, 6.1),
    (r'^第[%s]+编' % CN, 6.2),
    (r'^第[%s]+卷' % CN, 6.3),
    (r'^第[%s]+篇' % CN, 6.4),
    (r'^第[%s]+章' % CN, 7.0),
    (r'^第[%s]+款|款：' % CN, 7.4),
    (r'^第[%s\d]+[a-z]?节|^第\d+节|^§\s*\d+|^第\d+[a-z]节' % CN, 8.0),
    (r'^考察[%s]|^命题[%s\d]+|^第[%s]+个|^第[%s]+条附论' % (CN, CN, CN, CN), 8.0),
    (r'^[%s]+、' % CN, 9.0),
    (r'^[%s]+$' % CN, 9.0),
    (r'^[（(][%s\d]+[)）]' % CN, 9.4),
    (r'^[A-Z][\.．]|^[甲乙丙丁戊己庚辛]、', 9.6),
    (r'^\d+[\.．]', 10.0),
    (r'^\d+$', 10.0),
]
KEYWORDS = [
    (r'^科学院版(?:《[^》]*》)?(?:第.版)?编者导言', 7.5),
    (r'^附录', 7.2),
    (r'^(证明|定理|解说|附释|附注|说明|阐明|解释|运用|问题|注释|定义|结论|结束语|前言|后记|正论|反论|预示|划分|答复|反驳|附论|例证|总附释|总说明|总附注|导论|导言|决疑论问题)', 9.8),
]
CLASS_DEFAULT = {'h7': 7.0, 'h8': 8.0, 'z22': 7.0, 'z1': 9.0, 'z3': 10.0, 'yinwen-c': 9.0, 'cuti': 9.0, 'center1': 8.0,
                 'jz': 8.5, 'tuzhu-center': None, 'bold': 9.0, 'ch': 9.0}
HEAD_CLS = {'h7', 'h8', 'z1', 'z22', 'z3', 'yinwen-c', 'cuti', 'center1'}


def plain(runs):
    return runs_text([r for r in runs if not r.get('s')]).replace(BR, '')


def is_name(t, cls, after_heading):
    if len(t) > 44 or re.search(r'[0-9。：；！？]|第.{1,3}[章节部篇]', t):
        return False
    if '·' in t or re.search(r'（[A-Za-z][^）]*）?$', t):
        return True
    if cls in NAME_CLS and after_heading and re.fullmatch(r'[一-鿿]{2,4}', t) and t not in HEAD_WORDS:
        return True
    return False


KNOWN_NAMES = {'李秋零', '苗力田'}
HEAD_WORDS = {'证明', '定理', '解说', '附释', '附注', '说明', '阐明', '解释', '运用', '问题', '注释', '定义', '结论', '前言', '后记',
              '正论', '反论', '预示', '划分', '答复', '反驳', '附论', '例证', '导论', '导言', '附录', '结语', '总说明', '总附释'}


def pattern_level(t, cls):
    tt = MARK_TAIL.sub('', t)
    if cls in ('yinwen-c', 'yinwen-c2'):
        return CLASS_DEFAULT['yinwen-c']
    if cls in ('h7', 'h8'):
        return CLASS_DEFAULT[cls]
    for pat, lv in PATTERNS:
        if re.search(pat, tt):
            return lv
    for pat, lv in KEYWORDS:
        if re.search(pat, tt):
            return CLASS_DEFAULT.get(cls) if cls in HEAD_CLS and lv > 9 else lv
    return CLASS_DEFAULT.get(cls)


def unbreak(runs):
    """Hard line breaks of the source inside a short line that is not a heading: dropped (space between Latin words)."""
    out = []
    for r in runs:
        if '\u2028' in r['t']:
            t = re.sub(r'(?<=[A-Za-z0-9])\u2028(?=[A-Za-z0-9])', ' ', r['t']).replace('\u2028', '')
            r = dict(r, t=t)
        out.append(r)
    return merge_runs(out)


def centre_weak_runs(els):
    """Three or more consecutive short lines (heading-class lines without any numbering + centred lines) are the lines of a
    title page (author, place, date ...), not headings: the un-numbered ones become centred lines."""
    def short(b):
        return (b['k'] == 'h' and b.get('weak')) or (b['k'] == 'p' and b.get('style') in ('center', 'ck'))
    out, i = [], 0
    while i < len(els):
        if short(els[i]):
            j = i
            while j < len(els) and short(els[j]):
                j += 1
            run_ = els[i:j]
            if j - i >= 3 and any(b['k'] == 'h' for b in run_):
                for b in run_:
                    if b['k'] == 'h':
                        b = dict(b, k='p', style='center', nomerge=True)
                        b.pop('lvl', None)
                        b.pop('weak', None)
                    out.append(b)
            else:
                out += run_
            i = j
            continue
        out.append(els[i])
        i += 1
    return out


def split_runs(runs, pos):
    """Split a run list at character offset `pos`."""
    a, b, n = [], [], 0
    for r in runs:
        t = r['t']
        if n + len(t) <= pos:
            a.append(r)
        elif n >= pos:
            b.append(r)
        else:
            k = pos - n
            a.append(dict(r, t=t[:k]))
            b.append(dict(r, t=t[k:]))
        n += len(t)
    return a, b


def strip_breaks(runs):
    runs = [dict(r) for r in runs]
    while runs and runs[0]['t'] and not runs[0].get('i'):
        runs[0]['t'] = runs[0]['t'].lstrip('\u2028 ')
        if runs[0]['t']:
            break
        runs.pop(0)
    while runs and runs[-1]['t'] and not runs[-1].get('i'):
        runs[-1]['t'] = runs[-1]['t'].rstrip('\u2028 ')
        if runs[-1]['t']:
            break
        runs.pop()
    return runs


def elements(items, vol, part=None):
    """Items of one part -> (main elements, note items).  Main elements are blocks with an extra 'lvl' for headings."""
    from . import kant_tables
    KT.set_volume(vol)
    els, notes = [], []
    prev_heading = False
    skip_to = -1
    for idx, it in enumerate(items):
        if idx <= skip_to:
            continue
        if (part, idx) in kant_tables.FIRST:
            tid, skip_to = kant_tables.FIRST[(part, idx)]
            els.append(dict(k='fig', src=tid))
            prev_heading = False
            continue
        k = it['k']
        if k == 'note':
            if it['cls'] == 'noteTitle':
                continue
            notes.append(it)
            continue
        if k == 'img':
            els.append(dict(k='fig', src=it['src']))
            prev_heading = False
            continue
        if k == 'table':
            continue
        runs = KT.fix_edges(KT.fix_runs(it['runs']))
        if not runs:
            continue
        t = plain(runs)
        cls = it['cls']
        if k == 'h':
            runs = strip_breaks(runs)
            if not runs:
                continue
            tt = plain(runs)
            if '\u2028' in tt:
                head, _, tail = tt.rpartition('\u2028')
                if head.strip('\u2028') and is_name(tail.strip(), 'center', True):     # 'title / editor's name' in one heading
                    hr, nr = split_runs(runs, len(head))
                    els.append(dict(k='h', lvl=float(it['lvl']), runs=strip_breaks(hr), id=it['id'], src=f'h{it["lvl"]}.{cls}'))
                    els.append(dict(k='p', style='center', runs=strip_breaks(nr), name=1, nomerge=True, src='name'))
                    prev_heading = False
                    continue
            if it['lvl'] >= 2 and prev_heading and (tt in KNOWN_NAMES or ('·' in tt and is_name(tt, 'center', True))):
                els.append(dict(k='p', style='center', runs=runs, id=it['id'], src=f'h{it["lvl"]}.{cls}', name=1, nomerge=True))
                prev_heading = False                        # an author's name under a title (h2 in the source), not a heading
                continue
            els.append(dict(k='h', lvl=float(it['lvl']), runs=runs, id=it['id'], src=f'h{it["lvl"]}.{cls}'))
            prev_heading = True
            continue
        align = it.get('align')
        if vol == 1 and cls == '':               # vol 1 marks its short lines by alignment (div.tocenter / div.toleft) only
            cls = {'center': 'ch', 'left': 'bold'}.get(align, '')
        b = dict(k='p', runs=runs, id=it['id'], src=f'p.{cls}')
        if it.get('cap'):
            b['style'] = 'cap'
            els.append(b)
            continue
        if part == 16 and vol == 1 and 269 <= idx <= 279:
            b['style'] = 'verse'                       # Juvenal verse of the vol-1 text, indented with NBSP in the source
            b['nomerge'] = True
        elif SEP_RE.match(t):
            b['style'] = 'sep'
        elif cls in ('bodytext', ''):
            b['style'] = 'body'
        elif cls == 'yinwen' or (cls in ('yinwen1', 'yinwen0') and len(t) > 40):
            b['style'] = 'quote'
        elif cls == 'yinwen0':
            b['style'] = 'noindent'
        elif cls in ('bodytext-right', 'right'):
            b['style'] = 'right'
        elif cls == 'copyright-bodytext':
            b['style'] = 'copy'
        elif cls in SHORT_CLS or align in ('center', 'left', 'right'):
            b = short_line(b, t, cls, align, prev_heading)
        else:
            b['style'] = 'body'
        if b['k'] == 'p':
            b['runs'] = unbreak(b['runs'])
        prev_heading = b['k'] == 'h'
        els.append(b)
    return centre_weak_runs(els), notes


def short_line(b, t, cls, align, after_heading):
    """A short line of a heading-ish class: name / heading / centred line / paragraph."""
    if len(t) > 64 or (re.search(r'[。！？]', t[:-1]) and len(t) > 30):
        b['style'] = 'noindent'
        if cls == 'bold':
            b['runs'] = [dict(r, b=1) for r in b['runs']]
        return b
    if is_name(t, cls, after_heading):
        b.update(style='center', name=1)
        return b
    if cls in ('bold', 'ch', 'yinwen0') and re.search(r'[！：]$', t) and len(t) <= 24 and not re.match(r'^[%s第]' % CN, t):
        b['style'] = 'noindent'                            # salutation of a letter / dedication
        return b
    lv = pattern_level(t, cls)
    if cls in HEAD_CLS or (cls in ('ch', 'bold', 'jz', 'juzhong', 'center') and lv is not None):
        weak = lv is None or lv == CLASS_DEFAULT.get(cls)
        b.update(k='h', lvl=lv if lv is not None else CLASS_DEFAULT.get(cls, 9.0), style='h', weak=weak and cls in ('ch', 'jz', 'juzhong', 'center'))
    elif cls == 'bold':
        if re.search(r'[！？：]$', t):
            b['style'] = 'noindent'                       # salutation of a letter
        else:
            b.update(k='h', lvl=CLASS_DEFAULT['bold'], style='h')
    elif cls in ('bodytext-right', 'right') or align == 'right':
        b['style'] = 'right'
    elif cls == 'ck':
        b['style'] = 'ck'
    elif align == 'left':
        b['style'] = 'noindent'
    elif cls in ('yinwen1', 'yinwen0'):
        b['style'] = 'quote'
    elif cls in ('tuzhu-center', 'tuzhu-left'):
        b['style'] = 'ck'
    else:
        b['style'] = 'center'
    return b


# ---------------------------------------------------------------------------------------------- ranks
def rank_headings(blocks, overrides=()):
    """Assign rank 1.. to the heading blocks of one module from their source levels (see module docstring)."""
    hs = [b for b in blocks if b['k'] == 'h']
    if not hs:
        return blocks
    for b in hs:
        b['lvl0'] = b['lvl']
    for pat, lv in overrides:
        for b in hs:
            if re.search(pat, plain(b['runs'])):
                b['lvl'] = lv
    top = hs[0]['lvl']
    lower = sorted({b['lvl'] for b in hs if b['lvl'] > top})
    rank_of = {lv: i + 2 for i, lv in enumerate(lower)}
    for b in hs:
        b['rank'] = min(rank_of.get(b['lvl'], 1), 9)
        b['style'] = f'h{b["rank"]}'
    return blocks


# ---------------------------------------------------------------------------------------------- volumes / parts
VOL_PARTS = {1: (1, 22), 2: (23, 44), 3: (45, 115), 4: (116, 130), 5: (131, 152), 6: (153, 174), 7: (175, 234),
             8: (235, 305), 9: (306, 348), 10: (349, 374)}
P = lambda n: f'part{n:04d}'


def front_parts(v):
    """part numbers: cover, copyright (None for vol 1), contents, preface (前言), foreword (序), first body part"""
    a = VOL_PARTS[v][0]
    if v == 1:
        return dict(cover=a, copyright=None, toc=a + 1, preface=a + 2, foreword=a + 3, body=a + 4)
    return dict(cover=a, copyright=a + 1, toc=a + 2, preface=a + 3, foreword=a + 4, body=a + 5)


def text_len(els):
    return sum(len(runs_text(b['runs'])) for b in els if b.get('runs'))


def first_head_lvl(els):
    return els[0]['lvl'] if els and els[0]['k'] == 'h' else None


def load_part(n, v):
    els, notes = elements(KE.items(P(n)), v, n)
    for pat, lv in OVERRIDES.get(n, []):
        for b in els:
            if b['k'] == 'h' and re.search(pat, plain(b['runs'])):
                b['lvl'] = lv
    for pat, st in STYLE_FIX.get(n, []):
        for b in els:
            if b['k'] == 'h' and re.search(pat, plain(b['runs'])):
                b.update(k='p', style=st, nomerge=True)
                b.pop('lvl', None)
    fix_titles(els, n)
    return dict(n=n, els=els, notes=notes)


def is_title_page(rest):
    """Only headings, centred / right lines and short verse lines (no editor's introduction, no running text)."""
    for b in rest[1:]:
        if b['k'] == 'h':
            if re.search(r'编者导言|前言|序言', plain(b['runs'])):
                return False
        elif b['k'] == 'p':
            if b['style'] in ('body', 'noindent'):
                return False
            if b['style'] in ('quote', 'verse') and len(plain(b['runs'])) > 40:
                return False
        else:
            return False
    return True


def divider_len(els, v, nxt_lvl):
    """Number of leading elements that form a divider page (a work / section title page), 0 if none."""
    k = 0
    while k < len(els):
        rest = els[k:]
        first = rest[0]
        if first['k'] != 'h':
            break
        t = plain(first['runs'])
        if len(rest) > 1 and first['lvl'] == 1.0 and not ORD_ONLY.match(t) and rest[1]['k'] == 'h':
            t1 = plain(rest[1]['runs'])
            title_like = rest[1]['lvl'] == 2.0 or re.match(r'^(科学院版.*编者导言|前言|序言|献词|导论|引言)$', t1)
            if (rest[1]['lvl'] == 1.0 and v == 1) or (title_like and nxt_lvl is not None and nxt_lvl >= 2.0):
                k += 1
                continue
        break
    rest = els[k:]
    if rest and rest[0]['k'] == 'h' and nxt_lvl is not None and nxt_lvl > rest[0]['lvl'] and text_len(rest) < 260 \
            and len(rest) <= 10 and is_title_page(rest):
        if not (k == 0 and rest[0]['lvl'] > 6):
            return len(els)
    return k


# consecutive parts that form ONE module (a chapter split into files by the ebook): first part -> following parts
JOIN = {
    160: list(range(161, 169)),        # vol 6  判断力批判·导论 一–九
    367: [368, 369, 370, 371],         # vol 10 伦理教学法 第49–52节、附释
    372: [373, 374],                   # vol 10 伦理的修行法 第53节、结束语、最后的附释
    67: [68, 69, 70, 71], 72: [73, 74], 75: [76, 77], 78: [79, 80],                           # vol 3 宗教：四篇及其各章
    329: [330, 331, 332, 333], 334: [335, 336], 337: [338, 339], 340: [341, 342],            # vol 9 同上
    319: [320, 321, 322], 323: [324, 325],                                                     # vol 9 视灵者的梦：第一篇、第二篇
    87: [88, 89, 90, 91, 92, 93],      # vol 3 法权论：第一卷、第二卷（第二卷处自动分开）
    96: list(range(97, 106)),          # vol 3 伦理要素论：第一部分、第二部分
}
DIVIDER_OFF = {160}


def volume_units(v, parts=None):
    """List of units: dict(kind='divider'|'text', els, notes=[(part, note items)], parts=[...])."""
    a, b = VOL_PARTS[v]
    fp = front_parts(v)
    nums = list(range(fp['body'], b + 1))
    parts = parts or {n: load_part(n, v) for n in nums}
    parts = merge_joined(parts, nums)
    nums = [n for n in nums if n in parts]
    units = []
    carry = None
    for i, n in enumerate(nums):
        pd = parts[n]
        els = list(pd['els'])
        notes = [(n, pd['notes'])] if pd['notes'] else []
        pnums = list(pd.get('parts', [n]))
        if carry:
            els = carry['els'] + els
            notes = carry['notes'] + notes
            pnums = carry['parts'] + pnums
            carry = None
        nxt = parts[nums[i + 1]] if i + 1 < len(nums) else None
        nxt_lvl = first_head_lvl(nxt['els']) if nxt else None
        k = 0 if n in DIVIDER_OFF else divider_len(els, v, nxt_lvl)
        if k:
            units.append(dict(kind='divider', els=els[:k], notes=[], parts=pnums))
            els = els[k:]
        if not els:
            carry = dict(els=[], notes=notes, parts=pnums) if notes else None
            continue
        segs = split_h1(els)
        for si, seg in enumerate(segs):
            last = si == len(segs) - 1
            units.append(dict(kind='text', els=seg, notes=notes if last else [], parts=pnums))
        this_lvl = segs[-1][0]['lvl'] if segs[-1][0]['k'] == 'h' else None
        if text_len(segs[-1]) < 800 and nxt and len(segs) == 1 and not k and (nxt_lvl is None or nxt_lvl > 1.0) \
                and not (this_lvl is not None and nxt_lvl is not None and nxt_lvl < this_lvl):
            u = units.pop()
            carry = dict(els=u['els'], notes=u['notes'], parts=u['parts'])
    if carry:
        units.append(dict(kind='text', els=carry['els'], notes=carry['notes'], parts=carry['parts']))
    return units


def merge_joined(parts, nums):
    parts = dict(parts)
    for first, rest in JOIN.items():
        if first in parts and all(r in parts for r in rest):
            base = parts[first]
            for r in rest:
                base['els'] = base['els'] + parts[r]['els']
                base['notes'] = base['notes'] + parts[r]['notes']
                base.setdefault('parts', [first]).append(r)
                del parts[r]
    return parts


def split_h1(els):
    """A later heading that is at least as high as the module's first heading (a second work / the next 卷 / 篇 in the same
    file) starts a new module, provided both sides are substantial."""
    if not els or els[0]['k'] != 'h':
        return [els]
    L0 = els[0]['lvl']
    cuts = []
    for i, b in enumerate(els):
        if i == 0 or b['k'] != 'h' or b['lvl'] > min(L0, 6.5) or ORD_ONLY.match(plain(b['runs'])):
            continue
        if els[i - 1]['k'] == 'h' and els[i - 1]['lvl'] <= b['lvl']:
            continue
        lo = cuts[-1] if cuts else 0
        if text_len(els[lo:i]) >= 1500 and text_len(els[i:]) >= 350:
            cuts.append(i)
    if not cuts:
        return [els]
    out, lo = [], 0
    for c in cuts:
        out.append(els[lo:c])
        lo = c
    out.append(els[lo:])
    return out


NUM_PATTERNS = [
    (re.compile(r'^(第[%s]+条附论)[\s　\u2028]*(?=\S)' % CN), '　'),
    (re.compile(r'^(第[%s\d]+[部编卷篇章节款条期]分?)(?![的分])[\s　\u2028]*(?=\S)' % CN), '　'),
    (re.compile(r'^(第[%s]+个[^\s　]{0,4})[\s　]+(?=\S)' % CN), '　'),
    (re.compile(r'^(§\s*\d+)[\s　]*(?=[^\d\s])'), ' '),
    (re.compile(r'^([%s]+、)[\s　\u2028]*(?=\S)' % CN), ''),
    (re.compile(r'^([甲乙丙丁戊己庚辛]、)[\s　]*(?=\S)'), ''),
    (re.compile(r'^(考察[%s]|命题[%s\d]+)[\s　]*(?=\S)' % (CN, CN)), '　'),
    (re.compile(r'^(\d+[.．])[\s　]*(?=[^\d\s])'), ' '),
    (re.compile(r'^([A-Z][.．])[\s　]*(?=\S)'), ' '),
    (re.compile(r'^([Ⅰ-Ⅻ][.．])[\s　]*(?=\S)'), ' '),
    (re.compile(r'^(（[a-z\d%s]+）)[\s　]*(?=\S)' % CN), ' '),
]


_CJK_SP = re.compile(r'(?<=[\u4e00-\u9fff，、；：！？）》”—〕］])\u2028+(?=[\u4e00-\u9fff（《“—〔［])')


def _tidy(t, head_done):
    t = _CJK_SP.sub('', t)
    t = re.sub('\u2028+', ' ', t)
    # a single space between two Chinese strings inside a heading is a label gap ('导言 先验逻辑的理念')
    t = re.sub(r'(?<=[\u4e00-\u9fff]) (?=[\u4e00-\u9fff])', '\u3000', t) if head_done else t
    return t


def regap_heading(runs):
    """One solid gap between an ordinal (or label) and the title text; source line breaks inside a title removed."""
    if not runs:
        return runs
    first = runs[0]
    t = first['t']
    head, body = '', t
    if len(runs) == 1 and ORD_ONLY.match(t.strip()):
        return [dict(first, t=t.strip())]
    for pat, gap in NUM_PATTERNS:
        m = pat.match(t)
        if m:
            head, body = m.group(1) + gap, t[m.end():]
            break
    out = [dict(first, t=head + _tidy(body, True))] + [dict(r) for r in runs[1:]]
    for i in range(1, len(out)):
        if not out[i].get('i'):
            out[i]['t'] = _tidy(out[i]['t'], False)
    return out


def dedupe_title(runs):
    """'X X' or 'X…X' (the title text was typed twice in the source) -> one copy."""
    t = plain(runs)
    n = len(t)
    for k in range(min(n // 2, 40), 2, -1):
        if t[:k] == t[-k:] and n >= 2 * k and not t[:k].endswith(('章', '节')):
            cut = n - k
            new, pos = [], 0
            for r in runs:
                if r.get('s') or r.get('i'):
                    new.append(r)
                    continue
                keep = max(0, min(len(r['t']), cut - pos))
                pos += len(r['t'])
                if keep:
                    new.append(dict(r, t=r['t'][:keep]))
            return new, t[cut:]
    return runs, None


def merge_ordinals(els):
    """'第一部' + '先验要素论' (two consecutive headings of the same level) -> one heading '第一部　先验要素论'."""
    out = []
    i = 0
    while i < len(els):
        b = els[i]
        if b['k'] == 'h' and i + 1 < len(els) and els[i + 1]['k'] == 'h' and els[i + 1]['lvl'] == b['lvl'] \
                and ORD_ONLY.match(MARK_TAIL.sub('', plain(b['runs'])).strip()):
            nb = dict(b)
            nb['runs'] = merge_runs(list(b['runs']) + [run('　')] + list(els[i + 1]['runs']))
            out.append(nb)
            i += 2
            continue
        out.append(b)
        i += 1
    return out


# ---------------------------------------------------------------------------------------------- per-part corrections
# heading-level overrides: part -> [(regex on the heading text, source level)]
OVERRIDES = {
    128: [(r'^永久和平的第.条确定条款', 2.5)],
    148: [(r'^永久和平的第.条确定条款', 3.5), (r'^第.条\s*附论', 3.0)],
    141: [(r'^家庭社会的法权之第三款', 4.0), (r'^一切可以从契约中获得', 4.0), (r'^第三篇', 4.0)],
    58: [(r'^纯粹实践理性的基本法则', 8.5)],
    90: [(r'^一切可以从契约中获得', 7.4)],
    203: [(r'^附录', 9.0)],
    251: [(r'^第.部分', 4.5)],
    267: [(r'^(解说|定理|原理)\d*$', 4.5)], 268: [(r'^(解说|定理|原理)\d*$', 4.5)],
    276: [(r'^[甲乙丙丁戊]、', 8.6)],
    12: [(r'^第[一二]卷', 4.0), (r'^第[一二三]篇', 5.0), (r'^导论：论一般而言的先验判断力', 5.0), (r'^附录', 5.0), (r'^导言$', 4.0)],
    269: [(r'^(解说|定理|原理)\d*$', 4.5)], 270: [(r'^(解说|定理|原理)\d*$', 4.5)],
    234: [(r'^[一二三四五六七八九十]+、', 9.4), (r'^附录', 9.0)],
    93: [(r'^法权论的形而上学初始根据的解释性附释', 7.4)],
}
# obvious misprints of the source in heading text: (part, old) -> new
TITLE_FIX = {
    (130, '重新提出的问题：人类是否在'): '重新提出的问题：人类是否在不断地向着更善进步？',     # title cut off; full text in vol 5 (part 152)
    (58, '第一部 分纯粹实践理性的要素论'): '第一部分 纯粹实践理性的要素论',      # ordinal '第一部分' broken by a space
    (64, '纯粹实践理性的要素论'): '纯然理性界限内的宗教',                                     # wrong copy of the previous work's title; the same work is titled so in vol 9
}
# headings that are really lines of a letter (address / salutation): part -> [(regex, style)]
STYLE_FIX = {
    108: [(r'^尊贵的骑兵上尉夫人', 'center'), (r'^慈和的夫人', 'noindent')],
    7: [(r'^(BACO DEVERULAMIO|Instauratio|《伟大的复兴》序言|维鲁兰姆的培根)', 'center')],
    8: [(r'^(献给|王家国务大臣|策德利茨男爵阁下)', 'center')],
    241: [(r'^(尊贵的先生|博学的、经验丰富的博士先生|至堪敬慕的保护人)', 'noindent')],
    249: [(r'^(最尊贵、最强大的国王|最仁慈的国王和君主)', 'noindent')],
    252: [(r'^第一部分\u3000关于恒星中的系统状态', 'center')],
}
TITLE_LOG = []


def fix_titles(els, n):
    """Misprints in heading text (see TITLE_FIX), titles typed twice, ordinal gaps."""
    for b in els:
        if b['k'] != 'h':
            continue
        t = plain(b['runs'])
        for (pn, old), new in TITLE_FIX.items():
            if pn == n and t == old:
                b['runs'] = [run(new)]
                TITLE_LOG.append((n, old, new))
        new_runs, dup = dedupe_title(b['runs'])
        if dup:
            TITLE_LOG.append((n, plain(b['runs']), plain(new_runs)))
            b['runs'] = new_runs
        b['runs'] = regap_heading(b['runs'])
    return els


def unit_blocks(unit, v):
    """Final blocks of a text unit: ordinals merged, ranks assigned."""
    els = merge_ordinals([dict(b) for b in unit['els']])
    ov = []
    for n in unit['parts']:
        ov += OVERRIDES.get(n, [])
    rank_headings(els, ov)
    for b in els:
        if b['k'] == 'h' and BARE_NUM.match(plain(b['runs']).replace('\u3000', '').replace(' ', '')):
            b['style'] = 'secn'
    return els
