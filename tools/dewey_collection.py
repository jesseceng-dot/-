"""Whole-collection PDF of the Dewey selection: cover + master contents + the eleven volumes (each built module by module)."""
import os
import sys
import json
import pymupdf
from . import style, render, build, book as B, special, dewey
from .book import Mod
from .books import page_module
from .measure import Measurer
from .model import run
from .post import finish_pdf

TITLE = '杜威著作精选11种'
BOOKS = [(f'd{v}', v, dewey.TITLES[v]) for v in range(1, 12)]
SKIP = ('主编序',)


def is_skipped(label):
    return label.strip() in SKIP


def master_toc_blocks(cfgs, metas):
    """Collection-level contents: every volume with its works (bold) and the modules under them, each with the volume's own folio."""
    blocks = [dict(k='h', style='tochead', rank=1, runs=[run('总　目　录')], id='master-toc'),
              dict(k='p', style='mtocnote', runs=[run('页码依各册自身编号，前置部分用罗马数字；点击条目即可跳转')])]
    first = True
    for (bid, v, title), cfg, meta in zip(BOOKS, cfgs, metas):
        labels = dict(meta['toc'])
        cover = f'{bid}:{cfg["modules"][0].mid}'
        blocks.append(dict(k='p', style='mbook', runs=[run(f'《{title}》', h=cover)], h=cover, pg=f'全书 {meta["pages"]} 页',
                           tail='plain', rule=not first, before=1 if first else 2, minbefore=1 if first else 2))
        first = False
        under = False
        for mod in cfg['modules']:
            if mod.mid == 'toc' or not mod.toc or mod.mid not in labels:
                continue
            label = mod.toc_title or mod.title
            if not label:
                continue
            tgt = f'{bid}:{mod.mid}'
            if mod.kind == 'page':
                if mod.mid == 'plates':
                    blocks.append(dict(k='p', style='mvol', runs=[run('书后插图', h=tgt)], h=tgt, pg=labels[mod.mid], keep=2, minbefore=1))
                    under = False
                    continue
                under = True
                blocks.append(dict(k='p', style='mvol', runs=[run(label, h=tgt)], h=tgt, pg=labels[mod.mid], keep=2, minbefore=1))
                continue
            if mod.toc_level != 1 or is_skipped(label):
                continue
            blocks.append(dict(k='p', style='mtoc', runs=[run(label, h=tgt)], h=tgt, pg=labels[mod.mid]))
    return blocks


def build_collection(outdir):
    build.calibrate_all()
    cfgs = [dewey.book(v) for _, v, _ in BOOKS]
    metas = [json.load(open(os.path.join(outdir, f'{bid}.meta.json'))) for bid, _, _ in BOOKS]
    cover = page_module('cover', 'cover', special.cover_html('cover01866.jpeg'), folio=False)
    toc = Mod(mid='master-toc', zone='front', title='总目录', blocks=master_toc_blocks(cfgs, metas), toc=False, head=True)
    front_cfg = dict(id='d0', title=TITLE, meta=dict(author=dewey.AUTHOR), modules=[cover, toc], toc=toc)
    m = Measurer()
    bb = B.BookBuilder(front_cfg, m)
    bb.typeset_all()
    m.close()
    bb.sequence()
    html = render.document_html(bb.render_pages())
    raw = os.path.join(outdir, 'front.raw.pdf')
    render.print_pdf(html, raw, work_html=os.path.join(outdir, 'front.html'))
    merged = pymupdf.open(raw)
    bases = []
    for bid, _, _ in BOOKS:
        bases.append(len(merged))
        merged.insert_pdf(pymupdf.open(os.path.join(outdir, bid + '.pdf')), links=True, annots=True)
    anchors = dict((k, tuple(v)) for k, v in bb.anchors.items())
    outline = [[1, '封面', 1], [1, '总目录', 2]]
    labels = [{'startpage': 0, 'prefix': '', 'style': '', 'firstpagenum': 1},
              {'startpage': 1, 'prefix': '', 'style': 'r', 'firstpagenum': 1}]
    for (bid, v, title), meta, base in zip(BOOKS, metas, bases):
        for k, (pg, y) in meta['anchors'].items():
            anchors[f'{bid}:{k}'] = (pg + base, y)
        outline.append([1, f'《{title}》', base + 1])
        for lv, t, p in meta['outline']:
            outline.append([lv + 1, t, p + base])
        for lab in meta['labels']:
            labels.append(dict(lab, startpage=lab['startpage'] + base))
    out = os.path.join(outdir, f'00-{TITLE}（合集）.pdf')
    tmp = out + '.tmp.pdf'
    merged.save(tmp)
    info = finish_pdf(tmp, out, anchors, outline, labels, {'title': TITLE, 'author': '〔美〕约翰·杜威', 'subject': TITLE})
    os.remove(tmp)
    os.remove(raw)
    print('collection pages', len(pymupdf.open(out)), 'links', info['internal'], 'missing', info['missing'])
    return out


if __name__ == '__main__':
    build_collection(os.path.join(style.SCRATCH, 'out'))
