"""Whole-collection PDF: collection cover + master contents + the four books (each built module by module)."""
import os
import sys
import json
import pymupdf
from . import style, render, books, book as B, build
from .book import Mod
from .measure import Measurer
from .model import run
from .post import finish_pdf

BOOKS = [('b1', 'book1', '小逻辑'), ('b2', 'book2', '黑格尔早期神学著作'),
         ('b3', 'book3', '精神现象学'), ('b4', 'book4', '哲学史讲演录')]


def master_toc_blocks(cfgs, metas):
    blocks = [dict(k='h', style='tochead', rank=1, runs=[run('总　目　录')], id='master-toc')]
    for (bid, name, title), cfg, meta in zip(BOOKS, cfgs, metas):
        first = next(m for m in cfg['modules'] if m.zone != 'cover')
        labels = dict(meta['toc'])
        blocks.append(dict(k='p', style='toc0', runs=[run(f'《{title}》', h=f'{bid}:{cfg["modules"][0].mid}')],
                           h=f'{bid}:{cfg["modules"][0].mid}', pg=f'{meta["pages"]} 页', keep=1))
        last_vol = None
        for mod in cfg['modules']:
            if not mod.toc or mod.toc_level != 1 or mod.mid == 'toc':
                continue
            if mod.volume and mod.volume != last_vol:
                last_vol = mod.volume
                first_of_vol = next((x for x in cfg['modules'] if x.volume == mod.volume and x.mid in labels), None)
                if first_of_vol is not None:
                    blocks.append(dict(k='p', style='toc0', runs=[run(mod.volume, h=f'{bid}:{first_of_vol.mid}')],
                                       h=f'{bid}:{first_of_vol.mid}', pg=labels[first_of_vol.mid], keep=1))
            label = mod.toc_title or mod.title
            if not label or mod.mid not in labels:
                continue
            prefix = f'{mod.volume}　' if False else ''
            blocks.append(dict(k='p', style='mtoc', runs=[run(prefix + label, h=f'{bid}:{mod.mid}')],
                               h=f'{bid}:{mod.mid}', pg=labels[mod.mid]))
    return blocks


def build_collection(outdir):
    from .style import LINK_BASE
    build.calibrate_all()
    cfgs = [getattr(books, name)() for _, name, _ in BOOKS]
    metas = [json.load(open(os.path.join(outdir, name + '.meta.json'))) for _, name, _ in BOOKS]
    # ---- front: cover + master table of contents
    from . import special
    cover = books.page_module('cover', 'cover', special.cover_html('cover02021.jpeg'), folio=False)
    toc = Mod(mid='master-toc', zone='front', title='总目录', blocks=master_toc_blocks(cfgs, metas), toc=False, head=True)
    front_cfg = dict(id='b0', title='贺麟中译黑格尔经典著作', meta=dict(author='〔德〕黑格尔 著'), modules=[cover, toc], toc=toc)
    m = Measurer()
    bb = B.BookBuilder(front_cfg, m)
    bb.typeset_all()
    m.close()
    bb.sequence()
    html = render.document_html(bb.render_pages())
    raw = os.path.join(outdir, 'front.raw.pdf')
    render.print_pdf(html, raw, work_html=os.path.join(outdir, 'front.html'))
    nfront = len(bb.pages)
    # ---- merge
    merged = pymupdf.open(raw)
    bases = []
    for (_, name, _) in BOOKS:
        bases.append(len(merged))
        merged.insert_pdf(pymupdf.open(os.path.join(outdir, name + '.pdf')), links=True, annots=True)
    # ---- global anchors / outline / labels
    anchors = dict((k, tuple(v)) for k, v in bb.anchors.items())
    outline = [[1, '封面', 1], [1, '总目录', 2]]
    labels = [{'startpage': 0, 'prefix': '', 'style': '', 'firstpagenum': 1},
              {'startpage': 1, 'prefix': '', 'style': 'r', 'firstpagenum': 1}]
    for (bid, name, title), meta, base in zip(BOOKS, metas, bases):
        for k, (pg, y) in meta['anchors'].items():
            anchors[f'{bid}:{k}'] = (pg + base, y)
        outline.append([1, f'《{title}》', base + 1])
        for lv, t, p in meta['outline']:
            outline.append([lv + 1, t, p + base])
        for lab in meta['labels']:
            labels.append(dict(lab, startpage=lab['startpage'] + base))
    out = os.path.join(outdir, '贺麟中译黑格尔经典著作.pdf')
    tmp = out + '.tmp.pdf'
    merged.save(tmp)
    info = finish_pdf(tmp, out, anchors, outline, labels,
                      {'title': '贺麟中译黑格尔经典著作', 'author': '〔德〕黑格尔', 'subject': '小逻辑 / 黑格尔早期神学著作 / 精神现象学 / 哲学史讲演录'})
    os.remove(tmp)
    os.remove(raw)
    print('collection pages', len(pymupdf.open(out)), 'links', info['internal'], 'missing', info['missing'])
    return out


if __name__ == '__main__':
    build_collection(os.path.join(style.SCRATCH, 'out'))
