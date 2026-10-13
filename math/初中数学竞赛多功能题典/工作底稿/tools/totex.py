"""Reconstruct a LaTeX source skeleton for a paragraph of the book from the
visible glyphs, so that a fix can be applied as a textual edit."""
import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
import pymupdf
import vis

MATHFONTS = ('CMMI', 'CMR', 'CMSY', 'CMEX', 'MSAM', 'MSBM', 'Computer Modern')
SYM = {'·': r'\cdot ', '−': '-', '△': r'\triangle ', '⊥': r'\bot ', '∠': r'\angle ', '⊙': r'\odot ', '∥': r'\parallel ',
       '∼': r'\sim ', '≅': r'\cong ', '≤': r'\le ', '≥': r'\ge ', '≠': r'\ne ', '×': r'\times ', '÷': r'\div ', '±': r'\pm ',
       '∽': r'\backsim ', '⋆': r'\bigstar ', '◦': r'\circ ', '′': "'", '″': "''", '∈': r'\in ', '∞': r'\infty ', '→': r'\to ',
       '⩾': r'\geqslant ', '⩽': r'\leqslant ', '…': r'\ldots ', '···': r'\cdots ', '|': '|',
       '∪': r'\cup ', '∩': r'\cap ', '⊂': r'\subset ', '∅': r'\emptyset ', '∀': r'\forall ', '∃': r'\exists ', '⇒': r'\Rightarrow ',
       '⇔': r'\Leftrightarrow ', '≡': r'\equiv ', '≈': r'\approx ', '∑': r'\sum ', '∏': r'\prod ', '√': r'\surd ', '̸': r'\not ',
       'π': r'\pi ', 'α': r'\alpha ', 'β': r'\beta ', 'γ': r'\gamma ', 'θ': r'\theta ', 'λ': r'\lambda ', 'µ': r'\mu ', 'μ': r'\mu ',
       'φ': r'\varphi ', 'ϕ': r'\phi ', 'ω': r'\omega ', 'δ': r'\delta ', 'ε': r'\varepsilon ', 'ρ': r'\rho ', 'σ': r'\sigma ', 'τ': r'\tau ',
       'Δ': r'\Delta ', 'ξ': r'\xi ', 'η': r'\eta ', 'ψ': r'\psi '}


def is_math_item(it):
    if it.kind in ('frac', 'sqrt', 'angle', 'ov', 'un'):
        return True
    return it.font.startswith(MATHFONTS)


def math_text(it, inner=False):
    t = it.text
    if it.kind in ('frac',) and not inner:
        # a braced display fraction is an Ord atom (no thin spaces around it)
        t = t.replace('\\frac', '\\dfrac', 1)
    out = []
    i = 0
    # translate unicode symbols in composite texts too
    for ch in t:
        out.append(SYM.get(ch, ch))
    s = ''.join(out)
    s = s.replace('\\cdot  ', '\\cdot ')
    return s


from vis import BIN, REL, PUNCT, OPENS, atom_class, left_right_pairs, NULLDELIM, DELIM, open_bars


def run_tex(items):
    """items: sorted Items of one math run -> math source using sub/sup logic"""
    if not items:
        return ''
    msize = max(i.size for i in items)
    big = [it for it in items if it.size >= msize - 0.6]
    from collections import Counter
    mb = Counter(round(it.base * 2) / 2 for it in big).most_common(1)[0][0]
    lefts, rights = left_right_pairs(items, msize)
    obars = open_bars(items, msize)
    out = []; mode = None; buf = []

    def flush():
        nonlocal buf
        if buf:
            s = ''.join(buf)
            if mode == '^':
                out.append('^{' + s + '}')
            elif mode == '_':
                out.append('_{' + s + '}')
            else:
                out.append(s)
        buf = []
    for idx, it in enumerate(items):
        d = mb - it.base
        small = it.size < msize - 1.5
        m = '^' if (small and d > 1.2) else ('_' if (small and d < -0.8) else None)
        if m != mode:
            flush(); mode = m
        if idx in lefts:
            buf.append('\\left' + DELIM.get(it.text, it.text) + ' ')
        elif idx in rights:
            buf.append('\\right' + DELIM.get(it.text, it.text) + ' ')
        elif it.kind == 'g' and it.font.startswith('CMSY') and it.text in DELIM:
            buf.append(DELIM[it.text])
        elif idx in obars:
            buf.append('\\lvert ')
        else:
            buf.append(math_text(it))
    flush()
    s = ''.join(out)
    s = s.replace('^{\\circ }', '^\\circ ').replace("^{'}", "'").replace("^{''}", "''")
    s = re.sub(r'(\\cdot\s*){3}', r'\\cdots ', s)
    s = s.replace('...', r'\ldots ')
    return s


