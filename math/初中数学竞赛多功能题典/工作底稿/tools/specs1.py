SPECS = [
 dict(page=13, id='1.25fig', kind='remove', rect=(70, 665, 230, 685.5)),
 dict(page=15, id='1.33fig', kind='remove', rect=(70, 688, 270, 716)),
 dict(page=15, id='1.36', y=208.19, top=216, bot=200, tex=r"已知 $y=|2x+6|+|x-1|-4|x+1|,$ 求 $y$ 的最大值."),   # ordinary bars: unambiguous spacing
 dict(page=16, id='1.41', y=82.29, top=92, bot=55,   # ordinary bars as in the existing (re-set) first line
      tex=r"设 $n$ 个有理数 $x_{1},x_{2},\ldots ,x_{n}$ 满足 $|x_{i}|<1\left( i=1,2,\cdots ,n\right) ,$ 且 $|x_{1}|+|x_{2}|+\cdots +|x_{n}|$\linebreak $=19+|x_{1}+x_{2}+\cdots +x_{n}|$,"),
 dict(page=36, id='2.60', y=424.79, top=440, bot=410, edits=[('2x - 3xy + 2x', '2x - 3xy + 2y')]),
 dict(page=37, id='2.63', y=754.89, top=770, bot=740, edits=[(r'\dfrac{b}{bc + b + c}', r'\dfrac{b}{bc + b + 1}')]),
 dict(page=37, id='2.64', y=589.39, top=605, bot=575, edits=[('x^2 - 7x + 12', 'x^2 + 7x + 12')]),
]
