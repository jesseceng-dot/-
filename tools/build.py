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
    out = []
    for p in bb.pages:
        pass
    seen = set()
    for mod in bb.mods:
        if mod.zone == 'cover':
            out.append([1, '封面', bb.pages_of(mod)[0].index + 1])
            continue
        if not mod.toc and mod.mid not in ('toc',):
            if mod.mid in ('title', 'copyright') or mod.mid.endswith('0002'):
                out.append([1, mod.title or mod.mid, bb.pages_of(mod)[0].index + 1])
            continue
        first = bb.pages_of(mod)[0].index + 1
        title = mod.toc_title or mod.title or mod.mid
        out.append([1, title, first])
        if mod.kind == 'text':
            for bi, b in enumerate(mod.blocks):
                if b['k'] == 'h' and b.get('rank', 9) in (2, 3) and not b.get('notoc'):
                    pg = bb.block_pages.get((mod.mid, bi))
                    if pg is not None:
                        out.append([b['rank'], B.title_text(b['runs']), pg + 1])
    # bookmark levels must not jump by more than one
    fixed, last = [], 0
    for lv, t, p in out:
        lv = min(lv, last + 1)
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


def build(cfg, out_pdf):
    t0 = time.time()
    calibrate_all()
    m = Measurer()
    bb = B.BookBuilder(cfg, m)
    bb.typeset_all()
    m.close()
    print('typeset', round(time.time() - t0, 1), 's; pages', sum(mod.npages for mod in cfg['modules']), flush=True)
    from . import check
    for mod in cfg['modules']:
        if mod.kind == 'text':
            rep = check.module_report(mod)
            hard = {k: len(v) for k, v in rep.items() if v and k not in ('loose',)}
            print(f'  {mod.mid:9s} p{mod.npages:4d} cost {mod.plan["cost"]:7.1f} {hard}', flush=True)
    bb.sequence()
    B.fill_toc_labels(bb, cfg['toc'])
    htmls = bb.render_pages()
    html = render.document_html(htmls)
    raw = out_pdf + '.raw.pdf'
    render.print_pdf(html, raw, work_html=out_pdf + '.html')
    print('printed', round(time.time() - t0, 1), 's', flush=True)
    info = finish_pdf(raw, out_pdf, bb.anchors, outline_for(bb), labels_for(bb),
                      {'title': cfg['title'], 'author': cfg['meta']['author'], 'subject': '贺麟中译黑格尔经典著作'})
    os.remove(raw)
    print('links', info['internal'], 'internal', info['external'], 'external; missing', len(info['missing']),
          list(info['missing'].items())[:8], flush=True)
    return bb, info


if __name__ == '__main__':
    name = sys.argv[1]
    cfg = getattr(books, name)()
    out = os.path.join(style.SCRATCH, 'out')
    os.makedirs(out, exist_ok=True)
    build(cfg, os.path.join(out, name + '.pdf'))