def line_tex(items):
    items = sorted(items, key=lambda it: (it.x0, it.base))
    parts = []
    i = 0
    prev = None   # (kind, last item)
    while i < len(items):
        it = items[i]
        if is_math_item(it):
            j = i
            run = []
            while j < len(items) and is_math_item(items[j]):
                run.append(items[j]); j += 1
            # a comma followed by no thin space ended a formula in the source
            # (the next formula starts right after it): split there
            msz = max(x.size for x in run)
            subs = [[]]
            for k, x in enumerate(run):
                subs[-1].append(x)
                if x.kind == 'g' and x.text in (',', ';') and x.size >= msz - 0.6 and k + 1 < len(run) \
                        and run[k + 1].size >= msz - 0.6 and run[k + 1].x0 - x.x1 < 0.6:
                    subs.append([])
            src = '\\relax'.join('$' + run_tex(sub).strip() + '$' for sub in subs if sub)
            if prev is not None:
                pk, pit = prev
                gap = run[0].x0 - pit.x1
                if pk == 'cjk':
                    if not vis.is_cjk(pit.text[-1:]) or pit.text[-1:] not in '、：；，。（）“”':
                        parts.append(' ')
                elif pk == 'text' and gap > 1.6:
                    parts.append(' ')
            parts.append(src)
            prev = ('math', run[-1])
            i = j
            continue
        t = it.text
        cjk = vis.is_cjk(t[:1])
        if prev is not None:
            pk, pit = prev
            gap = it.x0 - pit.x1
            if cjk and pk == 'math' and t[:1] not in '、：；，。（）“”':
                parts.append(' ')
            elif not cjk and pk in ('math', 'text') and gap > 1.6:
                parts.append(' ')
            elif not cjk and pk == 'cjk' and gap > 1.6:
                parts.append(' ')
            elif cjk and pk == 'text' and gap > 1.6:
                parts.append(' ')
        # the book's text ellipsis is \ldots (Latin font, no CJK glue after it)
        # curly quotes: Latin font, spaced only where the source has a space
        # (\textquotedblleft gets no automatic CJK glue, unlike the `` ligature)
        parts.append(t.replace('…', '\\ldots{}').replace('“', '\\textquotedblleft{}').replace('”', '\\textquotedblright{}')
                     .replace('‘', '\\textquoteleft{}').replace('’', '\\textquoteright{}'))
        prev = ('cjk' if cjk else 'text', it)
        i += 1
    return ''.join(parts)


def paragraph_tex(doc, pn, y_top, y_bot, x_first=None):
    """y in PyMuPDF coordinates (y down): region of the paragraph."""
    page = doc[pn - 1]
    glyphs, rules, draws = vis.visible_glyphs(page)
    def gbase(g):
        if g['font'] == 'CMEX10' or g['c'] == '√':
            return (g['y0'] + g['y1']) / 2 + 0.25 * g['size']
        return g['oy']
    glyphs = [g for g in glyphs if y_top <= gbase(g) <= y_bot]
    rules = [r for r in rules if y_top - 10 <= r['y'] <= y_bot + 10]
    items = vis.build_items(glyphs, rules)
    items = vis.merge_opnames(items)
    items = vis.collapse(items, rules)
    items = vis.fix_cong(items)
    items = vis.drop_orphan_slashes(items)
    lines = vis.lines_of(items)
    out = []
    for k, c in enumerate(lines):
        its = sorted(c['its'], key=lambda it: it.x0)
        if k == 0 and x_first is not None:
            its = [it for it in its if it.x0 >= x_first - 0.5]
        out.append(line_tex(its))
    out = [l.replace('%', r'\%') for l in out]
    # join lines: CJK-CJK no space; otherwise a space
    s = ''
    for k, l in enumerate(out):
        if k == 0:
            s = l
        else:
            a = s[-1:]; b = l[:1]
            s += ('' if (vis.is_cjk(a) and vis.is_cjk(b)) else ' ') + l
    return s
