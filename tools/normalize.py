"""Normalization of the parsed blocks: heading ranks, number/title spacing, short-line alignment,
broken paragraphs, verse, note markers, Greek text."""
import re
import copy
from .model import run, merge_runs, runs_text, BR, OBJ
from . import extract

CN = '一二三四五六七八九十百零〇'
GAP_CJK = '　'      # ideographic space: 1 em, never collapsed by CSS
GAP_EN = ' '       # en space: 0.5 em, never collapsed by CSS

END = set('。！？；：…”’）】〕」』.!?—》')
MARKER_RE = re.compile(r'^[\[［]\d+[\]］]$')


def text_of(b):
    return runs_text(b['runs'])


def is_marker_run(r):
    return bool(r.get('h') or r.get('a')) and bool(MARKER_RE.match(r['t'].strip()))


# ------------------------------------------------------------------------------------------ headings
# (regex on the plain heading text, rank)   ranks: 1 module title .. 7 smallest
BOOK_RANKS = {
    'b1': [
        (r'^[ABC][.．]', 2),
        (r'^[Ⅰ-Ⅳ][.．]', 3),
        (r'^（[a-c]）', 3),
        (r'^（\d+）', 4),
    ],
    'b2': [
        (r'^第[%s]+部分' % CN, 2),
        (r'^第[%s]+章' % CN, 2),
        (r'^第[%s]+节' % CN, 3),
    ],
    'b3': [
        (r'^〔?[一二三四五六七八九十]+、', 3),
        (r'^[ABC][.．]', 4),
        (r'^（[a-c]）', 5),
        (r'^〔[Ⅰ-Ⅳ][.．]', 6),
        (r'^〔\d+[.．]', 7),
        (r'^〔结束语〕', 7),
    ],
    'b4': [
        (r'^第[%s]+部' % CN, 1),
        (r'^第[%s]+篇' % CN, 2),
        (r'^第[%s]+[期章]' % CN, 3),
        (r'^〔[引七分]', 3),
        (r'^[甲乙丙丁戊己][\s　]', 4),
        (r'^〔?[%s]+[\s　]' % CN, 5),
        (r'^\d+[.．]', 6),
    ],
}

# number patterns used to insert a robust visual gap between the ordinal and the heading text
NUM_PATTERNS = [
    (re.compile(r'^(第[%s\d]+[部篇章节期阶段](?:分)?)[\s　]*(?=\S)' % CN), GAP_CJK),
    (re.compile(r'^([甲乙丙丁戊己庚辛])[\s　]*(?=[^\s、.．])'), GAP_CJK),
    (re.compile(r'^([%s]+)[\s　]+(?=\S)' % CN), GAP_CJK),
    (re.compile(r'^(\d+[.．])[\s　]*(?=[^\d\s])'), GAP_EN),
    (re.compile(r'^([A-Z][.．])[\s　]*(?=\S)'), GAP_EN),
    (re.compile(r'^([Ⅰ-Ⅳ][.．])[\s　]*(?=\S)'), GAP_EN),
    (re.compile(r'^(（[a-z\d%s]+）)[\s　]*(?=\S)' % CN), GAP_EN),
    (re.compile(r'^([%s]+、)[\s　]*(?=\S)' % CN), ''),
]


def rank_for(text, book_id, default):
    for pat, rank in BOOK_RANKS.get(book_id, []):
        if re.match(pat, text):
            return rank
    return default


def regap_heading(runs):
    """Normalize the separator between an ordinal and the title text (keeps the ordinal, puts one solid gap)."""
    if not runs:
        return runs
    # work on the first text run only (ordinals never span runs)
    first = runs[0]
    t = first['t']
    prefix = ''
    if t.startswith('〔'):
        prefix, t = '〔', t[1:]
    for pat, gap in NUM_PATTERNS:
        m = pat.match(t)
        if m:
            num = m.group(1)
            rest = t[m.end():]
            new = prefix + num + gap + rest
            return [dict(first, t=new)] + runs[1:]
    return runs


