"""Build one book end to end."""
import os
import sys
import time
import json
from . import style, render, books, book as B
from .measure import Measurer
from .layout import STYLES, STYLES_SMALL, GRIDS
from .post import finish_pdf


def calibrate_all():
    pairs = set()
    for name, g in GRIDS.items():
        for st in list(STYLES.values()) + list(STYLES_SMALL.values()):
            if st['slots'] == 1 or True:
                pairs.add((st['cls'], g['pitch']))
    render.calibrate(sorted(pairs))


def outline_for(bb):
    """Bookmarks: modules, and the rank-2/3 headings inside them; volumes become a parent level."""
    out = []
    has_vol = any(m.volume for m in bb.mods)
    last_vol = None
    under = False                      # inside a work (divider page) of the Kant volumes: its modules are one level down
    for mod in bb.mods:
        pgs = bb.pages_of(mod)
        first = pgs[0].index + 1
        if mod.zone == 'cover':
            out.append([1, '封面', first])
            continue
        vol_page_only = mod.kind == 'page' and mod.volume and not mod.toc and mod.mid.find('v') > 0
        if mod.volume and mod.volume != last_vol:
            last_vol = mod.volume
            out.append([1, mod.volume, first])
        base = 2 if (has_vol and mod.volume) else 1
        if mod.kind == 'page' and mod.toc and mod.toc_level == 0:
            under = mod.mid != 'plates'
        elif under:
            base += 1
        if vol_page_only:
            continue
        if not mod.toc and mod.mid != 'toc' and not mod.title:
            continue
        if not mod.toc and mod.mid not in ('toc',) and mod.kind == 'page':
            continue
        title = mod.toc_title or mod.title or mod.mid
        lv = base + (1 if mod.toc_level == 2 else 0)
        out.append([lv, title, first])
        if mod.kind == 'text':
            heads = getattr(mod, 'toc_heads', None)          # Kant volumes: the headings that the contents page lists
            if heads is None:
                heads = [(bi, blk['rank']) for bi, blk in enumerate(mod.blocks)
                         if blk['k'] == 'h' and blk.get('rank', 9) in (2, 3) and not blk.get('notoc')]
            for bi, rk in heads:
                blk = mod.blocks[bi]
                pg = bb.block_pages.get((mod.mid, bi))
                if pg is not None:
                    out.append([lv + max(rk, 2) - 1, B.title_text(blk['runs']), pg + 1])
    fixed, last = [], 0
    for lv, t, p in out:
        lv = max(1, min(lv, last + 1))
        fixed.append([lv, t, p])
        last = lv
    return fixed


def labels_for(bb):
    labels = []
    prev = None
    n_front = 0
    for p in bb.pages:
        z = p.mod.zone
        kind = 'cover' if z == 'cover' else ('front' if z == 'front' else 'body')
        if kind != prev:
            if kind == 'cover':
                labels.append({'startpage': p.index, 'prefix': '', 'style': '', 'firstpagenum': 1})
            elif kind == 'front':
                labels.append({'startpage': p.index, 'prefix': '', 'style': 'r', 'firstpagenum': 1})
            else:
                labels.append({'startpage': p.index, 'prefix': '', 'style': 'D', 'firstpagenum': 1})
            prev = kind
    return labels


def build(cfg, out_pdf, redo=()):
    t0 = time.time()
    calibrate_all()
    m = Measurer()
    bb = B.BookBuilder(cfg, m)
    bb.typeset_all(redo=redo)
    m.close()
    print('typeset', round(time.time() - t0, 1), 's; pages', sum(mod.npages for mod in cfg['modules']), flush=True)
    from . import check
    for mod in cfg['modules']:
        if mod.kind == 'text':
            rep = check.module_report(mod)
            hard = {k: len(v) for k, v in rep.items() if v and k not in ('loose',)}
            print(f'  {mod.mid:9s} p{mod.npages:4d} cost {mod.plan["cost"]:7.1f} {hard}', flush=True)
    for mod in cfg['modules']:
        if mod.idx_stats:
            print('  index', mod.mid, mod.idx_stats, flush=True)
    idx_rows = []
    if any(m.idx_stats for m in cfg['modules']):
        from . import indexmap
        bb.sequence()
        for mod in cfg['modules']:
            if mod.idx_stats:
                idx_rows += indexmap.mapping_rows(bb, mod)
        import csv
        with open(out_pdf[:-4] + '.index-map.csv', 'w', newline='', encoding='utf8') as f:
            w = csv.writer(f)
            w.writerow(['index', 'entry', 'original page', 'page in this PDF', 'method'])
            w.writerows(idx_rows)
    bb.sequence()
    B.fill_toc_labels(bb, cfg['toc'])
    htmls = bb.render_pages()
    html = render.document_html(htmls)
    raw = out_pdf + '.raw.pdf'
    render.print_pdf(html, raw, work_html=out_pdf + '.html')
    print('printed', round(time.time() - t0, 1), 's', flush=True)
    info = finish_pdf(raw, out_pdf, bb.anchors, outline_for(bb), labels_for(bb),
                      {'title': cfg['title'], 'author': cfg['meta']['author'], 'subject': cfg['meta'].get('subject', '贺麟中译黑格尔经典著作')})
    os.remove(raw)
    meta = dict(pages=len(bb.pages), anchors={k: [int(v[0]), float(v[1])] for k, v in bb.anchors.items()},
                outline=outline_for(bb), labels=labels_for(bb), toc=[(p.mod.mid, p.label) for p in bb.pages if p.first])
    json.dump(meta, open(out_pdf[:-4] + '.meta.json', 'w'), ensure_ascii=False)
    print('links', info['internal'], 'internal', info['external'], 'external; missing', len(info['missing']),
          list(info['missing'].items())[:8], flush=True)
    return bb, info


if __name__ == '__main__':
    name = sys.argv[1]
    redo = tuple(a[7:].split(',') for a in sys.argv[2:] if a.startswith('--redo='))
    redo = redo[0] if redo else ()
    cfg = getattr(books, name)()
    out = os.path.join(style.SCRATCH, 'out')
    os.makedirs(out, exist_ok=True)
    build(cfg, os.path.join(out, name + '.pdf'), redo)
