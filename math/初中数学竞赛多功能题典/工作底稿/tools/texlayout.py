"""Typeset replacement text with XeLaTeX using the book's fonts and metrics,
and read back glyph placements and rules."""
import os, subprocess, hashlib, json, sys
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf
import pdfedit

TEXDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tex')
LM = 56.693          # left margin (bp)
TW = 481.89          # text width (bp)

PREAMBLE = r"""
\documentclass[11pt]{article}
\usepackage[paperwidth=595.28bp,paperheight=841.89bp,left=56.693bp,textwidth=481.89bp,top=72bp,textheight=650bp]{geometry}
\usepackage{amsmath,amssymb}
\usepackage[no-math]{fontspec}
\setmainfont{texgyretermes}[Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic]
\usepackage{xeCJK}
\setCJKmainfont{STSongBook.ttf}[Path=./fonts/]
\setCJKfamilyfont{hei}{STHeitiBook.ttf}[Path=./fonts/]
% Song-style fallback for characters missing from the book's STSong subset
\setCJKfamilyfont{arpl}{AR PL SungtiL GB}
% ctex default linestretch=\ccwd: stretch = (linewidth - ccwd - n ccwd)/n, n = floor((linewidth-2ccwd)/ccwd)
\xeCJKsetup{CJKglue={\hskip 0pt plus 0.30588pt}}
% as in the book: ellipsis and curly quotes are set in the Latin font
\xeCJKDeclareCharClass{Default}{"2026, "2018, "2019, "201C, "201D}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\pagestyle{empty}
\linespread{1.35}\selectfont
\everymath{\displaystyle}
\providecommand{\ov}[1]{\overline{#1}}\providecommand{\un}[1]{\underline{#1}}
% the book's \angle is the LaTeX kernel construction (scriptstyle slash + .34pt rule), not amssymb's glyph
\makeatletter\DeclareRobustCommand{\angle}{{\vbox{\ialign{$\m@th\scriptstyle##$\crcr\not\mathrel{\mkern14mu}\crcr\noalign{\nointerlineskip}\mkern2.5mu\leaders\hrule\@height.34\p@\hfill\mkern2.5mu\crcr}}}}\makeatother
% the book's parallelogram sign is a 7 x 4.5 bp outline drawn 1.5 bp above the baseline
\newcommand{\pgram}{\rule[1.5bp]{7bp}{4.5bp}\hspace{1.24bp}}
\frenchspacing
\emergencystretch=1.5em
%EXTRA%
\begin{document}
"""


def run(body, extra='', name=None):
    src = PREAMBLE.replace('%EXTRA%', extra) + body + '\n\\end{document}\n'
    h = hashlib.md5(src.encode('utf8')).hexdigest()[:12]
    name = name or ('t' + h)
    texf = os.path.join(TEXDIR, name + '.tex')
    pdff = os.path.join(TEXDIR, name + '.pdf')
    if not os.path.exists(pdff) or open(texf, encoding='utf8').read() != src:
        open(texf, 'w', encoding='utf8').write(src)
        r = subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error', name + '.tex'],
                           cwd=TEXDIR, capture_output=True, text=True)
        if r.returncode != 0:
            log = open(os.path.join(TEXDIR, name + '.log'), encoding='utf8', errors='replace').read()
            raise RuntimeError('xelatex failed:\n' + log[-3000:])
    return pdff


_OPEN = []     # keep layout documents open: their font objects may be copied into the book


def read_layout(pdff, page=0):
    pdf = pikepdf.open(pdff)
    _OPEN.append(pdf)
    pg = pdf.pages[page]
    ops, glyphs, items = pdfedit.interpret(pdf, pg)
    out = []
    for g in glyphs:
        d = dict(font=g.font.name, cid=g.font.cid, code=g.code, uni=g.uni, x=g.x, y=g.y,
                 size=g.size, adv=g.adv, color=g.color, fobj=g.fobj, src=pdff)
        if g.font.name.startswith('CMEX') or (g.font.name.startswith('CMSY') and g.code == 112):
            b = g.font.bounds.get(g.code)
            if b:
                d['vy'] = g.y + (b[1] + b[3]) / 2 * g.size
        out.append(d)
    rules = []
    for it in items:
        if it.kind == 'path':
            rules.append(dict(bbox=it.bbox, paint=it.paint, color=it.color, lw=it.lw, ops=[(str(o), [float(v) for v in a]) for a, o in ops[it.op0:it.op1 + 1]]))
    return out, rules


def lines_of(glyphs, tol=4.0):
    """Group glyphs into lines by baseline clusters of main-size glyphs."""
    base = sorted({round(g['y'], 2) for g in glyphs if g['size'] > 10})
    rows = []
    for y in sorted(base, reverse=True):
        if not rows or rows[-1] - y > tol:
            rows.append(y)
    res = {y: [] for y in rows}
    for g in glyphs:
        y = min(rows, key=lambda r: abs(r - g['y']))
        res[y].append(g)
    return [(y, sorted(res[y], key=lambda g: g['x'])) for y in rows]
