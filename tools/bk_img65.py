"""Books 65–74 (诺贝尔经济学奖获得者丛书·大师经典): the formulas the ebook sets as pictures inside a line (空间经济学 and
金融、研究、教育与增长), each read off its drawing.  Variables upright, as the ebook's own text sets them (“L^A”, “λ_r”,
“μ”), so that a line does not mix the two; the minus '−' and ∑ ∫ ≡ ⋛ in the Latin math face (math_ops).  Written with
^{…} and _{…}, nested: a script of a script is smaller (msup2: the M of “e^{−(σ−1)τ^M r̃}”).  Fractions in a line a/b;
a sum's or an integral's limits beside it (∑_{s=1}^{R}, ∫_{−f}^{0}); bars, tildes and dots as combining marks (R̄ h̃ θ̇).
A fraction whose terms are products keeps its factors together: E_1T^{1−σ}/(E_1+E_2) for the picture's stacked
E_1/(E_1+E_2) T^{1−σ}.
The speck at the right edge of image02486 is the cut-off comma of the original, the note goes on with '。'."""
import re

FORMULAS = {
    'image01982.jpeg': 'φ',                              # (记为⟨φ⟩_r, the text's own subscript after it)
    'image01990.jpeg': 'e^{rN}',
    'image02046.jpeg': 'd_{ni}x_{ni}(j)/z_{i}(j)=w_{n}L_{n}/w_{i}',
    'image02055.jpeg': 'R̄^{2}',
    'image02072.jpeg': 'μ<ge^{−θ}',
    'image02104.jpeg': 'h̃',
    'image02110.jpeg': '<e^{−(σ−1)τ^{M}r̃}∫_{−f}^{0}e^{−τ^{A}|s|}ds+e^{(σ−1)τ^{M}r̃}∫_{0}^{f}e^{−τ^{A}|s|}ds',
    'image02152.jpeg': 'θ̇',                         # (该式应为⟨θ̇⟩_2=…, the text's subscript after it)
    'image02190.jpeg': '（λ̇_{1}，λ̇_{2}，λ̇_{3}）',     # (as the text writes the point just before: （λ1，λ2，λ3）)
    'image02237.jpeg': 'μ^{1/θ}L',
    'image02243.jpeg': 'h^{β}',
    'image02267.jpeg': 'λ̇_{2}=2(L_{1}L̇_{2}−L_{2}L̇_{1})/(L_{1}+2L_{2})^{2}',
    'image02273.jpeg': 'ā',
    'image02285.jpeg': 'Ω̄',
    'image02318.jpeg': '⋛',                              # (> above one bar above <: ω1⋛ω2 … ω1⋛ω)
    'image02329.jpeg': 'μ_{i}^{1/θ}',
    'image02335.jpeg': 'A^{φ}',
    'image02439.jpeg': 'μ_{i}c_{ni}^{−θ}/μ̃_{n}',
    'image02461.jpeg': '[∑_{r}n_{r}x̃_{rs}^{ρ}]^{α/ρ}',
    'image02486.jpeg': 'G_{r}^{i}=[∑_{s=1}^{R}n_{s}^{i}(p_{s}^{i}T_{s,r})^{(1−σ)}]^{1/(1−σ)}',
    'image02534.jpeg': 'R_{j}>R_{j−1}',
    'image02539.jpeg': 'σ=2, α=1/8, γ=5/8，则(w^{2}/w^{1})^{β}=',   # (the text goes on: √61>1)
    'image02585.jpeg': 'ε_{i}^{η}Λ/z_{i}(t)',
    'image02628.jpeg': 'R_{j}(1−α)^{j−1}',
    'image02665.jpeg': '(w^{2}/w^{1})^{β}>1',
    'image02668.jpeg': 's_{K}',
    'image02683.jpeg': 'μ^{1/θ}L',
    'image02697.jpeg': 'Ȳ',
    'image02706.jpeg': 'μ_{s}',
    'image02739.jpeg': 'XLIV',                           # (根据霍依特书中的表⟨XLIV⟩计算: a Roman numeral)
    'image02780.jpeg': 'λ̃',                         # (λ^1=⟨λ̃⟩^2: the text's superscript after it)
    'image02811.jpeg': 'E≡w_{2}^{−σ}(L_{1}^{−1}p^{A})(B_{1}+B_{2})<w_{2}^{−σ}(L_{1}^{−1}p^{A})CΛ',
    'image02671.jpeg': '[∫_{0}^{n}m(i)^{ρ}di]^{1/ρ}=M',  # (约束条件：…。 the '=M' the ebook sets before it as well: bk_fixes)
    'image02449.jpeg': 'dw^{M}[σ−Zμ/b]+(1−σ)Z dG^{M}/G^{M}=(2Zμ/b)dλ',   # (the translator's note: 该式应为…)
    'image02086.jpeg': 'dv_{1}/dλ_{1}=dw_{1}/dλ_{1}+A″(1−λ_{1})=0',
    'image02472.jpeg': 'A′(1)≥A′(1−λ_{1})[(E_{1}T^{1−σ}/(E_{1}+E_{2})+E_{2}T^{σ−1}/(E_{1}+E_{2}))T^{−ασ}]^{1/[(1−α)σ]}',
    'image02302.jpeg': 'E^{2}=E^{1}=(1/2+γ/β)',
}

_CLS = {(): '', ('^',): 'msup', ('_',): 'msub', ('^', '^'): 'msup2', ('^', '_'): 'msupsub', ('_', '_'): 'msub2',
        ('_', '^'): 'msubsup'}


def runs(src):
    """'e^{−(σ−1)τ^{M}r̃}' -> [('e', ''), ('−(σ−1)τ', 'msup'), ('M', 'msup2'), ('r̃', 'msup')]: the pieces of a formula, each with
    the class of its script level."""
    out, stack, buf, i = [], [], '', 0
    while i < len(src):
        if src[i] in '^_' and src[i + 1:i + 2] == '{':
            if buf:
                out.append((buf, _CLS[tuple(stack)]))
            buf = ''
            stack.append(src[i])
            i += 2
            continue
        if src[i] == '}' and stack:
            if buf:
                out.append((buf, _CLS[tuple(stack)]))
            buf = ''
            stack.pop()
            i += 1
            continue
        buf += src[i]
        i += 1
    if buf:
        out.append((buf, _CLS[tuple(stack)]))
    merged = []
    for t, c in out:
        if merged and merged[-1][1] == c:
            merged[-1] = (merged[-1][0] + t, c)
        else:
            merged.append((t, c))
    return merged if any(c for _, c in merged) else merged[0][0]


IMG_TEXT = {k: runs(v) for k, v in FORMULAS.items()}
assert all(re.fullmatch(r'image\d{5}\.jpeg', k) for k in IMG_TEXT)
