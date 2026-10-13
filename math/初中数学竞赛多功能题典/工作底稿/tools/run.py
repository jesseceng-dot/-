"""Apply fix specifications to the book."""
import os, sys, json, importlib
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, pymupdf
import engine as E, para, totex
H = 841.89
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def apply_edits(tex, edits, fid):
    for e in edits:
        old, new = e[0], e[1]
        cnt = e[2] if len(e) > 2 else 1
        n = tex.count(old)
        if cnt == 'all':
            cnt = n if n else 1
        if n != cnt:
            raise ValueError('%s: edit %r found %d times (expected %d) in:\n%s' % (fid, old, n, cnt, tex))
        tex = tex.replace(old, new)
    return tex


def skeleton(doc, pn, top, bot, x_first):
    return totex.paragraph_tex(doc, pn, H - top, H - bot, x_first)


def spec_y(s):
    """vertical position of a spec's region; specs on a page are applied from
    the bottom up, so that content shifted by an edit above has already been
    processed (all coordinates in specs refer to the original page)"""
    if 'order' in s:
        return s['order']
    k = s.get('kind', 'para')
    if k in ('para',):
        return s['bot']
    if k in ('remove', 'move'):
        return s['rect'][1]
    if k == 'disp':
        return s['region'][1]
    if k == 'add':
        return s['y']
    if k == 'glyph':
        return s['glyphs'][0][3]
    if k == 'shift':
        return s.get('y_to', para.FOOT_Y)
    return 0