# ------------------------------------------------------------------------------------------ Greek
GREEK = {
    # image file -> text.  see docs/greek-ocr.md for the reading of each image
    'image01996.jpeg': 'πάντα ῥεῖ',
    'image01997.jpeg': 'οὐδὲν μᾶλλον τὸ ὂν τοῦ μὴ ὄντος ἐστίν',
    'image01998.jpeg': 'τοῦ ἑτέρου',
    'image01999.jpeg': 'δύναμις',
    'image02000.jpeg': 'ἐνέργεια',
    'image02001.jpeg': 'εἱμαρμένη',
    'image02002.jpeg': 'νόησις νοήσεως',
}


def replace_greek(runs):
    out = []
    for r in runs:
        if r.get('i') in GREEK:
            nr = {k: v for k, v in r.items() if k not in ('i',)}
            nr['t'] = GREEK[r['i']]
            out.append(nr)
        else:
            out.append(r)
    return merge_runs(out)


# ------------------------------------------------------------------------------------------ paragraph merging
def strip_markers(text):
    while True:
        t2 = re.sub(r'[\[［]\d+[\]］]\s*$', '', text).rstrip()
        if t2 == text:
            return text
        text = t2


def merge_broken(blocks, log=None):
    """Merge a body paragraph that stops mid-sentence with the paragraph that continues it."""
    out = []
    i = 0
    while i < len(blocks):
        b = blocks[i]
        if (out and b['k'] == 'p' and b['style'] == 'body' and out[-1]['k'] == 'p' and out[-1]['style'] == 'body'
                and not b.get('nomerge') and not out[-1].get('nomerge')):
            a = out[-1]
            ta = strip_markers(text_of(a))
            tb = text_of(b)
            starts_with_note = b['runs'] and is_marker_run(b['runs'][0]) and b['runs'][0].get('a')
            if (len(ta) >= 20 and ta[-1] not in END and not starts_with_note and len(tb) >= 1
                    and (tb[0] in '，、。；：）”’！？' or (len(text_of(a)) >= 30 and len(tb) >= 3
                                                            and not re.match(r'^[（〔\[［\d一二三四五六七八九十甲乙丙]', tb)))):
                if log is not None:
                    log.append(('merge', ta[-12:], tb[:12]))
                out[-1] = dict(a, runs=merge_runs(a['runs'] + b['runs']))
                i += 1
                continue
        out.append(b)
        i += 1
    return out


# ------------------------------------------------------------------------------------------ title balancing
def _w(ch):
    """Rough advance width of a character in em."""
    if ord(ch) < 0x2000:
        if ch in ' ':
            return 0.28
        if ch in 'ilI.,;:!\'|jtf()[]':
            return 0.32
        if ch in 'mwMW':
            return 0.85
        if ch.isupper() or ch.isdigit():
            return 0.62
        return 0.52
    if ch == ' ':
        return 0.5
    return 1.0


def _breakable(text, i):
    """May a line end before text[i]?"""
    if i <= 0 or i >= len(text):
        return False
    a, b = text[i - 1], text[i]
    if b in '，。、；：！？）〕】》”’」』…—·.,;:!?)]':
        return False
    if a in '（〔【《“‘「『([':
        return False
    if ord(a) < 0x2000 and ord(b) < 0x2000 and a != ' ' and b != ' ':
        return False        # inside a Latin word / number
    return True


