"""Inspect a printed PDF: per-page line count, first/last baseline, fonts."""
import pymupdf


def page_lines(page):
    out = []
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            sp = [s for s in l['spans'] if s['text'].strip()]
            if not sp:
                continue
            out.append(dict(y=round(sp[0]['origin'][1], 2), x0=round(l['bbox'][0], 2), x1=round(l['bbox'][2], 2),
                            text=''.join(s['text'] for s in l['spans']), size=round(sp[0]['size'], 2)))
    out.sort(key=lambda d: (d['y'], d['x0']))
    return out


def summarize(pdf, first=0, last=None):
    d = pymupdf.open(pdf)
    rows = []
    for pn in range(first, last if last is not None else len(d)):
        ls = page_lines(d[pn])
        rows.append((pn, len(ls), ls[0]['y'] if ls else None, ls[-1]['y'] if ls else None))
    return rows
