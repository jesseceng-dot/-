"""Index page numbers: original print pages -> pages of this PDF.

The ebook carries no print-page markers, so a printed page number cannot be looked up directly.  It is reconstructed
from the index itself: an index entry names a term and lists the printed pages on which the term stands, so wherever the
term occurs exactly once in the text (or as often as it has pages) we know both the printed page and the position in
the text.  These anchors calibrate, for every chapter, a monotone map  position -> printed page  (local regression),
and every index reference is then resolved to the occurrence of its term that lies closest to the printed page, or, if
the term cannot be found, to the position the map predicts for that printed page.
"""
import re
import bisect
from .model import runs_text

CLOSE = {'（': '）', '(': ')', '〔': '〕', '[': ']', '［': '］', '【': '】'}
NUM_RE = re.compile(r'(?<![\d.A-Za-z])(\d+)(?:[—–-](\d+))?(?![\d])')
NOT_PAGE_AFTER = re.compile(r'^(?:年|月|日|世纪|页|卷|章|节|篇|号|岁|个|种|届|次|%|％|\.\d)')
NOT_PAGE_BEFORE = re.compile(r'(?:前|约|公元|第|共|？|\?)$')


def expand_range(a, b):
    """'116—30' -> (116, 130); '295—6' -> (295, 296)"""
    lo = int(a)
    if b is None:
        return lo, lo
    if len(b) < len(a):
        b = a[:len(a) - len(b)] + b
    hi = int(b)
    return lo, max(lo, hi)


def bracket_depth_mask(t):
    """depth[i] > 0 when character i lies inside （…）〔…〕[…]"""
    depth = [0] * len(t)
    stack = []
    for i, ch in enumerate(t):
        if ch in CLOSE:
            stack.append(CLOSE[ch])
        elif stack and ch == stack[-1]:
            stack.pop()
        depth[i] = len(stack)
    return depth


class Series:
    """The text of an ordered list of modules, addressable by character offset."""

    def __init__(self, mods):
        self.mods = mods
        parts, self.blocks, self.starts = [], [], []
        off = 0
        for mod in mods:
            for bi, b in enumerate(mod.blocks):
                t = runs_text(b['runs']) if b.get('runs') else ''
                self.blocks.append((mod.mid, bi))
                self.starts.append(off)
                parts.append(t)
                off += len(t) + 1
        self.text = '\n'.join(parts)
        self.mod_start = {}
        for (mid, bi), s in zip(self.blocks, self.starts):
            self.mod_start.setdefault(mid, s)
        self.mod_ids = [m.mid for m in mods]

    def locate(self, off):
        i = bisect.bisect_right(self.starts, off) - 1
        mid, bi = self.blocks[i]
        return mid, bi, off - self.starts[i]

    def module_of(self, off):
        return self.locate(off)[0]

    def find_all(self, key):
        out, i = [], self.text.find(key)
        while i >= 0:
            out.append(i)
            i = self.text.find(key, i + 1)
        return out


def clean_key(s):
    s = re.sub(r'[（(〔\[［【].*?[）)〕\]］】]', '', s)
    s = s.replace('▲', '').replace('——', '').replace('*', '')
    s = s.strip(' 　：:，,；;、。.·')
    return s.strip()


def foreign_words(t, shift, body):
    """German / Latin / English words that the entry gives for its headword (they occur in the text where the translator
    glosses the term, which makes them very specific search keys)."""
    words = []
    if shift:                                     # 'Absolute,das<ideographic space>绝对...'
        words += re.split(r'[,\s/]+', t[:shift].strip('　 '))
    m = re.search(r'[（(]([^）)]*)[）)]', body)
    if m and not re.match(r'^\s*[\d—]', m.group(1)):
        words += re.split(r'[/／;；,，\s]+', m.group(1))
    out = []
    for w in words:
        w = w.strip(' .,:')
        if len(w) >= 4 and re.match(r'^[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß\-\.\']+$', w) and w.lower() not in ('der', 'die', 'das', 'the') \
                and w not in out:
            out.append(w)
    return out[:3]


