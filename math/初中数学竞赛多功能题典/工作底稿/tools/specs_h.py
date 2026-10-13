F19105 = r"设 $m$ 为正整数. 如果存在某个正整数 $n$ 使得 $m$ 可以表示为 $n$ 和 $n$ 的正约数个数 (包括 1 和自身) 的商, 则称 $m$ 是\textquotedblleft{}好数\textquotedblright{}. 求证: (1) $1,2,\cdots ,17$ 都是\textquotedblleft{}好数\textquotedblright{}; (2) 18 不是\textquotedblleft{}好数\textquotedblright{}."
TN = 'TeXGyreTermes-Regular'
SPECS = [
 dict(page=362, id='19.43', y=375.89, top=385, bot=312, edits=[('10 周.9 次越过', '10 周, 9 次越过')]),
 dict(page=364, id='19.52', y=205.69, top=215, bot=197, xtol=0.3, edits=[]),
 # 19.54: "rey" -- the expression is the expansion of the 3x3 determinant (r s t; u v w; x y z)
 dict(page=365, id='19.54', x=78.51, y=562.29, top=571, bot=553, single=True, edits=[('rey', 'rwy')]),
 dict(page=365, id='19.54b', x=78.51, y=543.99, top=553, bot=535, xtol=0.3, edits=[]),
 # 19.55: "这个乘积的和" -- the 2n products (column and row products)
 dict(page=365, id='19.55', y=347.39, top=356, bot=320, edits=[('( $n$ 为奇数)', '($n$ 为奇数)'), ('求证：这个乘积的和', '求证：这 $2n$ 个乘积的和')]),
 dict(page=366, id='19.60', y=123.79, top=133, bot=78, xtol=0.3, edits=[]),
 dict(page=367, id='19.63', y=365.69, top=375, bot=338, xtol=0.3, edits=[]),
 # 19.71: duplicated phrase "它的所有顶点"; |A_{n+1}A_n| for |A_{n-1}A_n|; first line ran 14pt into the margin
 dict(page=369, id='19.71', y=329.09, top=338, bot=302,
      tex=r"设有一条平面闭折线 $A_{1}A_{2}\cdots A_{n}A_{1},$ 它的所有顶点 $A_{i}\left( i=1,2,\cdots ,n\right)$ 都是格点, 且 $|A_{1}A_{2}|=|A_{2}A_{3}|=\cdots =|A_{n-1}A_{n}|=\left| A_{n}A_{1}\right| .$ 求证：$n$ 是偶数."),
 dict(page=369, id='19.72', y=98.09, top=107, bot=89, xtol=0.3, edits=[]),
 dict(page=370, id='19.77', y=118.79, top=128, bot=92, edits=[('证明为质数.', '证明 $n$ 为质数.')]),
 dict(page=373, id='19.88', y=598.89, top=608, bot=590, xtol=0.3, edits=[]),
 # 19.88: left side xyz (the conditions are symmetric in x, y, z)
 dict(page=373, id='19.88b', x=78.51, y=580.59, top=590, bot=572, single=True, edits=[('$yz=', '$xyz=')]),
 dict(page=374, id='19.94', y=438.89, top=448, bot=412, edits=[(r'<a_{10}$ 中. 将', r'<a_{10}.$ 将')]),
 dict(page=374, id='19.95', y=260.59, top=270, bot=252, xtol=0.3, edits=[]),
 # 19.97: closing quote and period of the definition missing
 dict(page=375, id='19.97', y=758.89, top=768, bot=713, edits=[(r"\textquotedblleft{}绝对质数例如： $2,", r"\textquotedblleft{}绝对质数\textquotedblright{}. 例如：$2,")]),
 dict(page=376, id='19.102', y=598.89, top=608, bot=590, xtol=0.3, edits=[]),
 dict(page=376, id='19.103', y=420.59, top=430, bot=393, edits=[('大于 1，且', '大于 1, 且'), ('正整数中. 必有', '正整数中, 必有')]),
 # 19.105: patch line without word spaces; the two sub-questions run together (continued on p377)
 dict(page=376, id='19.105', y=82.29, top=94, bot=73, max_lines=1, tex=F19105),
 dict(page=377, id='19.105b', x=56.693, y=758.89, top=768, bot=750, para_x=153.854, skip_lines=1, tex=F19105),
 # page number "371" was redrawn by a patch over glyphs without a text mapping
 dict(page=376, id='pageno', kind='remove', rect=(285, 30, 555, 50)),
 dict(page=376, id='pageno2', kind='glyph', color=(0.235, 0.443, 0.718), order=100,
      glyphs=[(TN, '3', 290.166, 37.984, 9.9626), (TN, '7', 295.1473, 37.984, 9.9626), (TN, '1', 300.1286, 37.984, 9.9626)]),
 dict(page=378, id='19.110', y=598.89, top=608, bot=590, edits=[('$x$：$y$', '$x$、$y$')]),
 # 19.112: number alone on its line; stars and text joined to it
 dict(page=378, id='19.112', x=105.522 + 5.455 + 2.727, y=278.89, top=288, bot=252,
      tex=r"$\bigstar$ $\bigstar$ 证明一列数：$49,4489,444889,44448889,\ldots$ 中的每个数都是完全平方数."),
 dict(page=379, id='19.115', y=598.89, top=608, bot=572, edits=[(r"称为 \textquotedblleft{}美妙数\textquotedblright{} 问所有", r"称为 \textquotedblleft{}美妙数\textquotedblright{}. 问所有")]),
 # 19.118: exponent n set in a non-embedded sans-serif font
 dict(page=379, id='19.118', y=82.29, top=93, bot=73, tex=r"设 $n$ 是正整数, 且使得 $2^{4}+2^{7}+2^{n}$ 是完全平方数, 求 $n$ 的值."),
 # 19.124: the digit-count marks were broken (small digits over "n1"); underbraces as in 19.14, 19.20
 dict(page=381, id='19.124', y=758.89, top=768, bot=740,
      tex=r"证明 $\underbrace{11\cdots 1}_{n\text{个}1},\underbrace{22\cdots 2}_{n\text{个}2},\ldots ,\underbrace{99\cdots 9}_{n\text{个}9}$ 都不是完全平方数 ($n$ 是大于 1 的整数)."),
 dict(page=381, id='19.125', y=598.89, top=608, bot=590, xtol=0.3, edits=[]),
 dict(page=381, id='19.128', y=100.59, top=110, bot=92, xtol=0.3, edits=[]),
 # 19.130: stray x in 8xc (the original problem has (2a-1)^2 + 8c)
 dict(page=382, id='19.130', y=598.89, top=608, bot=572,
      tex=r"已知正整数 $c$ 是一个奇合数. 证明：存在正整数 $a\le \dfrac{c}{3}-1,$ 使得 $\left( 2a-1\right) ^{2}+8c$ 是一个完全平方数."),
 dict(page=382, id='19.131', y=420.59, top=430, bot=393, xtol=0.3, edits=[]),
 dict(page=382, id='19.132', y=242.29, top=251, bot=233, xtol=0.3, edits=[]),
 dict(page=383, id='19.133', y=758.89, top=768, bot=750, xtol=0.3, edits=[]),
 dict(page=383, id='19.134', y=580.59, top=590, bot=572, xtol=0.3, edits=[]),
 dict(page=383, id='19.136', y=260.59, top=270, bot=233, edits=[('—个正整数', '一个正整数')]),
 dict(page=384, id='19.138', y=580.59, top=590, bot=553, xtol=0.3,
      edits=[('在二个连续', '在两个连续'), ('能不能有二个完全', '能不能有两个完全'), ('$ ？', '$？')]),
 dict(page=385, id='19.139(1)', x=78.51, y=722.39, top=731, bot=713, xtol=0.3, edits=[]),
 dict(page=385, id='19.139(2)', x=78.51, y=704.09, top=713, bot=695, xtol=0.3, edits=[]),
 # 20.8: 4^n + 1 (with 4n + 1 the statement fails for n = 5)
 dict(page=387, id='20.8', y=278.89, top=288, bot=270, edits=[(r'\left( 4n+1\right)', r'\left( 4^{n}+1\right)')]),
 # 20.13: Fermat numbers F_n = 2^(2^n) + 1 (exponent letter k)
 dict(page=388, id='20.13', y=260.59, top=276, bot=252,
      tex=r"形如 $F_{n}=2^{2^{n}}+1,n=0,1,2,\ldots$ 的数称为费马数. 证明：当 $n\ge 2$ 时,$F_{n}$ 的末位数字是 7."),
 # 20.18: second power tower printed at script size with a bare "k7" under it
 dict(page=389, id='20.18', y=260.59, top=276, bot=240,
      tex=r"求 $7^{7^{7}}$ 的末位数字和 $\underbrace{7^{7^{\cdot^{\cdot^{7}}}}}_{k\text{个}7}$ 的末两位数字, 其中 $k$ 是大于 1 的正整数."),
 dict(page=392, id='20.31', y=598.89, top=608, bot=590, edits=[('+4^{241},$ 能被', '+4^{241}$ 能被')]),
 dict(page=394, id='20.42', y=393.89, top=403, bot=385, edits=[('$3^{x}+4^{y}=5^{z}$ (1) 的', '$3^{x}+4^{y}=5^{z}$ 的')]),
]
