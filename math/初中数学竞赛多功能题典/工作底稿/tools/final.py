"""final.py out.pdf : apply every correction batch to the original book in one pass."""
import os, sys, importlib, json
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, pymupdf
import engine as E, run

MODULES = ['specs1', 'specs_a', 'specs_b', 'specs_c', 'specs_d', 'specs_e', 'specs_f',
           'specs_g', 'specs_h', 'specs_i', 'specs_j', 'specs_k', 'specs_l', 'specs_fig']


def all_specs():
    specs = []
    for m in MODULES:
        for s in importlib.import_module(m).SPECS:
            specs.append(dict(s, _mod=m))
    seen = {}
    for s in specs:
        key = (s['page'], s['id'])
        if key in seen:
            raise ValueError('duplicate spec %r in %s and %s' % (key, seen[key], s['_mod']))
        seen[key] = s['_mod']
    return specs


def drop_unused_fonts(pdf, report, names=('ArialMT',)):
    """remove page font resources of non-embedded fonts that no longer show any text
    (19.118: the sans-serif exponent n was replaced by the book's math italic)"""
    for i, page in enumerate(pdf.pages):
        fonts = page.obj.get('/Resources', {}).get('/Font')
        if not fonts:
            continue
        cand = [k for k in fonts.keys() if any(n in str(fonts[k].get('/BaseFont', '')) for n in names)]
        if not cand:
            continue
        ops = list(pikepdf.parse_content_stream(page))
        def has_glyphs(operands, o):
            if o == 'TJ':
                return any(isinstance(x, pikepdf.String) and len(bytes(x)) for x in operands[0])
            return o in ('Tj', "'", '"') and len(bytes(operands[-1])) > 0
        cur = None; shows = set()
        for operands, op in ops:
            o = str(op)
            if o == 'Tf':
                cur = str(operands[0])
            elif o in ('Tj', 'TJ', "'", '"') and has_glyphs(operands, o):
                shows.add(cur)
        for key in cand:
            if key in shows:
                continue
            # the font's Tf and its glyph-less (positioning only) TJ left over from removed glyphs;
            # the next text line is placed by Td from the line matrix, so the positions do not change
            kept = []; cur = None
            for a, op in ops:
                o = str(op)
                if o == 'Tf':
                    cur = str(a[0])
                    if cur == key:
                        continue
                if o == 'TJ' and cur == key and not has_glyphs(a, o):
                    continue
                kept.append((a, op))
            ops = kept
            page.Contents = pdf.make_stream(pikepdf.unparse_content_stream(ops))
            base = str(fonts[key].get('/BaseFont'))
            del fonts[key]
            report.append('p%d: dropped unused font resource %s (%s)' % (i + 1, key, base))


def main(out):
    src = os.path.join(run.BASE, 'src/book.pdf')
    pdf = pikepdf.open(src)
    doc = pymupdf.open(src)
    bf = E.BookFonts(pdf)
    by = {}
    for s in all_specs():
        by.setdefault(s['page'], []).append(s)
    report = []
    for pn in sorted(by):
        run.do_page(pdf, doc, bf, pn, by[pn], report)
    drop_unused_fonts(pdf, report)
    pdf.save(out, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
    return report, sorted(by)


if __name__ == '__main__':
    rep, pages = main(sys.argv[1])
    open(sys.argv[1] + '.log', 'w').write('\n'.join(rep) + '\n')
    print('pages edited:', len(pages))
    print('\n'.join(l for l in rep if 'WARN' in l or 'shift' in l))
