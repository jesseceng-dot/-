"""Re-typeset a displayed formula: emulate old and new versions with XeLaTeX,
register the emulated old version onto the book's glyphs (pure translation),
and replace only what differs between old and new."""
import os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
import engine as E
import texlayout as T


def typeset_display(tex, name, extra='', body_fmt=None):
    body = (body_fmt or '\\mbox{}\n\\[%s\\]\n') % tex
    pdff = T.run(body, extra=extra, name=name)
    return T.read_layout(pdff)


def ekey(g):
    return (E.norm_font_name(g['font']), g['code'])


def bkey(g):
    return (E.norm_font_name(g.font.name), g.code)


def rule_box(r):
    return r['bbox']


def register(emu, book, tol=0.12):
    """translation (dx, dy) mapping emulated glyphs onto book glyphs, and matching"""
    votes = Counter()
    bykey = {}
    for b in book:
        bykey.setdefault(bkey(b), []).append(b)
    for e in emu:
        for b in bykey.get(ekey(e), []):
            votes[(round(b.x - e['x'], 1), round(b.y - e['y'], 1))] += 1
    if not votes:
        raise RuntimeError('no common glyphs')
    (dx0, dy0), n = votes.most_common(1)[0]
    # refine with matched pairs
    pairs = []
    used = set()
    for e in emu:
        best = None
        for b in bykey.get(ekey(e), []):
            if id(b) in used:
                continue
            d = abs(b.x - e['x'] - dx0) + abs(b.y - e['y'] - dy0)
            if d < 0.3 and (best is None or d < best[0]):
                best = (d, b)
        if best:
            used.add(id(best[1])); pairs.append((e, best[1]))
    dxs = sorted(b.x - e['x'] for e, b in pairs); dys = sorted(b.y - e['y'] for e, b in pairs)
    dx = dxs[len(dxs) // 2]; dy = dys[len(dys) // 2]
    res = max(max(abs(b.x - e['x'] - dx), abs(b.y - e['y'] - dy)) for e, b in pairs)
    unmatched_e = [e for e in emu if not any(e is p[0] for p in pairs)]
    unmatched_b = [b for b in book if id(b) not in used]
    return dx, dy, pairs, res, unmatched_e, unmatched_b


def same_glyph(a, b, tol=0.01):
    return ekey(a) == ekey(b) and abs(a['x'] - b['x']) < tol and abs(a['y'] - b['y']) < tol and abs(a['size'] - b['size']) < 1e-3


def same_rule(a, b, tol=0.01):
    return a['paint'] == b['paint'] and all(abs(u - v) < tol for u, v in zip(a['bbox'], b['bbox']))


def redisplay(pe, region, tex_old, tex_new, name, extra='', keep=None, body_fmt=None, verbose=True, max_res=0.08):
    """region: (x0, y0, x1, y1) PDF coords containing the whole display in the book.
    keep(g_dict_or_rule, kind) -> True to leave this element of the book untouched."""
    x0, y0, x1, y1 = region
    gold, rold = typeset_display(tex_old, name + '_old', extra, body_fmt)
    gnew, rnew = typeset_display(tex_new, name + '_new', extra, body_fmt)
    book = pe.glyphs_in(x0, y0, x1, y1)
    dx, dy, pairs, res, ue, ub = register(gold, book)
    if verbose:
        print('%s: dx=%.3f dy=%.3f matched %d/%d (book %d) residual %.3f' % (name, dx, dy, len(pairs), len(gold), len(book), res))
        for e in ue:
            print('   unmatched emulated:', e['font'], repr(e['uni']), round(e['x'] + dx, 2), round(e['y'] + dy, 2))
        for b in ub:
            print('   unmatched book:', b.font.name, repr(b.uni), round(b.x, 2), round(b.y, 2))
    if res > max_res or ue:
        raise RuntimeError('%s: registration failed (res %.3f, %d unmatched)' % (name, res, len(ue)))
    # rules of the book in region
    brules = [it for it in pe.items_in(x0, y0, x1, y1, kinds=('path',)) if not (it.paint in ('f', 'F', 'f*', 'B', 'B*', 'b', 'b*') and all(abs(c - 1) < 1e-3 for c in it.color[:3]))]
    rpairs = []
    usedr = set()
    for r in rold:
        bb = r['bbox']
        cand = [it for it in brules if id(it) not in usedr and all(abs(u - v) < 0.15 for u, v in zip(it.bbox, (bb[0] + dx, bb[1] + dy, bb[2] + dx, bb[3] + dy)))]
        if not cand:
            raise RuntimeError('%s: rule %s not found in book' % (name, bb))
        usedr.add(id(cand[0])); rpairs.append((r, cand[0]))
    # diff old/new
    gone = [e for e in gold if not any(same_glyph(e, n) for n in gnew)]
    added = [n for n in gnew if not any(same_glyph(n, e) for e in gold)]
    rgone = [r for r in rold if not any(same_rule(r, n) for n in rnew)]
    radded = [n for n in rnew if not any(same_rule(n, r) for r in rold)]
    if keep:
        gone = [e for e in gone if not keep(e, 'g', dx, dy)]
        added = [n for n in added if not keep(n, 'g', dx, dy)]
        rgone = [r for r in rgone if not keep(r, 'r', dx, dy)]
        radded = [r for r in radded if not keep(r, 'r', dx, dy)]
    if verbose:
        print('   remove %d glyphs %d rules; add %d glyphs %d rules' % (len(gone), len(rgone), len(added), len(radded)))
        print('   removed:', ''.join(e['uni'] or '?' for e in gone), ' added:', ''.join(n['uni'] or '?' for n in added))
    pmap = {id(e): b for e, b in pairs}
    pe.remove_glyphs([pmap[id(e)] for e in gone])
    rmap = {id(r): it for r, it in rpairs}
    pe.remove_items([rmap[id(r)] for r in rgone])
    emit = []
    for n in added:
        fobj, code = E.map_layout_glyph(pe.bf, n)
        emit.append(dict(bookfont=fobj, code=code, x=n['x'] + dx, y=n['y'] + dy, size=n['size']))
    pe.emit_glyphs(emit)
    for r in radded:
        ops = r['ops']
        if r['paint'] == 'S' and len(ops) == 3 and ops[0][0] == 'm' and ops[1][0] == 'l':
            pe.emit_rule_stroke(r['bbox'][0] + dx, r['bbox'][1] + dy, r['bbox'][2] + dx, r['lw'])
        elif r['paint'] in ('f', 'F'):
            bb = r['bbox']
            pe.emit_rect_fill(bb[0] + dx, bb[1] + dy, bb[2] - bb[0], bb[3] - bb[1])
        else:
            raise RuntimeError('unsupported rule %r' % r)
    return dict(dx=dx, dy=dy, gone=gone, added=added, rgone=rgone, radded=radded, gold=gold, gnew=gnew)
