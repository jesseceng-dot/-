"""Book 33 (人体简史): the reviser's 70 LaTeX pictures in the text (inline <svg> with a <title>), each transcribed from
its title and checked against the drawing: fractions a/b, powers of ten as raised digits (10¹⁵, 7×10²⁷; the titles
'8乘以10的25次方' and '2.5×10的22次方' are drawn 8×10²⁵, 2.5×10²²), temperatures with ℃, ranges with '～' as the
text is set here, the minus of −45℃; '1/250万' is drawn 1/2,500,000 and written so; variables of the BMI formula
italic; the IPA of 'clitoris' in the Latin face (the body font has no ə ɪ ˈ)."""
from .bk_img32 import _scripts

_FRAC = ['1/3', '1/4', '1/5', '1/6', '1/7', '1/8', '1/10', '1/16', '1/30', '1/32', '1/50', '1/51', '1/71', '1/200', '1/238',
         '1/250', '1/345', '1/385', '1/450', '1/909', '1/1000', '1/1667', '1/2000', '1/2002', '1/3000', '1/3333', '1/5000',
         '1/6000', '1/10000', '1/12,200', '2/3', '3/4']
_TEMP = ['0℃', '1℃', '2℃', '4℃', '28℃', '30℃', '38℃', '49℃', '54℃', '55℃', '92.2℃', '98.9℃']

IMG_TEXT = {**{f'svg:{x}': x for x in _FRAC + _TEMP + ['20/20', '120/80', '130/80', '140/90', '300/190', '1×3×5', 'α', 'β',
                                                        '38.9‰', 'Styrbæk']},
    'svg:999,999,999又1/2': '999,999,999½',
    'svg:1015': '10¹⁵',
    'svg:1030': '10³⁰',
    'svg:1048': '10⁴⁸',
    'svg:1063': '10⁶³',
    'svg:7×1027': '7×10²⁷',
    'svg:8乘以10的25次方': '8×10²⁵',
    'svg:2.5×10的22次方': '2.5×10²²',
    'svg:1/250万': '1/2,500,000',
    'svg:-45℃': '−45℃',
    'svg:36~38℃': '36～38℃',
    'svg:1℃~2℃': '1℃～2℃',
    'svg:\\mathrm{BMI}=\\frac{m}{h^{2}}': [('BMI=', ''), ('m', 'it'), ('/', ''), ('h', 'it'), ('²', '')],
    'svg:m': [('m', 'it')],
    'svg:h': [('h', 'it')],
    'svg:/ˈklɪtərɪs/': [('/ˈklɪtərɪs/', 'lat')],
}
IMG_TEXT = {k: _scripts(v) for k, v in IMG_TEXT.items()}
