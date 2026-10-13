SYS = r'\left\{\begin{array}{@{}>{\displaystyle}c@{}}%s\end{array}\right.'
SPECS = [
 # 4.7: the question is missing after the system (cf. 4.1); new line placed where TeX puts the
 # paragraph after a display on this page (calibrated on 4.5, same page: +2.26 over emulation)
 dict(page=83, id='4.7', kind='add', x=78.511, y=82.38,
      tex=r"(1) 有唯一一组解; (2) 无解; (3) 有无穷多组解？"),
 # 4.19: numerator of the third term of (2) missing; restore 5 centred over the existing bar
 dict(page=87, id='4.19', kind='glyph', glyphs=[('CMR10', '5', 296.998 + (6.235 - 5.4545) / 2, 476.235, 10.909)]),
 # 4.30: x + xu + y -> x + xy + y (whole display re-centred as TeX would)
 dict(page=90, id='4.30', kind='disp', region=(200, 60, 420, 112),
      tex_old=SYS % r'x+xu+y=2+3\sqrt{2},\\x^2+y^2=6.',
      tex_new=SYS % r'x+xy+y=2+3\sqrt{2},\\x^2+y^2=6.'),
 # 4.35: last equation denominator 1 + x^2 -> 1 + x_n^2
 dict(page=92, id='4.35', kind='disp', region=(200, 330, 420, 470),
      tex_old=SYS % r'\frac{2x_1^2}{1+x_1^2}=x_2,\\\frac{2x_2^2}{1+x_2^2}=x_3,\\\ldots\ldots\\\frac{2x_{n-1}^2}{1+x_{n-1}^2}=x_n,\\\frac{2x_n^2}{1+x^2}=x_1.',
      tex_new=SYS % r'\frac{2x_1^2}{1+x_1^2}=x_2,\\\frac{2x_2^2}{1+x_2^2}=x_3,\\\ldots\ldots\\\frac{2x_{n-1}^2}{1+x_{n-1}^2}=x_n,\\\frac{2x_n^2}{1+x_n^2}=x_1.'),
]