def do_page(pdf, doc, bf, pn, specs, report):
    pe = E.PageEdit(pdf, pn, bf)
    for s in sorted(specs, key=spec_y):
        fid = 'p%d_%s' % (pn, s['id'].replace('.', '_').replace(' ', ''))
        k = s.get('kind', 'para')
        if k == 'para':
            x_first = s.get('x') or para.first_text_x(pe, s['y'])
            tex = s.get('tex')
            if tex is None:
                tex = skeleton(doc, pn, s['top'], s['bot'], x_first)
                tex = apply_edits(tex, s.get('edits', []), fid)
            tex = s.get('pre', '') + tex
            r = para.retypeset(pe, x_first, s['top'], s['bot'], tex, fid, extra=s.get('extra', ''),
                               xmin_other=s.get('xmin_other'), top_band=s.get('top_band'),
                               keep_unchanged=s.get('keep_unchanged', True), levels=s.get('levels', True),
                               single_y=s['y'] if s.get('single') else None, orig_base=s.get('obase'),
                               max_lines=s.get('max_lines'), xtol=s.get('xtol', 1.2),
                               para_x=s.get('para_x'), skip_lines=s.get('skip_lines', 0))
            if r['delta'] and s.get('shift', True):
                # everything below the paragraph's last original line moves (incl. a
                # figure whose top reaches into the line's descender zone)
                ybelow = r['obase'][-1] - 2.5 if s.get('shift_from') is None else s['shift_from']
                n = para.shift_region(pe, ybelow, r['delta'])
                report.append('%s: shifted content below %.1f by %.2f (%s)' % (fid, ybelow, r['delta'], n))
            report.append('%s: lines %d->%d changed %s' % (fid, len(r['obase']), len(r['nbase']), r['changed']))
        elif k == 'remove':
            x0, y0, x1, y1 = s['rect']
            gl = pe.glyphs_in(x0, y0, x1, y1, s.get('gpred'))
            its = pe.items_in(x0, y0, x1, y1, kinds=s.get('kinds', ('path', 'do')), full=True)
            pe.remove_glyphs(gl); pe.remove_items(its)
            report.append('%s: removed %d glyphs %d items' % (fid, len(gl), len(its)))
        elif k == 'move':
            x0, y0, x1, y1 = s['rect']
            gl = pe.glyphs_in(x0, y0, x1, y1, s.get('gpred'))
            its = pe.items_in(x0, y0, x1, y1, kinds=s.get('kinds', ('path', 'do')), full=True)
            pe.move(gl, its, s.get('dx', 0), s.get('dy', 0))
            report.append('%s: moved %d glyphs %d items by (%.2f,%.2f)' % (fid, len(gl), len(its), s.get('dx', 0), s.get('dy', 0)))
        elif k == 'shift':
            n = para.shift_region(pe, s['y_from'], s['delta'], y_to=s.get('y_to', para.FOOT_Y))
            report.append('%s: shifted %s' % (fid, n))
        elif k == 'disp':
            import disp
            extra = s.get('extra', r'\usepackage{array}')
            r = disp.redisplay(pe, s['region'], s['tex_old'], s['tex_new'], fid, extra=extra, keep=s.get('keep'),
                               body_fmt=s.get('body_fmt'), verbose=False)
            report.append('%s: display re-typeset (dx %.3f dy %.3f): -%d/+%d glyphs, -%d/+%d rules' % (
                fid, r['dx'], r['dy'], len(r['gone']), len(r['added']), len(r['rgone']), len(r['radded'])))
        elif k == 'add':
            # typeset a new paragraph whose first line starts at (x, y)
            gl, rules = para.typeset(s['x'], s['tex'], fid, s.get('extra', ''))
            base = para.cluster_baselines(gl, lambda g: g['font'], lambda g: g['y'], s.get('levels', True))
            dy = s['y'] - base[0]
            emit = []
            for g in gl:
                fobj, code = E.map_layout_glyph(bf, g)
                emit.append(dict(bookfont=fobj, code=code, x=g['x'], y=g['y'] + dy, size=g['size']))
            pe.emit_glyphs(emit)
            for r in rules:
                if r['paint'] == 'S':
                    pe.emit_rule_stroke(r['bbox'][0], r['bbox'][1] + dy, r['bbox'][2], r['lw'])
                else:
                    bb = r['bbox']; pe.emit_rect_fill(bb[0], bb[1] + dy, bb[2] - bb[0], bb[3] - bb[1])
            report.append('%s: added %d lines (%d glyphs) at y=%.2f' % (fid, len(base), len(gl), s['y']))
        elif k == 'glyph':
            # add single glyphs: list of (font name, char or code, x, y, size)
            emit = []
            for fn, ch, x, y, size in s['glyphs']:
                fobj = bf.get(fn)
                fi = E.FONTS.get(fobj, pdf)
                code = ch if isinstance(ch, int) else fi.fromunicode[ch]
                if not fi.has(code):
                    raise KeyError('%s: code %d not in %s' % (fid, code, fn))
                emit.append(dict(bookfont=fobj, code=code, x=x, y=y, size=size))
                if s.get('color'):
                    emit[-1]['color'] = s['color']
            pe.emit_glyphs(emit)
            report.append('%s: added glyphs %s' % (fid, [(g[1], g[2], g[3]) for g in s['glyphs']]))
        elif k == 'custom':
            s['fn'](pe, doc, bf, report)
        else:
            raise ValueError(k)
        if pe.log:
            report.extend('%s: %s' % (fid, l) for l in pe.log); pe.log = []
        if s.get('commit_each', True):
            pe.commit()
    pe.commit()


def main(spec_module, out, pages=None):
    mod = importlib.import_module(spec_module)
    specs = mod.SPECS
    src = os.path.join(BASE, 'src/book.pdf')
    pdf = pikepdf.open(src)
    doc = pymupdf.open(src)
    bf = E.BookFonts(pdf)
    by = {}
    for s in specs:
        by.setdefault(s['page'], []).append(s)
    report = []
    for pn in sorted(by):
        if pages and pn not in pages:
            continue
        do_page(pdf, doc, bf, pn, by[pn], report)
    pdf.save(out)
    return report




