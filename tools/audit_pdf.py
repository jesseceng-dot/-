"""Checks of a finished PDF on its own (no build data needed), for re-examining delivered books:

    python -m tools.audit_pdf <a.pdf> [<b.pdf> ...]          # one summary line per PDF, details with -v

  sizes    page sizes used
  type3    Type3 fonts
  foot     a page whose content (text or picture) ends a line or more above the common last baseline, when the next
           page does not open a new section (its first line lower than usual, a heading, a picture page) -- a blank foot
  grid     body-size lines off the line grid of the page's own last baseline
  kinsoku  a line of body text that starts with a closing mark or ends with an opening one
  over     text beyond the common right edge of the text block (an overfull line, a table cell pushing out)
  edge     a page with ink of any text (a caption, a title page, a running head, a note) 1.5 pt or more outside the
           common edges of the text block, left or right
  col      on a page of two columns (an index), a line of the left column running into the gutter: past the right
           edge the left column would have if as wide as the right one, with a line of the right column beside it
  overlap  two lines of text drawn over each other
  lone     a line of nothing but punctuation or a note mark
  short    a page with only one or two lines that runs on from the page before (not a new section)
  head_bottom  a heading in the last two lines of a page with no text under it
  markstart  a raised note mark at the very start of a line
  numbreak a number broken at a dash or after 'p.' ('1797—' / '1798', 'pp.355—' / '361', '图7-' / '2'): not an error, a nicety
  split    a Latin word broken without a hyphen one letter after a hyphenation point ('Indiv' / 'idual'): the measuring
           of a line broken at a soft hyphen put the next letter on the line before (fixed in tools/measure.py); two
           words broken at their space can show up here too ('sensus' / 'communis'), look at each
  links    internal links whose target page does not exist
  joiner   word joiners drawn with a width (a gap before a note mark)
  empty    pages with neither text nor pictures
  apos     an apostrophe inside a Latin word drawn in a CJK face, whose ’ is full width ('Nature’ s')
"""
import collections
import re
import sys

import pymupdf

from .model import apostrophes
from .qa_pdf import joiners

NO_START = set('，。、；：！？）》」』”’】〕…,.;:!?)')
NO_END = set('（《「『“‘【〔(')
MARK = re.compile(r'(?:[\[［(（]?[\d注校]+[\]］)）]?)+')
NUM_END = re.compile(r'(\d[-–—~～－])$|(\bpp?\.)$')
FUNC = set('a and as at by de del der des di die das dem den du e el en et for from in is la le les of on or than the to und '
           'van von with zu'.split())                  # (a line broken before one of these is two words broken at their space)
URLISH = re.compile(r'https?:|www\.|\.(com|org|net|edu|gov|html?)\b|/')
LONE = re.compile(r'[^\w\s]+|[^\w\s]*[\[［(（]\d+[\]］)）][^\w\s]*|[①-⑳]+[^\w\s]*|\d{1,4}[)）\]］][^\w\s]*')


def _lines(pg):
    out = []
    for b in pg.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            sp = [s for s in l['spans'] if s['text'].strip() and set(s['text']) - set('• ')]   # (emphasis dots under a word, 着重号:
                                                                                             #  the text of the line above, not a line)
            if sp:
                out.append(dict(y=sp[0]['origin'][1], size=round(max(s['size'] for s in sp), 1), x0=l['bbox'][0],
                                x1=l['bbox'][2], y0=l['bbox'][1], y1=l['bbox'][3], text=''.join(s['text'] for s in sp),
                                font=sp[0]['font']))
    merged = []                                       # pieces of one line split by a raised note mark: one line again
    for l in sorted(out, key=lambda l: (round(l['y'], 1), l['x0'])):
        m = merged[-1] if merged else None
        if m and abs(m['y'] - l['y']) < 0.6 and abs(m['size'] - l['size']) < 0.6 and l['x0'] >= m['x0']:
            m.update(x1=max(m['x1'], l['x1']), text=m['text'] + l['text'], y0=min(m['y0'], l['y0']), y1=max(m['y1'], l['y1']))
        else:
            merged.append(dict(l))
    return merged


def _ink_x1(pg, l):
    """Right edge of the last visible character of a line (a trailing ideographic space has a box but no ink)."""
    x1 = 0
    for b in pg.get_text('rawdict')['blocks']:
        for ln in b.get('lines', []):
            for sp in ln['spans']:
                if abs(sp['origin'][1] - l['y']) < 0.6:
                    x1 = max([x1] + [c['bbox'][2] for c in sp['chars'] if not c['c'].isspace()])
    return x1