def parse_entries(blocks, head_only=False, skip_c=False):
    """Find page references of an index.

    Returns a list of refs: dict(bi, start, end, lo, hi, prefix, keys) where [start, end) is the span of the number
    (or 'a—b' range) in the block text, (lo, hi) the printed page range, `prefix` the series prefix ('上'/'下') and
    `keys` the search strings, most specific first."""
    refs = []
    head = ''
    for bi, b in enumerate(blocks):
        if b.get('k') != 'p' or b['style'] not in ('index', 'indexc') or (skip_c and b['style'] == 'indexc'):
            continue
        t = runs_text(b['runs'])
        if t.startswith('*'):
            continue
        depth = bracket_depth_mask(t)
        body = t.split('　', 1)[1] if '　' in t[:60] and re.match(r'^[A-Za-z .,\'’\-/ÄÖÜäöüßéèçñ]+　', t) else t
        shift = len(t) - len(body)
        # headword: the first Chinese chunk
        m = re.match(r'^[▲—\s*]*([^（(〔\[0-9，,；;：:～~/]+)', body)
        entry_head = clean_key(m.group(1)) if m and not body.startswith('——') else ''
        if b['style'] == 'index' and entry_head and not re.fullmatch(r'[\d\s—]+', body.strip()):
            head = entry_head
        fkeys = foreign_words(t, shift, body)
        cur_prefix = None
        seg_start = shift
        for nm in NUM_RE.finditer(t):
            s, e = nm.start(), nm.end()
            if s < shift or depth[s] > 0:
                continue
            after, before = t[e:e + 3], t[max(0, s - 2):s]
            if NOT_PAGE_AFTER.match(after) or NOT_PAGE_BEFORE.search(before):
                continue
            if len(nm.group(1)) == 4 and 1500 < int(nm.group(1)) < 2100 and not nm.group(2) is None:
                continue
            # series prefix (Book 3: 上254, 下56[512])
            pm = re.search(r'([上下])$', t[:s])
            if pm:
                cur_prefix = pm.group(1)
            letter = bool(re.search(r'信$', t[:s]))
            # segment text before the number, back to the previous separator
            k = s
            while k > seg_start and t[k - 1] not in '，,；;：:':
                k -= 1
            phrase = t[k:s]
            phrase = re.sub(r'[上下]$', '', phrase)
            if not phrase.strip('、 　') and seg_start < s:
                # further numbers of the same list: look further back to the segment start
                prev = t[seg_start:s]
                phrase = re.split(r'[\d]', prev)[0] if prev else ''
            hd = head
            ph = phrase.replace('～', hd).replace('~', hd)
            keys = []
            for cand in (() if head_only else (ph, phrase)):
                c2 = clean_key(cand)
                c2 = re.sub(r'^[^一-鿿A-Za-z《]*', '', c2)
                c2 = re.sub(r'[\d\s]+$', '', c2)
                if 2 <= len(c2) <= 12 and c2 not in keys and '～' not in c2 and '~' not in c2:
                    keys.append(c2)
            for kk in [hd, entry_head]:
                if kk and len(kk) >= 2 and kk not in keys:
                    keys.append(kk)
            keys = [k2.strip('《》') for k2 in keys]
            expanded = []
            for k2 in keys:
                for part in re.split(r'[/／]', k2):
                    part = part.strip()
                    if len(part) >= 2 and part not in expanded:
                        expanded.append(part)
            lo, hi = expand_range(nm.group(1), nm.group(2))
            refs.append(dict(bi=bi, start=s, end=e, lo=lo, hi=hi, prefix=cur_prefix, letter=letter, keys=expanded,
                             fkeys=fkeys, pre_attached=bool(pm)))
            seg_start = e
    return refs


# ------------------------------------------------------------------------------------------------ page model
def _wls_line(pts, x0):
    """Weighted least squares  y = a + b (x - x0)  over points (x, y, w); returns (a, b) or None."""
    sw = sum(w for _, _, w in pts)
    if sw <= 0:
        return None
    mx = sum(w * (x - x0) for x, _, w in pts) / sw
    my = sum(w * y for _, y, w in pts) / sw
    sxx = sum(w * ((x - x0) - mx) ** 2 for x, _, w in pts)
    if sxx < 1e-9:
        return None
    b = sum(w * ((x - x0) - mx) * (y - my) for x, y, w in pts) / sxx
    return my - b * mx, b


