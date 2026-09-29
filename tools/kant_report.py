"""Acceptance numbers for the Kant volumes (writes docs/kant/QA-report.md) and the text difference source -> typeset."""
import os
import sys
import collections
import pymupdf
from . import style, build, check, book as B, qa, kant, kant_extract as KE, kant_struct as KS, kant_tables
from .measure import Measurer
from .model import runs_text

IGN = qa.IGN


def counter(t):
    return collections.Counter(c for c in t if c not in IGN)


def source_counter(v):
    """Characters of the source parts of volume v that end up in the book (contents / copyright pages excluded)."""
    fp = KS.front_parts(v)
    a, b = KS.VOL_PARTS[v]
    parts = [fp['preface'], fp['foreword']] + list(range(fp['body'], b + 1))
    c = collections.Counter()
    for n in parts:
        for it in KE.items(KS.P(n)):
            if it['k'] in ('img', 'table') or (it['k'] == 'note' and it['cls'] in ('noteTitle',)):
                continue
            for r in it['runs']:
                if r.get('i'):
                    continue
                t = r['t'].replace(' ', '')
                c += counter(t)
    return c


def block_counter(cfg):
    c = collections.Counter()
    for m in cfg['modules']:
        if m.kind == 'text' and m.mid not in ('toc', 'copyright'):
            for b in m.blocks:
                if b['k'] in ('img', 'space'):
                    continue
                if b.get('id', '').endswith('#top') and b['style'] == 'h1' and runs_text(b['runs']) == '注　释':
                    continue
                if b.get('style') == 'idxhead' and m.mid.startswith('notes'):
                    continue
                c += counter(runs_text(b['runs']).replace('⁠', ''))
        elif m.kind == 'page' and hasattr(m, 'lines'):
            for t in m.lines:
                c += counter(t.replace('⁠', ''))
    for tid, t in kant_tables.TABLES.items():
        pass
    return c


def volume(v, m):
    cfg = kant.book(v)
    bb = B.BookBuilder(cfg, m)
    bb.typeset_all()
    bb.sequence()
    B.fill_toc_labels(bb, cfg['toc'])
    pdf = os.path.join(style.SCRATCH, 'out', f'k{v}.pdf')
    pc = check.pdf_checks(pdf, bb)
    fid = qa.fidelity(bb, pdf)
    rep_tot = collections.Counter()
    n_loose = n_lines = 0
    for mod in cfg['modules']:
        if mod.kind != 'text':
            continue
        rep = check.module_report(mod)
        for k, val in rep.items():
            rep_tot[k] += len(val)
        for lb in mod.lbs:
            if lb.block['k'] == 'p' and lb.st['align'] == 'j':
                vi = mod.plan['variants'][lb.idx]
                for j in range(len(lb.starts[vi]) - 1):
                    n_lines += 1
                    w = lb.st['W'] - (lb.st['left'] + lb.st['right'] + (lb.st['first'] if j == 0 else 0)) * lb.st['fs']
                    if (w - lb.nat[vi][j]) / lb.st['fs'] > 3.0:
                        n_loose += 1
    doc = pymupdf.open(pdf)
    links = sum(len(p.get_links()) for p in doc)
    src = source_counter(v)
    have = block_counter(cfg)
    miss, extra = src - have, have - src
    return dict(v=v, cfg=cfg, pc=pc, fid=fid, rep=rep_tot, loose=n_loose, lines=n_lines, links=links,
                miss=miss, extra=extra, pages=len(doc))


def main(vols=None):
    build.calibrate_all()
    m = Measurer()
    rows = []
    for v in vols or range(1, 11):
        r = volume(v, m)
        rows.append(r)
        pc, rep = r['pc'], r['rep']
        print(f"vol {v} {kant.TITLES[v]}: pages {r['pages']} bottom {pc['ref_bottom']} bad_bottom {len(pc['bad_bottom'])} type3 {len(pc['type3'])} "
              f"gap {rep['gap']} head_bottom {rep['head_bottom']} head_short {rep['head_short']} lone {rep['lone']} last {rep['last_page']} "
              f"widow/orphan {rep['widow'] + rep['orphan']} loose {r['loose']}/{r['lines']} fid {len(r['fid'])} links {r['links']}")
        print('    source-only chars:', dict(r['miss'].most_common(12)), sum(r['miss'].values()))
        print('    typeset-only chars:', dict(r['extra'].most_common(12)), sum(r['extra'].values()))
    m.close()
    return rows


if __name__ == '__main__':
    main([int(a) for a in sys.argv[1:]] or None)
