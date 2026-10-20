"""Collection PDF of single books sold as one set (认知三部曲 = books 36–38): cover + master contents + each volume's own PDF.
Run in the scratch of the first volume (its unpacked set gives the cover picture, its font subsets cover the whole set):
  BOOK_SCRATCH=$SP/q36 BOOK_GEOM=k16 BOOK_FONT_DIR=$SP/q36/fonts python -m tools.bk_collection renzhi
The volumes are read from <scratch of volume>/out/bNN.pdf and bNN.meta.json (tools.bk_build)."""
import os
import re
import sys
import json
import pymupdf
from . import style, render, build, book as B, special, bk
from .book import Mod, roman
from .books import page_module
from .measure import Measurer
from .model import run
from .post import finish_pdf

SETS = {
    'renzhi': dict(title='认知三部曲', books=(36, 37, 38), cover='cover00429.jpeg', file='36-38-认知三部曲（合集）'),
    'xifang': dict(title='西方现代思想家精品译丛（18卷）', books=tuple(range(41, 59)), cover='cover06209.jpeg',
                   file='41-58-西方现代思想家精品译丛（合集）', author='米瑟斯　哈耶克　波普尔　克尔凯郭尔',
                   names={45: '《开放社会及其敌人》第一卷', 46: '《开放社会及其敌人》第二卷', 50: '《非此即彼》（上）',
                          51: '《非此即彼》（下）'}),     # (two volumes of one title: told apart)
}


def vol_name(S, b):
    return S.get('names', {}).get(b) or f'《{bk.CFG[b]["title"]}》'
SKIP = ('封面', '版权页', '目录')
PART = re.compile(r'^第[一二三四五六七八九十]+部分')


def page_label(labels, i):
    """The printed folio of page i (0-based) of a volume, from its page labels."""
    lab = max((x for x in labels if x['startpage'] <= i), key=lambda x: x['startpage'])
    n = lab['firstpagenum'] + i - lab['startpage']
    return {'r': roman(n), 'D': str(n)}.get(lab['style'], '')


def scratch_of(b):
    return os.path.join(os.path.dirname(style.SCRATCH.rstrip('/')), bk.CFG[b]['scratch'])


def master_toc_blocks(S, metas):
    """Every volume (bold, with its page count) and its chapters with the volume's own folios; a volume in parts: the parts
    (and the entries beside them) one step up, their chapters under them."""
    blocks = [dict(k='h', style='tochead', rank=1, runs=[run('总　目　录')], id='master-toc'),
              dict(k='p', style='mtocnote', runs=[run('页码依各册自身编号，前置部分用罗马数字；点击条目即可跳转')])]
    for k, (b, meta) in enumerate(zip(S['books'], metas)):
        cover = f'b{b}:p1'
        blocks.append(dict(k='p', style='mbook', runs=[run(vol_name(S, b), h=cover)], h=cover,
                           pg=f'全书 {meta["pages"]} 页', tail='plain', rule=k > 0, before=2 if k else 1, minbefore=2 if k else 1))
        parts = any(lv == 1 and PART.match(t) for lv, t, _ in meta['outline'])
        under = False
        for lv, t, p in meta['outline']:
            tgt = f'b{b}:p{p}'
            label = t.replace('⁠', '')
            if lv == 1:
                if label in SKIP:
                    continue
                under = bool(PART.match(label))
                st = 'mvol' if parts else 'mtoc'
                x = dict(k='p', style=st, runs=[run(label, h=tgt)], h=tgt, pg=page_label(meta['labels'], p - 1))
                if st == 'mvol':
                    x.update(keep=2, minbefore=1)
                blocks.append(x)
            elif lv == 2 and under:
                blocks.append(dict(k='p', style='mtoc', runs=[run(label, h=tgt)], h=tgt, pg=page_label(meta['labels'], p - 1)))
    return blocks


def build_collection(name):
    S = SETS[name]
    outdir = os.path.join(style.SCRATCH, 'out')
    build.calibrate_all()
    vols = [os.path.join(scratch_of(b), 'out', f'b{b}') for b in S['books']]
    metas = [json.load(open(v + '.meta.json')) for v in vols]
    first = bk.CFG[S['books'][0]]
    cover = page_module('cover', 'cover', special.cover_html(S['cover']), folio=False)
    toc = Mod(mid='master-toc', zone='front', title='总目录', blocks=master_toc_blocks(S, metas), toc=False, head=True)
    front_cfg = dict(id='c0', title=S['title'], meta=dict(author=S.get('author', first['pdf_author'])), modules=[cover, toc], toc=toc)
    m = Measurer()
    bb = B.BookBuilder(front_cfg, m)
    bb.typeset_all()
    m.close()
    bb.sequence()
    html = render.document_html(bb.render_pages())
    raw = os.path.join(outdir, f'{name}-front.raw.pdf')
    render.print_pdf(html, raw, work_html=os.path.join(outdir, f'{name}-front.html'))
    merged = pymupdf.open(raw)
    bases = []
    for v in vols:
        bases.append(len(merged))
        merged.insert_pdf(pymupdf.open(v + '.pdf'), links=True, annots=True)
    anchors = dict((k, tuple(v)) for k, v in bb.anchors.items())
    outline = [[1, '封面', 1], [1, '总目录', 2]]
    labels = [{'startpage': 0, 'prefix': '', 'style': '', 'firstpagenum': 1},
              {'startpage': 1, 'prefix': '', 'style': 'r', 'firstpagenum': 1}]
    for b, meta, base in zip(S['books'], metas, bases):
        for p in range(1, meta['pages'] + 1):
            anchors[f'b{b}:p{p}'] = (base + p - 1, 0.0)
        outline.append([1, vol_name(S, b), base + 1])
        for lv, t, p in meta['outline']:
            outline.append([lv + 1, t, p + base])
        for lab in meta['labels']:
            labels.append(dict(lab, startpage=lab['startpage'] + base))
    out = os.path.join(outdir, S['file'] + '.pdf')
    tmp = out + '.tmp.pdf'
    merged.save(tmp)
    info = finish_pdf(tmp, out, anchors, outline, labels,
                      {'title': f'{S["title"]}（合集）', 'author': S.get('author', first['pdf_author']), 'subject': S['title']})
    os.remove(tmp)
    os.remove(raw)
    print('collection pages', len(pymupdf.open(out)), 'links', info['internal'], 'missing', info['missing'])
    return out


if __name__ == '__main__':
    build_collection(sys.argv[1])
