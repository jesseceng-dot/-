"""Book 39 (世界观): the formulas the ebook sets as pictures, each read off its drawing.  Variables italic (l, v, t, d, s,
x, y, z, θ, γ), the speed of light c upright as the drawings have it, Δ and sin upright; the digit groups of the drawings
(1 000, 180 000, 300 000) written as the text writes these numbers (180000千米/秒).
IMG_TEXT: the pictures inside a line; IMG_PARA: the display formulas (each a centred line, or four for the Lorentz
transformation); image00284 is the placeholder box of the inductive schema ('在我们过去的经验中，❑总是……发生')."""
from .bk_img32 import _scripts
from .model import run

_ROOT = [('√(1−(', ''), ('v', 'it'), ('/c)²)', '')]                      # √(1−(v/c)²)
_ROOT_SP = [('√(1 − (', ''), ('v', 'it'), ('/c)²)', '')]

IMG_TEXT = {
    'image00284.jpeg': [('❑', 'sym')],
    'image00339.jpeg': [('lv', 'it'), ('/c²', '')],
    'image00342.jpeg': [('lv', 'it'), ('/c²', '')],
    'image00285.jpeg': _ROOT,
    'image00291.jpeg': _ROOT,
    'image00345.jpeg': '1000/180000',
    'image00351.jpeg': '√(c²0²−\u200b1000²−\u200b0²−\u200b0²)',     # (may break after a minus: the line before it is not spread)
    'image00272.jpeg': '√2',
    'image00300.jpeg': '√2',
}
IMG_TEXT = {k: _scripts(v) for k, v in IMG_TEXT.items()}


def _line(v):
    s = _scripts(v)
    return [run(s)] if isinstance(s, str) else [run(t, c=c) for t, c in s]


IMG_PARA = {k: [_line(x) for x in v] for k, v in {
    'image00335.jpeg': [_ROOT_SP],
    'image00282.jpeg': [_ROOT_SP],
    'image00311.jpeg': [[('(', ''), ('lv', 'it'), ('/', '')] + _ROOT_SP + [(')/c²', '')]],
    'image00314.jpeg': [_ROOT_SP + [('/√(1 − sin²', ''), ('θ', 'it'), ('(', ''), ('v', 'it'), ('/c)²)', '')]],
    'image00320.jpeg': [[('t', 'it'), (' = ', ''), ('d', 'it'), ('/300000', '')]],
    'image00348.jpeg': [[('t', 'it'), (' = (', ''), ('d', 'it'), (' − 800)/180000', '')]],
    'image00323.jpeg': [[('s', 'it'), ('² = c²(Δ', ''), ('t', 'it'), (')² − (Δ', ''), ('x', 'it'), (')² − (Δ', ''), ('y', 'it'),
                         (')² − (Δ', ''), ('z', 'it'), (')²', '')]],
    'image00321.jpeg': [[('γ', 'it'), (' = 1/', '')] + _ROOT_SP],
    'image00349.jpeg': [[('t′', 'it'), (' = ', ''), ('γ', 'it'), ('(', ''), ('t', 'it'), (' − ', ''), ('vx', 'it'), ('/c²)', '')],
                        [('x′', 'it'), (' = ', ''), ('γ', 'it'), ('(', ''), ('x', 'it'), (' − ', ''), ('vt', 'it'), (')', '')],
                        [('y′', 'it'), (' = ', ''), ('y', 'it')],
                        [('z′', 'it'), (' = ', ''), ('z', 'it')]],
}.items()}
