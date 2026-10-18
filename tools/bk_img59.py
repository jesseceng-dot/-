"""Book 59 (魔鬼数学): the 20 formulas the ebook sets as pictures inside a line, each read off its drawing.  Variables
italic as drawn (m, n, k, q, Q, i, x, A, B, C), digits and operators upright; the minus of the formulas '−', the dash
before the negative root '–' as the drawing (and the text: “如果我们选择‘–’”) has it; the digit groups of the long
decimals (0.493 901 531 9) with thin spaces, the dash kept with its number.  The comma after the positive root belongs to the picture
(“就会得到⟨图⟩与我们……”); the speck at the right edge of 'n²=2k²' is cut-off, the text continues with '。'.
The radical sign in FreeSerif (.rad): the CJK faces set √ full width."""
from .bk_img32 import _scripts

N = '\u2009'                                   # (thin space: the digit groups of the drawing; a line may break there)
_IT = lambda t: (t, 'it')

IMG_TEXT = {
    'image00311.jpeg': '1/(4×10²⁴)',                     # (“82个1/2相乘的得数略小于⟨图⟩”: a fraction drawn stacked)
    'image00315.jpeg': [('2=', ''), _IT('m'), ('²/', ''), _IT('n'), ('²，即2', ''), _IT('n'), ('²=', ''), _IT('m'), ('²', '')],
    'image00324.jpeg': '3²+4²=5²',
    'image00327.jpeg': [_IT('q'), ('i', 'it msub'), ('+1', 'msub')],
    'image00331.jpeg': [_IT('Q'), ('i', 'it msub')],
    'image00354.jpeg': '12²+12²=288',
    'image00355.jpeg': [_IT('x'), (f' = 20 − 2√105，即–\u20600.493{N}901{N}531{N}9……', '')],
    'image00356.jpeg': '4+2√2',
    'image00359.jpeg': '√2',
    'image00363.jpeg': [('2', ''), _IT('n'), ('²=(2', ''), _IT('k'), (')²=4', ''), _IT('k'), ('²', '')],
    'image00370.jpeg': [_IT('Q'), ('i', 'it msub')],
    'image00376.jpeg': [_IT('Q'), ('i', 'it msub')],
    'image00398.jpeg': '1²+1²=1+1=2',
    'image00403.jpeg': [_IT('x'), ('³+2', ''), _IT('x'), ('²−11', ''), _IT('x'), ('=12', '')],
    'image00407.jpeg': [('√2 = ', ''), _IT('m'), ('/', ''), _IT('n')],
    'image00410.jpeg': '8(√2 − 1)',
    'image00411.jpeg': [_IT('n'), ('²=2', ''), _IT('k'), ('²', '')],
    'image00415.jpeg': [_IT('A'), ('n', 'it msup'), ('+', ''), _IT('B'), ('n', 'it msup'), ('=', ''), _IT('C'), ('n', 'it msup')],
    'image00418.jpeg': [_IT('q'), ('i', 'it msub')],
    'image00444.jpeg': [_IT('x'), (f' = 20 + 2√105，即40.493{N}901{N}531{N}9……，', '')],
}


def _rad(v):
    """The radical sign in FreeSerif's (.rad): the CJK faces set √ full width, a gap after it ('√ 2')."""
    pieces = [(v, '')] if isinstance(v, str) else v
    out = []
    for t, c in pieces:
        for k, part in enumerate(t.split('√')):
            if k:
                out.append(('√', (c + ' rad').strip()))
            if part:
                out.append((part, c))
    return out


IMG_TEXT = {k: _rad(_scripts(v)) for k, v in IMG_TEXT.items()}