def balance_title(runs, fs, avail_pt, slack=0.94):
    """Insert forced line breaks so that a long title breaks into balanced, sensible lines."""
    text = runs_text(runs)
    if BR in text:
        return runs
    cap = avail_pt * slack / fs
    widths = [_w(c) for c in text]
    total = sum(widths)
    if total <= cap:
        return runs
    n_lines = int(total // cap) + 1
    # nesting depth of brackets / title marks at every offset
    depth = [0] * (len(text) + 1)
    d = 0
    for i, ch in enumerate(text):
        if ch in '（《〔(':
            d += 1
        depth[i] = d
        if ch in '）》〕)':
            d -= 1
    import itertools
    idx = [i for i in range(1, len(text)) if _breakable(text, i)]
    best = None
    for k in range(n_lines, n_lines + 2):
        for cuts in itertools.combinations(idx, k - 1):
            bounds = (0,) + cuts + (len(text),)
            ws = [sum(widths[bounds[j]:bounds[j + 1]]) - (0.28 if text[bounds[j + 1] - 1] == ' ' else 0)
                  for j in range(k)]
            if max(ws) > cap:
                continue
            score = (max(ws) - min(ws)) * 0.6
            for c in cuts:
                a, b = text[c - 1], text[c]
                if depth[c] > 0 and depth[c - 1] > 0:
                    score += 5.0 if ('《' in text[:c] and '》' in text[c:]) else 3.0
                if a in '：；，、' or a == '\u3000':
                    score -= 3.0
                elif b in '（〔《':
                    score -= 2.5
                elif a == ' ':
                    score -= 0.0
                elif ord(a) < 0x2000 and a != ' ':
                    score += 1.0
                if a == ' ' or b == ' ':
                    score += 1.5
                # do not strand very short pieces
            if min(ws) < 3.5:
                score += 6.0
            key = (k, score)
            if best is None or key < best[0]:
                best = (key, cuts)
        if best:
            break
    if not best:
        return runs
    cuts = set(best[1])
    # rebuild runs with BR runs at the cut offsets (drop a space that sits on the cut)
    out, pos = [], 0
    for r in runs:
        t = r['t']
        seg = ''
        for j, ch in enumerate(t):
            if pos + j in cuts:
                if seg:
                    out.append(dict(r, t=seg))
                out.append(run(BR))
                seg = ''
                if ch == ' ':
                    continue
            seg += ch
        if seg:
            out.append(dict(r, t=seg))
        pos += len(t)
    res = []
    for r in out:      # strip spaces next to breaks
        res.append(r)
    return merge_runs(res)


# ------------------------------------------------------------------------------------------ per-part pipeline
SRC_LEVEL = {'h1': 1, 'h2': 1, 'h3': 2, 'h4': 3, 'h5': 4, 'h6': 5}
SHORT = 46


def _src_tag(b):
    return b.get('src', '').split('.')[0]


def to_heading(b, rank):
    b = dict(b)
    b['k'] = 'h'
    b['style'] = f'h{rank}'
    b['rank'] = rank
    return b


def apply_fixes(blocks, fixes):
    """fixes: list of tuples applied on the original block indexes (so they stay stable)."""
    blocks = [dict(b, idx=i) for i, b in enumerate(blocks)]
    drop = set()
    for f in fixes or []:
        op = f[0]
        if op == 'style':                 # ('style', idx_or_range, style)
            for i in _rng(f[1]):
                blocks[i]['style'] = f[2]
                if blocks[i]['k'] == 'h':
                    blocks[i]['k'] = 'p'
        elif op == 'rank':                # ('rank', idx_or_range, rank)
            for i in _rng(f[1]):
                blocks[i] = to_heading(blocks[i], f[2])
        elif op == 'join':                # ('join', i, j, sep): heading-continuation lines merged into block i
            i, j = f[1], f[2]
            sep = f[3] if len(f) > 3 else GAP_CJK
            runs = list(blocks[i]['runs'])
            for k in range(i + 1, j + 1):
                runs += [run(sep)] + list(blocks[k]['runs']) if sep else list(blocks[k]['runs'])
                drop.add(k)
            blocks[i]['runs'] = merge_runs(runs)
        elif op == 'merge':               # ('merge', i, j): paragraph j continues i
            i, j = f[1], f[2]
            blocks[i]['runs'] = merge_runs(blocks[i]['runs'] + blocks[j]['runs'])
            drop.add(j)
        elif op == 'drop':
            for i in _rng(f[1]):
                drop.add(i)
        elif op == 'set':                 # ('set', idx_or_range, {key: value})
            for i in _rng(f[1]):
                blocks[i].update(f[2])
        else:
            raise ValueError(op)
    return [b for i, b in enumerate(blocks) if i not in drop]


def _rng(x):
    if isinstance(x, int):
        return [x]
    if isinstance(x, tuple):
        return list(range(x[0], x[1] + 1))
    return list(x)


def is_note_start(b):
    return bool(b['runs']) and is_marker_run(b['runs'][0]) and bool(b['runs'][0].get('a')) \
        and bool(re.match(r'^[\[［]\d+[\]］]', b['runs'][0]['t']))


def process_part(part, book_id, fixes=(), heading_default=True, merge=True, log=None):
    """parse_part + fixes + heading ranks + spacing; returns list of blocks ready for typesetting."""
    blocks = apply_fixes(extract.parse_part(part), fixes)
    first_src = None
    out = []
    for b in blocks:
        b = dict(b)
        b['runs'] = replace_greek(b['runs'])
        t = text_of(b)
        # headings coming from real <h*> tags
        if b['k'] == 'h' and 'rank' not in b:
            lvl = SRC_LEVEL[_src_tag(b)]
            if first_src is None:
                first_src = lvl
            rank = max(1, lvl - first_src + 1)
            b = to_heading(b, rank_for(t, book_id, rank))
        elif b['k'] == 'p' and b['style'] in ('body', 'noindent', 'center') and heading_default and len(t) <= SHORT \
                and t and t[-1] not in '。！？；：，、' and not is_note_start(b):
            for pat, rank in BOOK_RANKS.get(book_id, []):
                if re.match(pat, t) and not b.get('nohead'):
                    b = to_heading(b, rank)
                    break
        out.append(b)
    blocks = out
    if merge:
        blocks = merge_broken(blocks, log)
    return blocks


def finish_headings(blocks):
    """Ordinal gap + balanced line breaks for all headings."""
    from .layout import STYLES
    for b in blocks:
        if b['k'] != 'h':
            continue
        st = STYLES[b['style']]
        b['runs'] = regap_heading(b['runs'])
        avail = 294 - (st['left'] + st['right']) * st['fs']
        if st['align'] == 'c' or b['rank'] <= 2:
            b['runs'] = balance_title(b['runs'], st['fs'], avail)
    return blocks


# ------------------------------------------------------------------------------------------ alignment passes
def group_verse(blocks, max_chars=26):
    """Short quote lines (poetry, dicta, schematic lists) become 'verse' lines: left-aligned, uniform indent, no justification."""
    out = []
    for b in blocks:
        if b['k'] == 'p' and b['style'] == 'quote':
            n = len(strip_markers(text_of(b)))
            if n <= max_chars:
                b = dict(b, style='verse')
        out.append(b)
    return out


def keep_signatures(blocks):
    """Consecutive right-aligned lines (name / place / date) stay together and never start a page on their own."""
    i = 0
    while i < len(blocks):
        if blocks[i]['k'] == 'p' and blocks[i]['style'] == 'right':
            j = i
            while j + 1 < len(blocks) and blocks[j + 1]['k'] == 'p' and blocks[j + 1]['style'] == 'right':
                j += 1
            for k in range(i, j + 1):
                blocks[k]['nostart'] = True
                if k < j:
                    blocks[k]['keep'] = 1
            i = j + 1
        else:
            i += 1
    return blocks


def wrap_short_lines(blocks):
    """Right/centre aligned single lines that are too long for one line get balanced manual line breaks."""
    from .layout import STYLES
    for b in blocks:
        if b['k'] == 'p' and b['style'] in ('right', 'center') and BR not in text_of(b):
            st = STYLES[b['style']]
            avail = 294 - (st['left'] + st['right']) * st['fs']
            b['runs'] = balance_title(b['runs'], st['fs'], avail, slack=0.9)
    return blocks


def postprocess(blocks):
    blocks = group_verse(blocks)
    blocks = wrap_short_lines(blocks)
    blocks = keep_signatures(blocks)
    return blocks
