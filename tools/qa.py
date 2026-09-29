"""Quality assurance sweeps over a built book."""
import re
import sys
import os
import json
import collections
import pymupdf
from . import style, books, book as B, check, build
from .measure import Measurer
from .model import runs_text

IGN = set(' \t\r\n\u2060\u200b\u3000\u2002\ufeff\u00a0\u00ad')


def norm_counter(text):
    return collections.Counter(c for c in text if c not in IGN)


def pdf_text_of_pages(doc, pages, clip_top=52.0, clip_bottom=style.PAGE_H - 48.0):
    out = []
    for p in pages:
        page = doc[p.index]
        for blk in page.get_text('dict')['blocks']:
            for l in blk.get('lines', []):
                y = l['bbox'][1]
                if y < clip_top or y > clip_bottom:
                    # header / folio (allowed area of running heads); heading modules start lower than 52 anyway
                    continue
                out.append(''.join(s['text'] for s in l['spans']))
    return ''.join(out)


def fidelity(bb, pdf):
    """Compare the characters set in each text module with those extracted from the printed PDF."""
    doc = pymupdf.open(pdf)
    problems = []
    for mod in bb.mods:
        if mod.kind != 'text' or mod.mid == 'toc':
            continue
        exp = collections.Counter()
        for b in mod.blocks:
            if b['k'] in ('img', 'space'):
                continue
            exp += norm_counter(runs_text(b['runs']))
        got = norm_counter(pdf_text_of_pages(doc, bb.pages_of(mod)))
        miss = exp - got
        extra = got - exp
        if miss or extra:
            problems.append((mod.mid, dict(miss.most_common(8)), dict(extra.most_common(8)), sum(miss.values()), sum(extra.values())))
    return problems


if __name__ == '__main__':
    name = sys.argv[1]
    cfg = getattr(books, name)()
    out = os.path.join(style.SCRATCH, 'out')
    pdf = os.path.join(out, name + '.pdf')
    build.calibrate_all()
    m = Measurer()
    bb = B.BookBuilder(cfg, m)
    bb.typeset_all()
    m.close()
    bb.sequence()
    B.fill_toc_labels(bb, cfg['toc'])
    probs = fidelity(bb, pdf)
    print(name, 'modules with text differences:', len(probs))
    for p in probs[:40]:
        print('  ', p)


def source_fidelity(cfgs):
    """Characters of every source part vs the characters of the blocks built from it (whitespace ignored)."""
    from . import extract
    from .extract import load_body
    import glob
    have = collections.defaultdict(collections.Counter)
    for cfg in cfgs:
        for mod in cfg['modules']:
            if mod.kind != 'text':
                continue
            key = mod.mid[:-1] if (mod.mid.endswith('n') and mod.mid[:-1].startswith('part')) else mod.mid
            for b in mod.blocks:
                if b['k'] in ('img', 'space'):
                    continue
                have[key] += norm_counter(runs_text(b['runs']))
    diffs = []
    for f in sorted(glob.glob(extract.TEXT_DIR + '/part*.xhtml')):
        part = os.path.basename(f)[:-6]
        if part not in have:
            continue
        body = load_body(part)
        src = norm_counter(''.join(body.itertext()))
        miss = src - have[part]
        extra = have[part] - src
        if miss or extra:
            diffs.append((part, dict(miss.most_common(6)), dict(extra.most_common(6)), sum(miss.values()), sum(extra.values())))
    return diffs
