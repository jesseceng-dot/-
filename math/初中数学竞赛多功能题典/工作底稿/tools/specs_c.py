SPECS = [
 dict(page=107, id='5.26', x=78.511, y=205.69, top=214, bot=200, edits=[('bc+c', 'bx+c'), (r'\lvert ', '|', 'all')]),
 # 5.47(4): the formula after 则 was wiped by an old patch (only the big parentheses and two
 # fraction bars of (1/a + 1/b) remain under the white box): restore the classical inequality
 dict(page=113, id='5.47(4)', x=78.511, y=690.65, top=705, bot=676,
      tex=r"(4) 设 $a$、$b$ 是正实数, 则 $\left( \frac{1}{a}+\frac{1}{b}\right) (a+b)\ge 4;$"),
 # 5.51(3): second fraction lost numerator and bar, 4/5 shrunk: restore as in (1)(2)
 dict(page=114, id='5.51(3)', x=78.511, y=649.19, top=662, bot=630, single=True,
      tex=r"$\frac{1}{x+2}+\frac{1}{y+2}\ge \frac{4}{5}.$"),
 # mis-split paragraphs (5.67-5.72, 5.78): merged; units upright
 dict(page=118, id='5.67', y=758.89, top=768, bot=680, edits=[]),
 dict(page=118, id='5.68', y=470.89, top=480, bot=374,
      edits=[('$60$ km$/h,$', '$60$ km/h,'), ('5 km$/h.$', '5 km/h.')]),
 dict(page=118, id='5.69', y=219.39, top=228, bot=140, edits=[]),
 dict(page=119, id='5.70', y=758.89, top=768, bot=680,
      edits=[('从早 $700$ 开始', '从早 $7{:}00$ 开始'), ('早上 $830$ 由', '早上 $8{:}30$ 由')]),
 dict(page=119, id='5.71', y=448.79, top=458, bot=388, edits=[]),
 dict(page=119, id='5.72', y=233.89, top=243, bot=190, edits=[('$400m$', '$400$ m')]),
 dict(page=120, id='5.73', y=562.29, top=571, bot=535, edits=[]),
 dict(page=120, id='5.75', y=205.69, top=215, bot=140, edits=[(r'$1,$\relax$2,$ $3,$\ldots{}', r'$1,$\allowbreak$2,$\allowbreak$3,$\ldots{}. ')]),   # sentence boundary after the ellipsis
 dict(page=121, id='5.78', y=402.29, top=411, bot=340, edits=[]),
 dict(page=121, id='5.79', x=78.511, y=91.99, top=100, bot=85, edits=[('方案,', '方案.')]),

 dict(page=123, id='6.3', y=347.09, top=356, bot=340, edits=[('若 $f(5)=7$ 求', '若 $f(5)=7,$ 求')]),
 # 6.14: 散 in the wrong (bold) font, 当0 spacing; (1) starts its own indented line like (2)
 dict(page=127, id='6.14', y=758.89, top=768, bot=680,
      edits=[('开始分散.', r'开始分{\CJKfamily{arpl}散}.'),   # 散 is missing from the book's STSong subset
             (r'图像是线段.(1) 当 $0\le x$ $\le 10$ 时', r'图像是线段.\hspace{3.55pt}\mbox{}\par\hspace*{21.818bp}(1) 当 $0\le x\le 10$ 时')]),
 dict(page=130, id='6.25', y=347.39, top=356, bot=323, edits=[('(15,6) 直线', '(15,6), 直线')]),
 dict(page=135, id='6.39', y=578.69, top=588, bot=555,
      edits=[(r'、 $\triangle BC$', r'、$\triangle BCD$')]),
 dict(page=137, id='6.48', y=365.69, top=374, bot=340, edits=[]),
 # 6.51 remark: stray gap in 关系 是, missing final stop
 dict(page=138, id='6.51r', x=116.693, y=379.99, top=388, bot=375, edits=[('关系是一种行之有效的方法', '关系是一种行之有效的方法.')]),
 dict(page=138, id='6.52', y=361.69, top=377, bot=338,
      tex=r"设函数 $f(x)=x^{2}+x+\frac{1}{2}\left( n\le x\le n+1\right) ,$ 这里 $n$ 是正整数, 则在 $f(x)$ 的值域中有多少个整数？"),
 # 6.53: label alone on its line; stars and text joined to it
 dict(page=138, id='6.53', x=94.613 + 5.455 + 2.727, y=183.39, top=192, bot=140,
      tex=r"$\bigstar$ $\bigstar$ $\bigstar$ 设 $m$、$n$ 为正整数, 且 $m\not =2,$ 如果对一切实数 $t,$ 二次函数 $y=x^{2}+(3-mt)x-3mt$ 的图象与 $x$ 轴的两个交点间的距离不小于 $|2t+n|,$ 求 $m$、$n$ 的值."),
 dict(page=139, id='6.55', x=56.693, y=517.69, top=526, bot=510, edits=[('的值,', '的值.')]),
 dict(page=141, id='6.62', y=755.49, top=765, bot=748,
      tex=r"\looseness=-1 已知点 $M$、$N$ 的坐标分别为 $M(0,1)$、$N(0,-1)$, 点 $P$ 是抛物线 $y=\frac{1}{4}x^{2}$ 上一个动点."),   # one line, as before
 dict(page=142, id='6.66', y=577.19, top=586, bot=552, edits=[('则对任何整数 $x$、$y$ 的值', '则对任何整数 $x,$ $y$ 的值')]),

 # units: upright and separated from the number (GB 3102)
 dict(page=126, id='6.13', y=383.99, top=393, bot=360,
      edits=[('$x(h)$', r'$x(\text{h})$'), ('$2000h,$ 照明', '$2000$ h, 照明')]),
 dict(page=126, id='6.13(3)', x=78.511, y=133.09, top=142, bot=125, edits=[('$1500h,$ 他', '$1500$ h, 他')]),
 # 6.74: stray blank glyph after the number; stars back in place
 dict(page=144, id='6.74', x=94.613 + 5.455 + 2.727, y=438.89, top=452, bot=430,
      tex=r"$\bigstar$ $\bigstar$ 已知 $0<k<1,$ 试确定关于 $x$ 的方程 $\left| 1-x^{2}\right| =kx+k$ 的解的个数."),
 # 6.79: second line lost the braces of max{...} and half of |x^2 - 5|
 dict(page=145, id='6.79', y=269.49, top=278, bot=245,
      edits=[(r'$f(x)=\max \left| x+1\right| ,x^{2}-5$ 的最小值', r'$f(x)=\max \left\{ \left| x+1\right| ,\left| x^{2}-5\right| \right\}$ 的最小值'),
             (r' $||$', '')]),
 dict(page=147, id='6.87', x=78.511, y=339.39, top=348, bot=333, edits=[('的最小值,', '的最小值.')]),
 dict(page=147, id='6.88', y=179.29, top=188, bot=172, edits=[]),
 dict(page=148, id='6.91', y=420.59, top=430, bot=396, edits=[('-2(a^{2}-1)x+1$ 其中', '-2(a^{2}-1)x+1,$ 其中')]),
 dict(page=148, id='6.92', y=242.29, top=251, bot=218, edits=[('且 $g($ $p)=25;$', '且 $g(p)=25;$')]),
 # 6.96: label alone on its line
 dict(page=149, id='6.96', x=94.613 + 5.455 + 2.727, y=186.29, top=196, bot=150,
      tex=r"$\bigstar$ $\bigstar$ 求函数 $y=\frac{x^{2}-2x-3}{2x^{2}+2x+1}$ 的最值."),
 dict(page=153, id='6.114', y=276.49, top=285, bot=252, edits=[(r'$AF=2,$\relax$BF=1.$', r'$AF=2,$\allowbreak$BF=1.$')]),
 dict(page=154, id='6.117', y=383.99, top=393, bot=323,
      edits=[('(单位：$h$)', '(单位：h)'), ('每行驶 $1km$ 需要', '每行驶 $1$ km 需要')]),
 # 6.123: first line ran 30pt into the margin (no break points between the formulas)
 dict(page=156, id='6.123', x=98.250 + 5.455 + 2.727, y=562.29, top=571, bot=535,
      tex=r"$\bigstar$ $\bigstar$ $\bigstar$ 整数 $x_{0},x_{1},x_{2},\ldots ,x_{2002},x_{2003}$ 满足条件：$x_{0}=0,$\allowbreak$|x_{1}|=\left| x_{0}+1\right| ,$\allowbreak$|x_{2}|=\left| x_{1}+1\right| ,$\allowbreak\ldots{},\allowbreak$|x_{2003}|=\left| x_{2002}+1\right| ,$ 求 $|x_{1}+x_{2}+\cdots +x_{2002}+x_{2003}|$ 的最小值."),
 dict(page=156, id='6.125', x=78.511, y=110.59, top=118, bot=104, edits=[(r'\ge 2,$', r'\ge 2;$')]),
 dict(page=159, id='7.2(5)', x=78.511, y=357.39, top=372, bot=345, edits=[(r'若 $\tan \alpha =3$ 求', r'若 $\tan \alpha =3,$ 求')]),
]