class ModuleModel:
    """position (characters from the start of the module) -> printed page (float; page p spans [p, p+1))."""

    def __init__(self, mid, length, anchors, dens, glob=None, start=0):
        self.mid, self.length, self.dens = mid, length, dens or 700.0
        self.anchors = sorted(anchors)            # (offset, page)
        self.xs = [a[0] for a in self.anchors]
        self.glob, self.start = glob, start       # fallback: series-wide line  page = a + b * (start + offset)

    def usable(self):
        return len(self.anchors) >= 2 or self.glob is not None

    def _fit(self, c, k=10, skip=None):
        anchors = self.anchors if skip is None else [a for i, a in enumerate(self.anchors) if i != skip]
        if len(anchors) < 2:
            if self.glob is not None:
                a, b = self.glob
                return a + b * (self.start + c)
            return None
        pts = sorted(anchors, key=lambda p: abs(p[0] - c))[:k]
        h = max(abs(x - c) for x, _ in pts) + 1.0
        tri = [(x, y, (1 - (abs(x - c) / h) ** 3) ** 3) for x, y in pts]
        for _ in range(3):                         # robust re-weighting (bisquare)
            fit = _wls_line(tri, c)
            if fit is None:
                break
            a, b = fit
            res = [abs(y - (a + b * (x - c))) for x, y, _ in tri]
            med = sorted(res)[len(res) // 2]
            tri = [(x, y, w * max(0.0, 1 - (r / (6 * med + 0.05)) ** 2) ** 2) for (x, y, w), r in zip(tri, res)]
            tri = [t for t in tri if t[2] > 0]
            if not tri:
                break
        fit = _wls_line(tri, c) if tri else None
        if fit is None or not (0.2 / self.dens < fit[1] < 5 / self.dens):
            x, y = pts[0]                                       # implausible slope: nearest anchor + global density
            return y + (c - x) / self.dens
        # anchors that lie close together give a noisy slope: shrink it towards the series-wide density, and extrapolate
        # from the weighted centre of the anchors with that slope
        sw = sum(w for _, _, w in tri)
        mx = sum(w * x for x, _, w in tri) / sw
        my = sum(w * y for _, y, w in tri) / sw
        span = max(x for x, _, _ in tri) - min(x for x, _, _ in tri)
        wt = min(1.0, span / (8 * self.dens))
        b = wt * fit[1] + (1 - wt) / self.dens
        return my + b * (c - mx)

    def page(self, c, skip=None):
        return self._fit(c, skip=skip)

    def offset(self, page):
        """inverse: offset whose predicted page is `page` (bisection); None if the module does not reach it."""
        if not self.usable():
            return None
        lo, hi = 0.0, float(self.length)
        plo, phi = self.page(lo), self.page(hi)
        if page < plo - 0.6 or page > phi + 0.6:
            return None
        for _ in range(40):
            mid = (lo + hi) / 2
            if self.page(mid) < page:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2


def ref_keys(r):
    return r['keys'] + r.get('fkeys', [])


def collect_anchors(S, refs, prefix_filter=None):
    """Anchors (module id, offset in module, printed page, ref index): a term that occurs exactly as often in the text as
    the entry lists pages for it fixes each of its pages (paired in order)."""
    done = set()
    out = []
    occ_cache = {}

    def occ(k):
        if k not in occ_cache:
            occ_cache[k] = S.find_all(k)
        return occ_cache[k]

    depth = max((len(ref_keys(r)) for r in refs), default=0)
    for level in range(depth):
        groups = {}
        for ri, r in enumerate(refs):
            if ri in done or r['letter'] or r['lo'] != r['hi']:
                continue
            if prefix_filter is not None and (r['prefix'] or '') != prefix_filter:
                continue
            ks = ref_keys(r)
            if level < len(ks):
                groups.setdefault((r['bi'], ks[level]), []).append((r['lo'], ri))
        for (bi, k), lst in groups.items():
            o = occ(k)
            if not o or len(o) != len(lst):
                continue
            for (p, ri), off in zip(sorted(lst), sorted(o)):
                c = off + len(k) // 2
                mid = S.module_of(c)
                out.append((mid, c - S.mod_start[mid], p, ri))
                done.add(ri)
    return out


def lnds(seq):
    """Indices of a longest non-decreasing subsequence of `seq` (values) - patience sorting."""
    tails, idx, prev = [], [], [-1] * len(seq)
    for i, v in enumerate(seq):
        k = bisect.bisect_right(tails, v)
        if k == len(tails):
            tails.append(v)
            idx.append(i)
        else:
            tails[k] = v
            idx[k] = i
        prev[i] = idx[k - 1] if k > 0 else -1
    out, i = [], idx[-1] if idx else -1
    while i >= 0:
        out.append(i)
        i = prev[i]
    return out[::-1]


def clean_anchors(anchors, S=None, dmin=300.0, dmax=1300.0, gap=8):
    """Keep the largest set of anchors that form one plausible chain: printed page never decreases with the position,
    and between two chosen anchors the pages advance at a plausible rate (dmin..dmax characters per page, +1 page of
    slack, +`gap` pages when the chain crosses into another chapter - endnotes and blank pages sit between chapters).
    This removes anchors whose term was matched at the wrong place, including small groups of them."""
    if not anchors:
        return []
    if S is None:                                             # module-local chain only
        by = {}
        for a in anchors:
            by.setdefault(a[0], []).append(a)
        out = []
        for lst in by.values():
            lst.sort(key=lambda a: (a[1], a[2]))
            out.extend(lst[i] for i in lnds([a[2] for a in lst]))
        return out
    pts = sorted(((S.mod_start[a[0]] + a[1], a[2], a) for a in anchors), key=lambda t: (t[0], t[1]))
    n = len(pts)
    best, prev = [1] * n, [-1] * n
    for j in range(n):
        cj, yj, aj = pts[j]
        for i in range(j):
            ci, yi, ai = pts[i]
            dy = yj - yi
            if dy < 0:
                continue
            dc = cj - ci
            slack = 1.0 + (gap if ai[0] != aj[0] else 0)
            if dy > dc / dmin + slack or dy < dc / dmax - 1.0:
                continue
            if best[i] + 1 > best[j]:
                best[j], prev[j] = best[i] + 1, i
    j = max(range(n), key=lambda k: best[k])
    out = []
    while j >= 0:
        out.append(pts[j][2])
        j = prev[j]
    return out[::-1]


# ------------------------------------------------------------------------------------------------ resolving
EPS = 0.75                    # a candidate occurrence is accepted if its predicted page is within EPS of the printed page


def build_models(S, anchors):
    per = {}
    for mid, off, p, ri in anchors:
        per.setdefault(mid, []).append((off, p + 0.5))
    sl = []
    for a in per.values():
        a.sort()
        for (x1, y1), (x2, y2) in zip(a, a[1:]):
            if y2 - y1 >= 3:
                sl.append((x2 - x1) / (y2 - y1))
    dens = sorted(sl)[len(sl) // 2] if sl else 700.0
    # series-wide line (used for chapters that own fewer than two anchors)
    glob = None
    pts = sorted((S.mod_start[mid] + off, y) for mid, a in per.items() for off, y in a)
    if len(pts) >= 6:
        keep = lnds([y for _, y in pts])
        pts = [pts[i] for i in keep]
        fit = _wls_line([(x, y, 1.0) for x, y in pts], 0.0)
        if fit and 0.3 / dens < fit[1] < 3 / dens:
            glob = fit
    starts = [S.mod_start[i] for i in S.mod_ids] + [len(S.text)]
    return {mid: ModuleModel(mid, starts[i + 1] - starts[i], per.get(mid, []), dens, glob, starts[i])
            for i, mid in enumerate(S.mod_ids)}


def resolve_ref(S, models, r):
    """Position (offset in the series text) for one single-page reference.  Returns (offset, method)."""
    lo = r['lo']
    cand = []
    for k in ref_keys(r):
        occ = S.find_all(k)
        if occ:
            cand.append((len(occ), k, occ))
    cand.sort(key=lambda t: t[0])                          # most specific key first
    for n, k, occ in cand[:3]:
        best = None
        for o in occ:
            c = o + len(k) // 2
            mid = S.module_of(c)
            mm = models[mid]
            q = mm.page(c - S.mod_start[mid]) if mm.usable() else None
            if q is None:
                if n == 1:
                    return c, 'term1'
                continue
            d = 0.0 if lo <= q <= lo + 1 else min(abs(q - lo), abs(q - (lo + 1)))
            if best is None or d < best[0]:
                best = (d, c)
        if best is not None and best[0] <= EPS:
            return best[1], ('term1' if n == 1 else 'term')
    mid, off = _interp(S, models, lo + 0.5)
    if mid is None:
        return None, 'none'
    return S.mod_start[mid] + off, 'interp'


def _interp(S, models, page):
    """(module id, offset) whose predicted printed page is `page`; prefers modules whose anchors span that page."""
    cands = []
    for mid in S.mod_ids:
        mm = models[mid]
        if not mm.usable():
            continue
        off = mm.offset(page)
        if off is not None:
            own = len(mm.anchors) >= 2
            inside = own and mm.page(mm.xs[0]) - 0.5 <= page <= mm.page(mm.xs[-1]) + 0.5
            cands.append((0 if inside else (1 if own else 2), -len(mm.anchors), mid, off))
    if not cands:
        return None, None
    cands.sort()
    return cands[0][2], cands[0][3]


def resolve_range(S, models, r):
    """(start, end) offsets of a page range (printed pages lo..hi)."""
    mid, off = _interp(S, models, r['lo'] + 0.05)
    if mid is None:
        return None, None, 'none'
    e = models[mid].offset(r['hi'] + 0.95)
    return S.mod_start[mid] + off, S.mod_start[mid] + (e if e is not None else off), 'range'


# ------------------------------------------------------------------------------------------------ applying to a module
def apply_edits(runs, edits):
    """Replace spans of the run list.  edits = [(start, end, text, extra_run_attrs)]; every span must lie inside one run
    (others are skipped); the new text takes the attributes of that run (minus link/anchor/class) plus `extra`."""
    edits = sorted(edits, key=lambda e: e[0])
    out, pos, ei = [], 0, 0
    for r in runs:
        t = r['t']
        n = len(t)
        cur = 0
        while ei < len(edits) and edits[ei][0] < pos + n:
            s, e, new, extra = edits[ei]
            ei += 1
            if e > pos + n or s - pos < cur:
                continue
            if s - pos > cur:
                out.append(dict(r, t=t[cur:s - pos]))
            if new:
                out.append(dict({k: v for k, v in r.items() if k not in ('t', 'h', 'a', 'c', 'i')}, t=new, **extra))
            cur = e - pos
        if cur < n:
            out.append(dict(r, t=t[cur:]))
        pos += n
    return [r for r in out if r['t']]


def _refs_of(mod):
    cfg = mod.idxmap
    return parse_entries(mod.src_blocks, head_only=cfg.get('head_only', False), skip_c=cfg.get('skip_c', False))


def _pooled(mod, siblings, blocks_of):
    """Series objects and page models of an index; the anchors of all indexes that share the same text series (term
    index and name index of one book/volume) are pooled, because every anchor helps every index."""
    cfg = mod.idxmap
    key = tuple(sorted((k, tuple(v)) for k, v in cfg['series'].items()))
    group = [m for m in siblings if tuple(sorted((k, tuple(v)) for k, v in m.idxmap['series'].items())) == key]
    series, models, counts = {}, {}, {}
    for pre, mids in cfg['series'].items():
        S = Series([blocks_of(m) for m in mids])
        anchors = []
        for m in group:
            refs = m.idx_refs if getattr(m, 'idx_refs', None) is not None else _refs_of(m)
            anchors += collect_anchors(S, refs, pre if len(cfg['series']) > 1 else None)
        anchors = clean_anchors(anchors, S)
        series[pre], models[pre], counts[pre] = S, build_models(S, anchors), len(anchors)
    return series, models, counts


def resolve_module(mod, blocks_of, siblings=None):
    """Positions of every reference of an index module, independent of the pagination.  `blocks_of(mid)` returns the
    module object for a module id.  Returns (refs, resolved) with resolved[i] = (kind, pos0, pos1); a position is
    (module id, block index, offset in block)."""
    cfg = mod.idxmap
    refs = _refs_of(mod)
    series, models, counts = _pooled(mod, siblings or [mod], blocks_of)
    resolved = []
    stats = {}
    for ri, r in enumerate(refs):
        pre = (r['prefix'] or '') if len(cfg['series']) > 1 else next(iter(cfg['series']))
        if r['letter'] or pre not in series:
            resolved.append(('skip', None, None))
            stats['skip'] = stats.get('skip', 0) + 1
            continue
        S, md = series[pre], models[pre]
        if r['lo'] == r['hi']:
            off, kind = resolve_ref(S, md, r)
            p0 = S.locate(off) if off is not None else None
            resolved.append((kind, p0, p0))
        else:
            a, b, kind = resolve_range(S, md, r)
            resolved.append((kind, S.locate(a) if a is not None else None, S.locate(b) if b is not None else None))
        stats[kind] = stats.get(kind, 0) + 1
    mod.idx_stats = dict(stats, anchors=counts)
    return refs, resolved


def remap_module(bb, mod):
    """New block list of an index module: every printed page number replaced by the label of the page of this PDF that
    holds the term (linked to that page).  Pure function of the module's source blocks and the current page labels."""
    import copy
    if getattr(mod, 'idx_resolved', None) is None:
        by_id = {m.mid: m for m in bb.mods}
        sib = [m for m in bb.mods if m.idxmap]
        for m in sib:
            if m.idx_refs is None:
                m.idx_refs = _refs_of(m)
        mod.idx_refs, mod.idx_resolved = resolve_module(mod, by_id.__getitem__, sib)
    refs, resolved = mod.idx_refs, mod.idx_resolved
    blocks = copy.deepcopy(mod.src_blocks)
    per_block = {}
    for r, (kind, p0, p1) in zip(refs, resolved):
        if p0 is None or p1 is None:
            continue
        per_block.setdefault(r['bi'], []).append((r, p0, p1))
    for bi, lst in per_block.items():
        b = blocks[bi]
        text = runs_text(b['runs'])
        edits = []
        last = None                                      # (end offset, label) of the previous reference of the list
        for r, p0, p1 in sorted(lst, key=lambda x: x[0]['start']):
            pa, la = bb.page_and_label(*p0)
            pb, lb_ = bb.page_and_label(*p1)
            label = la if la == lb_ else f'{la}—{lb_}'
            gap = text[last[0]:r['start']] if last else None
            if last and last[1] == label and re.fullmatch(r'[，、,\s]*', gap or 'x'):
                edits.append((last[0], r['end'], '', {}))          # same page listed again: drop the repeat
                last = (r['end'], label)
                continue
            edits.append((r['start'] - (1 if r.get('pre_attached') else 0), r['end'], label, dict(h=f'pgp{pa}', c='pn')))
            last = (r['end'], label)
        b['runs'] = apply_edits(b['runs'], edits)
    return blocks


def mapping_rows(bb, mod):
    """One row per converted reference: (index, entry, original number, label in this PDF, method)."""
    rows = []
    for r, (kind, p0, p1) in zip(mod.idx_refs, mod.idx_resolved):
        blk = mod.src_blocks[r['bi']]
        t = runs_text(blk['runs'])
        orig = t[r['start']:r['end']]
        if p0 is None or p1 is None:
            rows.append((mod.mid, t[:40], (r['prefix'] or '') + orig, '', kind))
            continue
        la, lb_ = bb.page_and_label(*p0)[1], bb.page_and_label(*p1)[1]
        rows.append((mod.mid, t[:40].replace('　', ' '), (r['prefix'] or '') + orig, la if la == lb_ else f'{la}—{lb_}', kind))
    return rows


def validate(mod, blocks_of, siblings=None):
    """Held-out check of the page model of one index: leave each anchor out in turn and compare the printed page the
    model predicts for its position with the true one.  Returns dict(n, within_half, within_one, within_two, median)."""
    cfg = mod.idxmap
    key = tuple(sorted((k2, tuple(v)) for k2, v in cfg['series'].items()))
    group = [m for m in (siblings or [mod]) if tuple(sorted((k2, tuple(v)) for k2, v in m.idxmap['series'].items())) == key]
    errs = []
    for pre, mids in cfg['series'].items():
        S = Series([blocks_of(m) for m in mids])
        anchors = []
        for m in group:
            anchors += collect_anchors(S, _refs_of(m), pre if len(cfg['series']) > 1 else None)
        anchors = clean_anchors(anchors, S)
        models = build_models(S, anchors)
        per = {}
        for mid, off, p, ri in anchors:
            per.setdefault(mid, []).append((off, p + 0.5))
        for mid, a in per.items():
            mm = models[mid]
            a.sort()
            for i2, (x, y) in enumerate(a):
                if len(a) < 3:
                    continue
                q = mm.page(x, skip=i2)
                if q is not None:
                    errs.append(abs(q - y))
    n = len(errs)
    if not n:
        return dict(n=0)
    return dict(n=n, within_half=sum(e <= 0.5 for e in errs) / n, within_one=sum(e <= 1 for e in errs) / n,
                within_two=sum(e <= 2 for e in errs) / n, median=sorted(errs)[n // 2])