def _ink_lines(pg):
    """The lines of a page as drawn (the columns of a row are not merged), by their ink: a trailing ideographic space has
    a box but no ink; zero-width characters and emphasis dots (the line above's) do not count."""
    out = []
    for bl in pg.get_text('rawdict')['blocks']:
        for ln in bl.get('lines', []):
            cs = [c for sp in ln['spans'] for c in sp['chars'] if not c['c'].isspace() and c['c'] not in '\u200b\u2060']
            if cs and set(c['c'] for c in cs) - {'•'}:
                out.append(dict(x0=cs[0]['bbox'][0], x1=max(c['bbox'][2] for c in cs), y=ln['spans'][0]['origin'][1],
                                text=''.join(c['c'] for sp in ln['spans'] for c in sp['chars'])))
    return out


def audit(path):
    d = pymupdf.open(path)
    n = len(d)
    pages = [_lines(p) for p in d]
    imgs = [[im['bbox'] for im in p.get_image_info() if im['bbox'][3] - im['bbox'][1] > 8] for p in d]
    sizes = collections.Counter((round(p.rect.width, 1), round(p.rect.height, 1)) for p in d)
    fs = collections.Counter(l['size'] for ls in pages for l in ls)
    body = fs.most_common(1)[0][0] if fs else 10.5
    is_body = lambda l: abs(l['size'] - body) < 0.6
    bottoms = collections.Counter(round(max(l['y'] for l in ls if is_body(l)), 1) for ls in pages if any(is_body(l) for l in ls))
    ref = bottoms.most_common(1)[0][0] if bottoms else None
    tops = collections.Counter(round(min(l['y'] for l in ls if is_body(l)), 1) for ls in pages if any(is_body(l) for l in ls))
    top = tops.most_common(1)[0][0] if tops else None
    gaps = collections.Counter()
    for ls in pages:
        ys = sorted(set(round(l['y'], 2) for l in ls if is_body(l)))
        for a, b in zip(ys, ys[1:]):
            if 5 < b - a < 40:
                gaps[round(b - a, 1)] += 1
    pitch = gaps.most_common(1)[0][0] if gaps else 17.0
    right = collections.Counter(round(l['x1']) for ls in pages for l in ls if is_body(l))
    rmax = max((x for x, c in right.items() if c >= max(5, sum(right.values()) // 200)), default=0)
    left = collections.Counter(round(l['x0']) for ls in pages for l in ls if is_body(l))
    lmin = min((x for x, c in left.items() if c >= max(5, sum(left.values()) // 200)), default=0)
    serif = lambda l: any(k in l['font'] for k in ('Serif', 'WenKai', 'Song', 'Kai'))
    rep = collections.defaultdict(list)
    drawn = [_ink_lines(p) for p in d]
    mid = (lmin + rmax) / 2

    def col_start(raw):                                # where the right column of a page of two columns starts: many
        rcol = [l for l in raw if l['x0'] > mid + 2]   # lines start at one place (the piece of a line after a note mark
        st = [x for x, c in collections.Counter(round(l["x0"]) for l in rcol).items() if c >= 2]   # does not; book 67: a page with two
                                                                                              #  main entries in the right column)
        st = [x for x in st if 0.3 < (rmax - x) / max(1, rmax - lmin) < 0.55]   # (no page numbers of a contents page)
        return min(st) if st else None
    starts = collections.Counter(x for x in map(col_start, drawn) if x is not None)
    rstart = starts.most_common(1)[0][0] if starts else None   # (one place for the book: continuation lines start
    words = collections.Counter(w.lower() for p in d for w in re.findall(r'[A-Za-zÀ-ÿ]{2,}', p.get_text()))
    import pyphen
    hyph = [pyphen.Pyphen(lang=x) for x in ('en_US', 'de_DE', 'it')]

    def opens(i):                                      # does page i open a section?
        if i >= n:
            return True
        ls = pages[i]
        if not ls:
            return True                                # a picture page or a blank page
        if any(l['size'] >= body + 2.5 for l in ls if l['y'] < (top or 0) + 12 * pitch):
            return True                                # a heading in its upper part
        b = [l for l in ls if is_body(l)]
        if not b:
            return True
        first = min(l['y'] for l in b)
        return top is not None and first > top + 1.5 * pitch     # the first line lower than usual: a chapter sink
    for i, ls in enumerate(pages):
        if not ls and not imgs[i]:
            rep['empty'].append(i + 1)
            continue
        b = [l for l in ls if is_body(l)]
        folio = any(l['y'] > (ref or 0) + 0.9 * pitch and re.fullmatch(r'[0-9ivxlcdm]{1,6}', l['text'].strip()) for l in ls)
        # (a page without a page number is a page of its own design: a title page, a board, a dedication, a part page)
        bottom = max([l['y'] for l in b] + [im[3] - 0.25 * body for im in imgs[i]] + [l['y'] for l in ls if l['size'] < body - 0.6], default=0)
        if ref and b and folio and bottom < ref - 0.9 * pitch and i < n - 1 and not opens(i + 1):
            rep['foot'].append((i + 1, round((ref - bottom) / pitch, 1)))
        if ref and b and folio and not imgs[i]:
            pref = max(l['y'] for l in b)
            for l in b:
                if not serif(l):
                    continue                             # (headings in their own families sit in their slots)
                off = (pref - l['y']) % pitch
                if 0.3 < off < pitch - 0.3:
                    rep['grid'].append((i + 1, l['text'][:12]))
                    break
        for l in b:
            t = l['text'].strip()
            if t and len(t) > 3 and (t[0] in NO_START and l['x0'] < lmin + 2.5 * body
                                     and not (t.startswith('…') and l['x0'] > lmin + 1.5 * body)
                                     or t[-1] in NO_END and l['x1'] > rmax - 1.5 * body):
                rep['kinsoku'].append((i + 1, t[:14]))       # (only at the edges of the text block: a line after a raised mark starts mid-line;
                # an indented line that starts with '……' is a paragraph that does)
            if rmax and l['x1'] > rmax + 3 and _ink_x1(d[i], l) > rmax + 3:
                rep['over'].append((i + 1, t[:14], round(_ink_x1(d[i], l) - rmax, 1)))
        ink = drawn[i]
        if ink and lmin and rmax and (min(l['x0'] for l in ink) < lmin - 2 or max(l['x1'] for l in ink) > rmax + 2):
            rep['edge'].append((i + 1, round(min(l['x0'] for l in ink), 1), round(max(l['x1'] for l in ink), 1)))
        raw = drawn[i]
        if rstart and col_start(raw) is not None:
            rcol = [l for l in raw if l['x0'] > mid + 2]
            colr = lmin + (rmax - rstart)                          # (the columns are as wide as each other)
            if sum(1 for l in raw if l['x0'] < mid - 2 and abs(l['x1'] - colr) <= 3) >= 5:   # (a table, a derivation:
                for l in raw:                                                               #  no column ends there)
                    if l['x0'] < mid - 2 and l['x1'] > colr + 2 and any(abs(r['y'] - l['y']) < 0.6 * pitch for r in rcol):
                        rep['col'].append((i + 1, l['text'][:24], round(l['x1'] - colr, 1)))
        inside = [l for l in ls if top is not None and ref and top - 1 <= l['y'] <= ref + 1]
        for l in inside:
            t = l['text'].replace('\u2060', '').strip()
            if t and len(t) <= 5 and LONE.fullmatch(t) and not set(t) <= set('*＊∗※-—─_=# ') and not re.fullmatch(r'[◀▶]+\s*(?:[（(\[]\d+[)）\]])?', t) \
                    and not any(m is not l and abs(m['y'] - l['y']) < 0.8 * body for m in ls) \
                    and not (re.fullmatch(r'\[[\d*]+\]|[）)，。；：、]', t) and any(im[1] - 2 < l['y'] < im[3] + 2 and (im[0] < l['x0'] or im[0] > l['x1'] - 1) for im in imgs[i])):
                # (a row of asterisks or dashes: a section break; book 65: a note mark or a closing bracket after a line set as a picture;
                #  book 72: a note's number before the first line of a note set as a picture)
                rep['lone'].append((i + 1, t, round(l['y'])))               # a line of nothing but punctuation or a note mark (a raised mark beside its line is not one)
        if not imgs[i] and inside and all(abs(l['size'] - body) < 1.6 for l in inside) and len({round(l['y']) for l in inside}) <= 2 \
                and i > 0 and pages[i - 1] and not opens(i) and folio:
            rep['short'].append((i + 1, inside[0]['text'][:12]))     # a page with one or two lines, run on from the page before
        for l in ls:
            if l['size'] < body - 2 and MARK.fullmatch(l['text'].strip()) and abs(l['x0'] - lmin) < 1.5 \
                    and any(is_body(m) and 1 < m['y'] - l['y'] < 7 for m in ls):
                rep['markstart'].append((i + 1, l['text'].strip()))     # a raised note mark that opens a line
        seq = sorted((l for l in ls if l['size'] >= body - 2.5), key=lambda l: l['y'])
        spaced = None
        for a, c in zip(seq, seq[1:]):
            m1, m2 = re.search(r'([A-Za-zÀ-ÿ]+)$', a['text']), re.match(r'\s*([a-zà-ÿ]+)', c['text'])
            if m1 and m2 and spaced is None:               # lines whose last character is a space (broken at a space)
                spaced = {round(ln['spans'][0]['origin'][1]) for bl in d[i].get_text('rawdict')['blocks'] for ln in bl.get('lines', [])
                          if ln['spans'] and [ch for sp in ln['spans'] for ch in sp['chars']][-1:] and
                          [ch for sp in ln['spans'] for ch in sp['chars']][-1]['c'].isspace()}
            if m1 and m2 and 5 < c['y'] - a['y'] < 25 and round(a['y']) not in spaced \
                    and not (URLISH.search(a['text'][-40:]) or URLISH.search(c['text'][:40])):
                w1, w2 = m1.group(1), m2.group(1)
                if w2 not in FUNC and not (words[w1.lower()] >= 2 and words[w2.lower()] >= 2) and any(len(w1) - 1 in h.positions(w1 + w2) for h in hyph):
                    rep['split'].append((i + 1, w1 + '|' + w2))
            if NUM_END.search(a['text'].replace('\u2060', '').strip()) and re.match(r'\d', c['text'].strip()) and 5 < c['y'] - a['y'] < 25:
                rep['numbreak'].append((i + 1, a['text'].strip()[-8:], c['text'].strip()[:6]))   # '1797—' / '1798', 'p.' / '264'
        heads = [l for l in inside if l['size'] >= body + 1]
        if heads and b and folio:
            h = max(heads, key=lambda l: l['y'])
            if h['y'] > ref - 2.5 * pitch and not any(l['y'] > h['y'] + 1 for l in b):
                rep['head_bottom'].append((i + 1, h['text'][:12]))   # a heading in the last lines with nothing under it
        for a in range(len(ls)):
            for c in range(a + 1, len(ls)):
                p, q = ls[a], ls[c]
                if abs(p['y'] - q['y']) < 0.5 or min(p['size'], q['size']) < body - 1.5:
                    continue                             # (marks, indices and exponents sit off the line on purpose)
                ox = min(p['x1'], q['x1']) - max(p['x0'], q['x0'])
                oy = min(p['y'], q['y']) - max(p['y'], q['y']) + min(p['size'], q['size']) * 0.6
                if ox > 4 and oy > 1 and abs(p['y'] - q['y']) < 0.55 * min(p['size'], q['size']):
                    rep['overlap'].append((i + 1, p['text'][:8], q['text'][:8]))
        for lk in d[i].get_links():
            if lk.get('kind') == pymupdf.LINK_GOTO and not 0 <= lk.get('page', -1) < n:
                rep['links'].append((i + 1, lk.get('page')))
    rep['type3'] = sorted({f[3] for pn in range(n) for f in d.get_page_fonts(pn) if f[2] == 'Type3'})
    for i in range(n):
        # apostrophes inside Latin words set in a CJK face; a ’ that closes a ‘ on the page is a quote (model.apostrophes)
        chars = [('\n', '')]
        for b in d[i].get_text('rawdict')['blocks']:
            for l in b.get('lines', []):
                chars += [(c['c'], sp['font']) for sp in l['spans'] for c in sp['chars']] + [('\n', '')]
        for k in sorted(apostrophes(''.join(x for x, _ in chars))):
            if re.search(r'CJK|SC-|Han', chars[k][1]):
                rep['apos'].append((i + 1, ''.join(x for x, _ in chars[max(0, k - 6):k + 4])))
    try:
        rep['joiner'] = [x for x in joiners(d) if x[1]] if callable(joiners) else []
    except Exception:
        rep['joiner'] = []
    return dict(pages=n, sizes=dict(sizes), body=body, ref=ref, pitch=pitch, rep=rep)


def main(args):
    verbose = '-v' in args
    for p in [a for a in args if a != '-v']:
        r = audit(p)
        rep = r['rep']
        keys = ('foot', 'grid', 'kinsoku', 'over', 'edge', 'col', 'overlap', 'lone', 'short', 'head_bottom', 'markstart', 'numbreak', 'split', 'links', 'joiner',
                'empty', 'apos', 'type3')
        print(f"{p.split('/')[-1]}: {r['pages']} pp, sizes {list(r['sizes'])}, body {r['body']}, bottom {r['ref']}, pitch {r['pitch']} | "
              + ' '.join(f'{k} {len(rep.get(k, []))}' for k in keys))
        if verbose:
            for k in keys:
                if rep.get(k):
                    print(f'   {k}: {rep[k][:12]}')


if __name__ == '__main__':
    main(sys.argv[1:])
