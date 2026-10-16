"""PDF-level checks that the acceptance report (tools/bk_report) does not make:

    python -m tools.qa_pdf <book.pdf> [<book.meta.json>]

  grid   body-size lines whose baseline is off the line grid (the common last baseline - k * LINE);
  foot   a white band at the foot of a page that is not the last page of its module (a figure or a table that left
         the page short; the rule is: such a figure goes to the back of the book, one per page, linked both ways);
  joiner word joiners (U+2060) drawn with a width -- a gap before a note mark (fixed in tools/render.py; earlier PDFs).
The meta.json written next to the PDF by the build (pages of the modules) is found by itself when it is there.
"""
import collections
import json
import os
import sys
import pymupdf
from . import style


def ref_bottom(d):
    c = collections.Counter()
    for pg in d:
        ys = [l['spans'][0]['origin'][1] for b in pg.get_text('dict')['blocks'] for l in b.get('lines', [])
              if l['spans'] and l['spans'][0]['text'].strip() and abs(l['spans'][0]['size'] - style.FONT) < 0.6]
        if ys:
            c[round(max(ys), 1)] += 1
    return c.most_common(1)[0][0] if c else None


def grid(d, bottom):
    agg, ex = collections.Counter(), {}
    for pn, pg in enumerate(d):
        if any(im['bbox'][3] - im['bbox'][1] > 40 for im in pg.get_image_info()):
            continue                                     # pages with pictures: captions sit off the grid on purpose
        for b in pg.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                sp = [s for s in l['spans'] if s['text'].strip()]
                if not sp or not style.FONT - 1.1 <= sp[0]['size'] <= style.FONT + 0.6:
                    continue
                if not any(k in sp[0]['font'] for k in ('Serif', 'WenKai')):
                    continue                             # headings (their own families) are centred in their slots
                y = sp[0]['origin'][1]
                if not style.TOP - 6 < y < bottom + 5:
                    continue
                off = round((bottom - y) % style.LINE, 1)
                if 0.15 < off < style.LINE - 0.15:
                    k = (sp[0]['font'][:22], round(sp[0]['size'], 1), off)
                    agg[k] += 1
                    ex.setdefault(k, []).append((pn + 1, ''.join(s['text'] for s in sp)[:16]))
    return [(n, k, ex[k][:4]) for k, n in agg.most_common()]


def foot(d, meta, bottom):
    lab2idx = {d[i].get_label(): i for i in range(len(d))}
    starts = sorted(set([lab2idx[l] for _, l in meta.get('toc', []) if l in lab2idx] + [0, 1, 2, 3]))
    last = {s - 1 for s in starts[1:]} | {len(d) - 1}
    t0 = next((lab2idx[l] for m, l in meta.get('toc', []) if m == 'toc' and l in lab2idx), None)
    if t0 is not None:                                            # the contents: its pages end between entries
        t1 = next((s for s in starts if s > t0), len(d))
        last |= set(range(t0, t1))
    out = []
    for i, pg in enumerate(d):
        if i in last or i < 4:
            continue
        low = 0.0
        for b in pg.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                for s in l['spans']:
                    if s['text'].strip() and s['bbox'][3] < bottom + 25:
                        low = max(low, s['bbox'][3])
        for im in pg.get_image_info():
            if im['bbox'][3] - im['bbox'][1] > 20:
                low = max(low, im['bbox'][3])
        band = bottom + 3 - low
        if band > 14:
            out.append((i + 1, pg.get_label(), round(band, 1)))
    return out


def joiners(d):
    n, bad, ex = 0, 0, []
    for pno, pg in enumerate(d):
        for b in pg.get_text('rawdict')['blocks']:
            for l in b.get('lines', []):
                chars = [c for s in l['spans'] for c in s['chars']]
                for i, c in enumerate(chars[:-1]):
                    if c['c'] == '⁠':
                        n += 1
                        if chars[i + 1]['origin'][0] - c['origin'][0] > 0.3:
                            bad += 1
                            if len(ex) < 5:
                                ex.append((pno + 1, chars[i + 1]['c']))
    return n, bad, ex


if __name__ == '__main__':
    pdf = sys.argv[1]
    mp = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(pdf)[0] + '.meta.json'
    d = pymupdf.open(pdf)
    bottom = ref_bottom(d)
    print(f'{os.path.basename(pdf)}: {len(d)} 页，整页末行基线 {bottom} pt')
    g = grid(d, bottom)
    print(f'grid   不在行格上的正文行：{sum(n for n, _, _ in g)}')
    for n, k, ex in g[:12]:
        print(f'         {n:4d} {k} {ex}')
    if os.path.exists(mp):
        f = foot(d, json.load(open(mp)), bottom)
        print(f'foot   页底留白（非章节末页）：{len(f)}')
        for x in f[:20]:
            print('        ', x)
    else:
        print('foot   （没有 meta.json，跳过）')
    n, bad, ex = joiners(d)
    print(f'joiner 词连接符 {n} 个，其中占了宽度的 {bad} 个 {ex}')