def line_diff(o, n, ob, nb):
    """describe the difference between an original line (Glyph objects) and a
    re-typeset line (dicts), both sorted by x."""
    import difflib
    a = [g.uni or '%s#%d' % (E.norm_font_name(g.font.name), g.code) for g in o]
    b = [(g['uni'] if (g['uni'] and o and True) else '%s#%d' % (E.norm_font_name(g['font']), g['code'])) for g in n]
    # characters without unicode in the book compare by font/code on both sides
    nob = {i for i, g in enumerate(o) if not g.uni}
    b = [x if not x or not any(a[i] == '%s#%d' % (E.norm_font_name(g['font']), g['code']) for i in nob) else '%s#%d' % (E.norm_font_name(g['font']), g['code']) for x, g in zip(b, n)]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    worst = (0, None)
    ops = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                g, h = o[i1 + k], n[j1 + k]
                d = max(abs(g.x - h['x']), abs((g.y - ob) - (h['y'] - nb)))
                if d > worst[0]:
                    worst = (d, '%r@%.1f dx=%+.2f dy=%+.2f' % (g.uni, g.x, h['x'] - g.x, (h['y'] - nb) - (g.y - ob)))
        else:
            ops.append('%s %r->%r' % (tag, ''.join(a[i1:i2]), ''.join(b[j1:j2])))
    return worst, ops


def selftest(spec_module, pages=None, only=None):
    """typeset the unedited skeleton of each paragraph spec and report every
    line that does not reproduce the original."""
    mod = importlib.import_module(spec_module)
    src = os.path.join(BASE, 'src/book.pdf')
    pdf = pikepdf.open(src); doc = pymupdf.open(src); bf = E.BookFonts(pdf)
    for s in mod.SPECS:
        if s.get('kind', 'para') != 'para' or (pages and s['page'] not in pages) or (only and s['id'] not in only):
            continue
        pn = s['page']
        fid = 'p%d_%s' % (pn, s['id'].replace('.', '_').replace(' ', ''))
        pe = E.PageEdit(pdf, pn, bf)
        x_first = s.get('x') or para.first_text_x(pe, s['y'])
        tex = s.get('tex_orig')
        if tex is None and s.get('tex') is None:
            tex = skeleton(doc, pn, s['top'], s['bot'], x_first)
        if tex is None:
            print('%s: no original tex, skipped' % fid); continue
        tex = s.get('pre', '') + tex
        r = para.retypeset(pe, x_first, s['top'], s['bot'], tex, fid + '_self', extra=s.get('extra', ''),
                           xmin_other=s.get('xmin_other'), dry=True, verbose=False, levels=s.get('levels', True),
                           single_y=s['y'] if s.get('single') else None, keep_same_text=False, orig_base=s.get('obase'),
                           max_lines=s.get('max_lines'))
        bad = []
        for i, b in enumerate(r['nbase']):
            if i not in r['changed']:
                continue
            if i >= len(r['obase']):
                bad.append('  line %d: extra line' % i); continue
            ob = r['obase'][i]
            o = sorted(r['orows'][ob], key=lambda g: (g.x, g.y)); n = sorted(r['nrows'][b], key=lambda g: (g['x'], g['y']))
            worst, ops = line_diff(o, n, ob, b)
            bad.append('  line %d: worst %.2f %s %s' % (i, worst[0], worst[1] or '', '; '.join(ops[:4])))
        if len(r['nbase']) != len(r['obase']):
            bad.append('  line count %d -> %d' % (len(r['obase']), len(r['nbase'])))
        print('%s: %s' % (fid, 'OK' if not bad else 'DIFF'))
        for l in bad:
            print(l)


if __name__ == '__main__':
    if sys.argv[1] == '--selftest':
        selftest(sys.argv[2], [int(p) for p in sys.argv[3:]] or None)
    else:
        rep = main(sys.argv[1], sys.argv[2], [int(p) for p in sys.argv[3:]] or None)
        print('\n'.join(rep))
