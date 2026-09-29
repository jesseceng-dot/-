"""Acceptance checks on solved layouts (plan level) and on printed PDFs."""
import re
import pymupdf
from . import style
from .layout import GRIDS
from .model import runs_text
from . import normalize

HEAD_STYLES = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'h9', 'secn', 'secnum', 'idxhead', 'tochead'}


def module_report(mod):
    """Plan-level checks for one text module.  Returns dict of issue lists."""
    rep = dict(gap=[], head_bottom=[], head_short=[], widow=[], orphan=[], last_page=[], lone=[], loose=[])
    if mod.kind != 'text' or not mod.plan:
        return rep
    lbs, plan = mod.lbs, mod.plan
    g = GRIDS[mod.grid]
    pages = plan['pages']
    for pi, p in enumerate(pages):
        last_page = pi == len(pages) - 1
        if p['gap'] and not last_page:
            rep['gap'].append((pi, p['gap']))
        items = p['items']
        if not items:
            continue
        # heading as last thing on the page
        bi, lo, hi, s0 = items[-1]
        b = lbs[bi].block
        if lbs[bi].st.get('keep') and not last_page and b['k'] != 'img':
            rep['head_bottom'].append((pi, runs_text(b['runs'])[:20]))
        # heading followed by fewer than 2 lines of text
        for k, (bi, lo, hi, s0) in enumerate(items):
            b = lbs[bi].block
            if lbs[bi].st.get('keep') and k + 1 < len(items):
                nb, nlo, nhi, _ = items[k + 1]
                if not lbs[nb].st.get('keep') and lbs[nb].block['k'] == 'p' and nhi - nlo < 2 \
                        and nhi - nlo < lbs[nb].nl[plan['variants'][nb]]:
                    rep['head_short'].append((pi, runs_text(b['runs'])[:20]))
        # widow / orphan: pieces of a split block
        for (bi, lo, hi, s0) in items:
            lb = lbs[bi]
            n = lb.nl[plan['variants'][bi]]
            if lb.splittable and n > 1 and (hi - lo) < n:
                if lo == 0 and hi - lo == 1:
                    rep['orphan'].append((pi, runs_text(lb.block['runs'])[:16]))
                if hi == n and hi - lo == 1:
                    rep['widow'].append((pi, runs_text(lb.block['runs'])[:16]))
    # module tail
    last = pages[-1]['items']
    cnt = sum((hi - lo) * lbs[bi].st['slots'] for (bi, lo, hi, s0) in last)
    if cnt <= 2 and len(pages) > 1:
        rep['last_page'].append(('short tail', cnt))
    # lone marks / loose lines
    for lb in lbs:
        if lb.block['k'] != 'p':
            continue
        vi = plan['variants'][lb.idx]
        starts = lb.starts[vi]
        text = runs_text(lb.block['runs'])
        if len(starts) > 1 and lb.st['align'] == 'j':
            tail = text[starts[-1]:].strip()
            if len(tail) <= 1 and (not tail or tail in '。，、；：！？）】〕」』”’…—,.;:!?)]'):
                rep['lone'].append(text[-10:])
            if tail and len(tail) <= 6 and tail.strip('0123456789[]［］()（）') == '':
                rep['lone'].append(text[-10:])
            for j in range(len(starts) - 1):
                w = lb.st['W'] - (lb.st['left'] + lb.st['right'] + (lb.st['first'] if j == 0 else 0)) * lb.st['fs']
                if (w - lb.nat[vi][j]) / lb.st['fs'] > 1.6:
                    rep['loose'].append((lb.idx, j, round((w - lb.nat[vi][j]) / lb.st['fs'], 2)))
    return rep


def summarize(rep):
    return {k: len(v) for k, v in rep.items() if v}


def variant_stats(mod):
    from collections import Counter
    if not mod.plan:
        return {}
    return dict(Counter(mod.plan['variants']))


# ------------------------------------------------------------------------------ PDF level
def pdf_checks(pdf, bb):
    """Bottom-baseline alignment of every text page + fonts + links."""
    doc = pymupdf.open(pdf)
    out = dict(bad_bottom=[], type3=set(), pages=len(doc))
    want = (style.NLINES - 1) * style.LINE + style.TOP  # placeholder: real baseline is taken from the first full page
    from collections import Counter
    bottoms = Counter()
    per_page = {}
    for p in bb.pages:
        if p.mod.kind != 'text' or p.mod.mid in ('master-toc',):
            continue
        page = doc[p.index]
        if any(im['bbox'][3] - im['bbox'][1] > 40 for im in page.get_image_info()):
            continue                                         # a page carrying a figure of its own (appendix table image): no text baseline to compare
        ys = []
        for blk in page.get_text('dict')['blocks']:
            for l in blk.get('lines', []):
                sp = [s for s in l['spans'] if s['text'].strip()]
                if sp and 56 < sp[0]['origin'][1] < style.PAGE_H - 50:
                    ys.append(round(sp[0]['origin'][1], 2))
        if ys:
            per_page[p.index] = max(ys)
            bottoms[max(ys)] += 1
    ref = bottoms.most_common(1)[0][0] if bottoms else None
    last_pages = {max(p.index for p in bb.pages if p.mod is m) for m in bb.mods}
    for i, y in per_page.items():
        pg = bb.pages[i]
        if i not in last_pages and abs(y - ref) > 0.06:
            out['bad_bottom'].append((i, y))
    out['ref_bottom'] = ref
    for pn in range(len(doc)):
        for f in doc.get_page_fonts(pn):
            if f[2] == 'Type3':
                out['type3'].add(f[3])
    return out
