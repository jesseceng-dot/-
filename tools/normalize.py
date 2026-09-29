"""Normalization of the parsed blocks: heading ranks, number/title spacing, short-line alignment,
broken paragraphs, verse, note markers, Greek text."""
import re
import copy
from .model import run, merge_runs, runs_text, BR, OBJ
from . import extract

CN = '一二三四五六七八九十百零〇'
GAP_CJK = '　'      # ideographic space: 1 em, never collapsed by CSS
GAP_EN = ' '       # en space: 0.5 em, never collapsed by CSS

END = set('。！？；：…”’）】〕」』.!?—》］]．')
MERGES = []          # (part, 'merge', tail of first paragraph, head of second) for the disposition report
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
        (r'^[一二三四五六七八九十]$', 5),
        (r'^第[一二三四五六七八九十]+：〔', 6),
        (r'^\d+[.．]', 6),
    ],
}

# number patterns used to insert a robust visual gap between the ordinal and the heading text
NUM_PATTERNS = [
    (re.compile(r'^(第[%s\d]+[部篇章节期阶段](?:分)?)[\s　]*(?=\S)' % CN), GAP_CJK),
    (re.compile(r'^([甲乙丙丁戊己庚辛])[\s　]*(?=[^\s、.．（(])'), GAP_CJK),
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
        t2 = re.sub(r'\u2060?[\[［](?:\d+|注[一二三四五六七八九十]+)[\]］]\s*$', '', text).rstrip('\u2060 ')
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


def _word_boundaries(text, idx):
    """Keep only cut positions that fall between words (Chinese word segmentation), when available."""
    try:
        import rjieba
    except Exception:
        return idx
    bounds, pos = set(), 0
    for tok in rjieba.cut(text):
        pos += len(tok)
        bounds.add(pos)
    keep = [i for i in idx if i in bounds]
    return keep if len(keep) >= 2 else idx


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
    idx = _word_boundaries(text, idx)
    best = None
    from math import comb
    for k in range(n_lines, n_lines + 3):
        if comb(len(idx), k - 1) > 150000:
            continue
        for cuts in itertools.combinations(idx, k - 1):
            bounds = (0,) + cuts + (len(text),)
            ws = [sum(widths[bounds[j]:bounds[j + 1]]) - (0.28 if text[bounds[j + 1] - 1] == ' ' else 0)
                  for j in range(k)]
            if max(ws) > cap:
                continue
            score = (max(ws) - min(ws)) * 0.6 + 7.0 * (k - n_lines)
            for c in cuts:
                a_, b_ = text[c - 1], text[c]
                if depth[c] > 0 and depth[c - 1] > 0:
                    score += 9.0 if ('《' in text[:c] and '》' in text[c:]) else 3.0
                if (a_ in '年月' and b_.isdigit()) or (a_.isdigit() and b_ in '年月日'):
                    score += 8.0                    # never split a date
                if a_ == '》':
                    score -= 3.0
                if a_ == '）' and '（' in text[max(0, c - 5):c]:
                    score += 5.0                    # keep a short ordinal like （a） with the words after it
                if a_ in '：；':
                    score -= 6.0
                elif a_ in '，、）' or a_ == '\u3000':
                    score -= 3.0
                elif b_ in '（〔《':
                    score -= 2.5
                elif ord(a_) < 0x2000 and a_ != ' ':
                    score += 1.0
                if a_ in '的与和及而或之在于对' and a_ != '\u3000':
                    score -= 1.2
                if b_ in '的之而':
                    score += 2.5
                if a_ == ' ' or b_ == ' ':
                    score += 1.5
            if min(ws) < 3.5:
                score += 6.0
            if best is None or score < best[0]:
                best = (score, cuts)
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
    b['runs'] = merge_runs([{k: v for k, v in r.items() if k != 'b'} for r in b['runs']])
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
        elif op == 'gap':                 # ('gap', idx): jammed ordinal like '七有关…' -> '七　有关…'
            for i in _rng(f[1]):
                r0 = blocks[i]['runs'][0]
                m = re.match(r'^([%s]+)(?=[^%s\s、.．])' % (CN, CN), r0['t'])
                if m:
                    blocks[i]['runs'][0] = dict(r0, t=m.group(1) + GAP_CJK + r0['t'][m.end():])
        elif op == 'lstrip':              # ('lstrip', idxs): drop leading ideographic spaces
            for i in _rng(f[1]):
                r0 = blocks[i]['runs'][0]
                blocks[i]['runs'][0] = dict(r0, t=r0['t'].lstrip('\u3000 '))
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


def process_part(part, book_id, fixes=(), heading_default=True, merge=True, log=None, ranks=(), gapnum=(), styles=()):
    """parse_part + fixes + heading ranks + spacing; returns list of blocks ready for typesetting."""
    blocks = apply_fixes(extract.parse_part(part), fixes)
    first_src = None
    out = []
    for b in blocks:
        b = dict(b)
        b['runs'] = fix_typos(fix_dates(replace_greek(b['runs'])))
        t = text_of(b)
        if b['k'] == 'p' and b['style'] in ('body', 'noindent', 'center') and len(t) <= 60:
            if SEP_RE.match(t):
                b['style'] = 'sep'
                b['nohead'] = True
            for pat, st in styles:
                if re.search(pat, t):
                    b['style'] = st
                    b['nohead'] = True
                    break
        # headings coming from real <h*> tags
        if b['k'] == 'h' and 'rank' not in b:
            lvl = SRC_LEVEL[_src_tag(b)]
            if first_src is None:
                first_src = lvl
            rank = max(1, lvl - first_src + 1)
            b = to_heading(b, rank_for(t, book_id, rank))
        elif b['k'] == 'p' and b['style'] in ('body', 'noindent', 'center') and heading_default and len(t) <= SHORT \
                and t and t[-1] not in '。！？；：，、' and not is_note_start(b):
            for pat, rank in list(ranks) + BOOK_RANKS.get(book_id, []):
                if re.match(pat, t) and not b.get('nohead'):
                    b = to_heading(b, rank)
                    break
        out.append(b)
    blocks = out
    if blocks and blocks[0]['k'] == 'h' and blocks[0].get('rank', 1) > 1:
        blocks[0] = to_heading(blocks[0], 1)          # the first heading of a module is its title
    if merge:
        lg = []
        blocks = merge_broken(blocks, lg)
        MERGES.extend((part,) + x for x in lg)
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
    """Right/centre aligned single lines that are too long for one line get sensible manual line breaks:
    after a closing bracket (date | signature) when both parts fit, otherwise balanced."""
    from .layout import STYLES
    for b in blocks:
        if b['k'] == 'p' and b['style'] in ('right', 'center', 'epi') and BR not in text_of(b) and len(text_of(b)) <= 90:
            st = STYLES[b['style']]
            avail = 294 - (st['left'] + st['right']) * st['fs']
            text = text_of(b)
            cap = avail * 0.9 / st['fs']
            if sum(_w(c) for c in text) <= cap:
                continue
            cuts = [i + 1 for i, c in enumerate(text[:-1]) if c in '）)' and i + 1 >= 4 and text[i + 1] not in '，。、；：！？）》”』」']
            done = False
            for c in cuts:
                if sum(_w(x) for x in text[:c]) <= cap and sum(_w(x) for x in text[c:]) <= cap:
                    b['runs'] = _cut_runs(b['runs'], {c})
                    done = True
                    break
            if not done:
                b['runs'] = balance_title(b['runs'], st['fs'], avail, slack=0.9)
    return blocks


def _cut_runs(runs, cuts):
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
            seg += ch
        if seg:
            out.append(dict(r, t=seg))
        pos += len(t)
    return merge_runs(out)


def postprocess(blocks):
    blocks = group_verse(blocks)
    blocks = wrap_short_lines(blocks)
    blocks = keep_signatures(blocks)
    return blocks


# ------------------------------------------------------------------------------------------ notes
def mark_markers(blocks):
    """Footnote/endnote markers that are plain bracketed links become superscripts (like the marker spans of Book 1)."""
    for b in blocks:
        if b['k'] not in ('p', 'h'):
            continue
        runs = []
        for idx, r in enumerate(b['runs']):
            if (r.get('h') or r.get('a')) and MARKER_RE.match(r['t'].strip()) and not r.get('s'):
                if idx == 0 and is_note_start(b):
                    runs.append(r)
                    continue
                r = dict(r, s=1, t='\u2060' + r['t'] if not r['t'].startswith('\u2060') else r['t'])
                if r.get('h') and not r.get('a') and re.search(r'#b-\d+$', r['h']):
                    r['a'] = r['h'].replace('#b-', '#a-')      # some markers lost their anchor id in the source
            runs.append(r)
        b['runs'] = runs
    return blocks


def split_notes(blocks):
    """Split trailing note entries (paragraphs starting with a numbered back-link) off a chapter."""
    starts = [i for i, b in enumerate(blocks) if b['k'] == 'p' and is_note_start(b)]
    if not starts:
        return blocks, []
    n = len(blocks)
    for s in starts:
        after = blocks[s:]
        share = sum(1 for b in after if is_note_start(b)) / len(after)
        if share >= 0.6 and s >= 0.3 * n:
            return blocks[:s], blocks[s:]
    return blocks, []


def repair_note_links(notes, part):
    """A few note entries carry a placeholder href; point them at the marker `a-N` they belong to."""
    for b in notes:
        if not (b['runs'] and is_note_start(b)):
            continue
        r = b['runs'][0]
        m = re.match(r'^[\[［](\d+)[\]］]', r['t'])
        want = f'{part}#a-{m.group(1)}'
        if not r.get('h') or r['h'] == part:
            r['h'] = want
    return notes


def note_blocks(notes):
    out = []
    for b in notes:
        b = dict(b)
        if is_note_start(b):
            r0 = dict(b['runs'][0], c='nn')
            b['runs'] = [r0] + b['runs'][1:]
            b['style'] = 'note'
        elif b['style'] == 'right':
            b['style'] = 'noter'
        elif b['style'] in ('quote', 'verse'):
            b['style'] = 'notev'
        else:
            b['style'] = 'notec'
        out.append(b)
    return out


SEP_RE = re.compile(r'^\*(?:[\s\u3000]*\*)+$')


# Kindle private-use glyphs that stand for real characters (read from their context)
# hyphens that only exist because the printed original broke the word at a line end (rejoin the word)
PRINT_HYPHENS = {
    'Vor-stellung': 'Vorstellung', 'Philosophisch-en': 'Philosophischen', 'gen-erosus': 'generosus',
    'Philoso-phus': 'Philosophus', 'Nachden-ken': 'Nachdenken', 'intel-lectu': 'intellectu',
    'Aus-sereinander': 'Aussereinander', 'Nebenein-ander': 'Nebeneinander', 'En-tzweiung': 'Entzweiung',
    'Geschmack-surteil': 'Geschmacksurteil', 'me-dius': 'medius', 'Handels-spekula-tion': 'Handelsspekulation',
    'Handels-spekulation': 'Handelsspekulation', 'Be-sonderheit': 'Besonderheit', 'Lu-cian': 'Lucian',
    'Aristo-gitone': 'Aristogitone', 'Mari-vaux': 'Marivaux', 'pheno-menology': 'phenomenology',
    'Ges-talten': 'Gestalten', 'Loe-wenberg': 'Loewenberg', 'Bewu-ßtsein': 'Bewußtsein',
    'Repro-duktion': 'Reproduktion', 'ein-fache': 'einfache',
}
PUA_MAP = {'\ue19c': '畠', '\ue54f': 'ö', '\ue837': '抽'}
# plain misprints of the source (checked against the other volumes / the surrounding text)
TYPOS = {
    '上海上民出版社': '上海人民出版社',            # CIP line of 《小逻辑》 (the other three volumes read 上海人民出版社)
    '1811年7月29日子纽伦堡': '1811年7月29日于纽伦堡',   # letter heading: 'in Nürnberg'
}


def fix_typos(runs):
    out = []
    for r in runs:
        t = r['t']
        for k, v in TYPOS.items():
            t = t.replace(k, v)
        out.append(dict(r, t=t) if t != r['t'] else r)
    return out


# Latin / German / French / Sanskrit words in which the ebook replaced the umlaut, ß, ç, ö ... by a full stop ('Bartholom.us')
DROPOUTS = {
    'Encyclop-die': 'Encyclopädie', 'Sadduc.ismus': 'Sadducäismus', 'Mus.us': 'Musäus', 'Tr.ster': 'Tröster',
    'verkl.rt': 'verklärt', 'simpli.ed': 'simplified',
    'Vers.hnung': 'Versöhnung', 'Ph.nix': 'Phönix', 'Vis.nu': 'Viṣṇu', 'Vi.nu': 'Viṣṇu', 'Māhe.vara': 'Māheśvara',
    'Mahe.vara': 'Maheśvara', 'a.akti': 'aśakti', 'Ke.ava': 'Keśava', 'pratij.a': 'pratijñā', 'Vikram.ditya': 'Vikramāditya',
    'Substantialit.t': 'Substantialität', 'La.rtius': 'Laërtius', 'Dic.archos': 'Dicäarchos', 'Eud.monismus': 'Eudämonismus',
    'Dioch.tes': 'Diochätes', 'Po.sis': 'Poësis', 'Stob.us': 'Stobäus', 'Pal.stina': 'Palästina', 'Kr.sus': 'Krösus',
    'Alkm.on': 'Alkmäon', 'Laced.mon': 'Lacedämon', 'Pharis.er': 'Pharisäer', 'Chald.en': 'Chaldäen', 'Chald.a': 'Chaldäa',
    'Neupythagor.er': 'Neupythagoräer', 'Eub.a': 'Euböa', 'Wiedert.ufer': 'Wiedertäufer', 'Ptolem.er': 'Ptolemäer',
    'Ptolem.us': 'Ptolemäus', 'Pir.us': 'Piräus', 'Potid.a': 'Potidäa', 'The.tet': 'Theätet', 'Qu.ker': 'Quäker',
    'Ph.bus': 'Phöbus', 'Bartholom.us': 'Bartholomäus', 'Bollst.dt': 'Bollstädt', 'Gfr.rer': 'Gfrörer', 'Tim.us': 'Timäus',
    'Helmst.dt': 'Helmstädt', 'Manich.ismus': 'Manichäismus', 'Seh.nborn': 'Schönborn', 'Fran.ois': 'François',
    'Qualit.t': 'Qualität', 'Quallit.t': 'Quallität', 'Spontaneit.t': 'Spontaneität', 'Verm.gen': 'Vermögen',
    'Passitivit.t': 'Passivität', 'Ver.nderlichkeit': 'Veränderlichkeit', 'Unver.nderlichkeit': 'Unveränderlichkeit',
    'Ver.nderung': 'Veränderung', 'Ma.tab': 'Maßstab', 'Ma.stab': 'Maßstab',
    'Nichtgefa .twerdenk.nnen': 'Nichtgefaßtwerdenkönnen', 'Unverst.ndichste': 'Unverständlichste',
    'Unvest.ndlichkeit': 'Unverständlichkeit', 'Grunds.tze': 'Grundsätze', 'Grunds.tz': 'Grundsatz', 'Sch.pfung': 'Schöpfung',
    'Sch.pfer': 'Schöpfer', 'Originalit.t': 'Originalität', 'h.chstes': 'höchstes', 'h.chste': 'höchste',
    'Gegens.tzen': 'Gegensätzen', 'Duplizit.t': 'Duplizität', 'Immaterialit.t': 'Immaterialität', 'Negativit.t': 'Negativität',
    'kompendi.s': 'kompendiös', 'Rezeptivit.t': 'Rezeptivität', 'Verh.ltnis': 'Verhältnis', 'pr.stabilierte': 'prästabilierte',
    'Ged.chtnis': 'Gedächtnis', 'Aufl.ssung': 'Auflösung', 'm.gliche': 'mögliche', 'Idealit.t': 'Idealität',
    'Kontinuit.t': 'Kontinuität', 'Zusammenh.ngende': 'Zusammenhängende', 'Sch.ne': 'Schöne', 't.tige': 'tätige',
    'Erkenntnisverm.gen': 'Erkenntnisvermögen', 'Zuf.lligkeit': 'Zufälligkeit', 'Zuf.llige': 'Zufällige',
    'Realit.t': 'Realität', 'Reatit.t': 'Realität', 'Aufkl.rung': 'Aufklärung', 'Pr.szienz': 'Präszienz',
    'Totalit.t': 'Totalität', 'Tatalit.t': 'Totalität', 'Autorit.t': 'Autorität', 'Gewi.heit': 'Gewißheit',
    'Pers.nlichkeit': 'Persönlichkeit', 'Wahrnehmungsverm.gen': 'Wahrnehmungsvermögen', 'Trinit.t': 'Trinität',
    'Triplizit.t': 'Triplizität', 'Verkl.rung': 'Verklärung', 'Enlit.t': 'Entität', 'gegenst.ndlichen': 'gegenständlichen',
    'Gegenw.rtige': 'Gegenwärtige', 'lntellektualit.t': 'Intellektualität', 'Partikularit.t': 'Partikularität',
    'Identit.t': 'Identität', 'blo.e': 'bloße', '.u.erlichkeit': 'Äußerlichkeit', '.u.eres': 'Äußeres',
    '.u.erliche': 'äußerliche', '.u.erlich': 'äußerlich', 'St.rke': 'Stärke', 'Ph.nomene': 'Phänomene', 'prim.re': 'primäre',
    'sekund.re': 'sekundäre', 'Abh.ngigkeit': 'Abhängigkeit', 'Bewu.tsein': 'Bewußtsein', 'n.chste': 'nächste',
    'Kausalit.t': 'Kausalität', 'Subjektivit.t': 'Subjektivität', 'Objektivit.t': 'Objektivität', 'Fr.mmigkeit': 'Frömmigkeit',
    'religi.sen': 'religiösen',
    'SchluΒder': 'Schluß der', 'SchluΒin': 'Schluß in',      # ß typed as Greek beta, a space lost
}
_DROP_RE = re.compile(r'(?<![A-Za-zÀ-ÿ])(' + '|'.join(re.escape(k) for k in sorted(DROPOUTS, key=len, reverse=True)) +
                      r')(?![A-Za-zÀ-ÿ])')


_SS_RE = re.compile(r'(?<=[A-Za-zÄÖÜäöü])[βΒ]')


def repair_words(runs, book_digit):
    """Typos, dropped-letter foreign words and Greek words of one run list (applied to every text module of a book)."""
    from . import greekfix
    out = []
    for r in runs:
        t = r['t']
        for k, v in TYPOS.items():
            t = t.replace(k, v)
        t = _DROP_RE.sub(lambda m: DROPOUTS[m.group(1)], t)
        t = _SS_RE.sub('ß', t)                                   # 'MaΒ', 'Gröβe': Greek beta typed for German ß
        t = greekfix.restore(t, book_digit)
        out.append(dict(r, t=t) if t != r['t'] else r)
    return out


def fix_dates(runs):
    """'1816 年10 月28 日' -> '1816年10月28日' (stray spaces inside a date are a typesetting error of the source);
    private-use glyphs of the ebook are replaced by the characters they stand for."""
    out = []
    for r in runs:
        t = r['t']
        for k, v in PUA_MAP.items():
            t = t.replace(k, v)
        for k, v in PRINT_HYPHENS.items():
            if k in t:
                t = t.replace(k, v)
        t = re.sub('出处页\u3000+码', '出处页码', t)
        t2 = re.sub(r'(?<=\d) (?=[年月日])', '', t)
        t2 = re.sub(r'(?<=[年月]) (?=\d)', '', t2)
        # ASCII space before a full-width closing mark / after a full-width opening bracket (source typo; it would let a
        # line start with '）' or '，' or leave a visible gap before the mark)
        t2 = re.sub(r'(?<=[A-Za-z0-9一-鿿]) +(?=[）】〕」』，。、；：！？》])', '', t2)
        t2 = re.sub(r'(?<=[（【〔「『《]) +(?=\S)', '', t2)
        t2 = re.sub(r'(?<=[，、；：]) +(?=[？！])', '', t2)          # '，？—1679' (unknown birth year in the index)
        out.append(dict(r, t=t2) if t2 != r['t'] else r)
    return out
