F2313 = r"$\bigstar$ $\bigstar$ $\bigstar$ 将 $1,2,3,4,5$ 这五个数字排成一排, 最后一个数是奇数, 且使得其中任意连续三个数之和都能被这三个数中的第一个数整除, 问：满足要求的排法有多少种？"
XL = 100.068 + 5.455 + 2.727      # after a label number "23.1x"
SPECS = [
 # 21.12: second "10" squeezed by a patch (digits overlapping)
 dict(page=397, id='21.12', y=420.59, top=430, bot=375, edits=[]),
 # 21.14: equation tag "(1)" left over from the solution; "(p,q)=1" in the text font
 dict(page=398, id='21.14', x=78.51, y=705.09, top=714, bot=696, single=True, edits=[('$(1)', '$')]),
 dict(page=398, id='21.14b', x=78.51, y=686.79, top=696, bot=678, single=True,
      tex=r"其中 $p$、$q$ 为正整数,$(p,q)=1,$\relax$p>q,$\relax$p$、$q$ 一奇一偶."),
 dict(page=405, id='21.43', y=598.89, top=608, bot=590, edits=[('求方程 $3^{s}-5^{t}=4$', '(1) 求方程 $3^{s}-5^{t}=4$')]),
 dict(page=407, id='21.50', x=78.51, y=722.39, top=731, bot=713, single=True, edits=[('(2) 设是 $k', '(2) 设 $k')]),
 dict(page=407, id='21.52', x=78.51, y=347.39, top=356, bot=320, edits=[('不定方程组 $mn', '不定方程 $mn')]),
 dict(page=409, id='22.8', y=211.69, top=221, bot=203, edits=[('$2003<T<2004,$', '$2003<x<2004,$')]),
 # 22.14: right side 99/[x] (with 9/[x] the equation has no tractable solution set)
 dict(page=411, id='22.14', y=524.89, top=534, bot=516, edits=[(r'\dfrac{9}{[x]}', r'\dfrac{99}{[x]}')]),
 dict(page=411, id='22.16', y=182.59, top=192, bot=174, edits=[]),
 # 22.17: the statement to be proved is missing (restored; see the log)
 dict(page=412, id='22.17', kind='add', x=78.51, y=740.59, tex=r"$\left[ \sqrt{n}+\sqrt{n+1}\right] =\left[ \sqrt{4n+2}\right] .$", order=0),
 dict(page=412, id='22.17shift', kind='shift', y_from=745, delta=-18.30, order=-1),
 dict(page=412, id='22.20', y=258.59, top=268, bot=213, order=-2, edits=[(r'其中 $n=$1,2,3,\ldots{}.', r'其中 $n=1,2,3,\ldots .$')]),
 # 23.11, 23.13, 23.14: label number alone on its line
 dict(page=417, id='23.11', x=XL, y=438.89, top=448, bot=412,
      tex=r"$\bigstar$ $\bigstar$ $\bigstar$ 在 20000 与 70000 之间, 有多少个数字不重复的偶数？"),
 dict(page=417, id='23.13stars', kind='remove', rect=(75, 78, 116, 92), gpred=lambda g: g.font.name.startswith('MSAM'), kinds=(), order=-1),
 dict(page=417, id='23.13lab', kind='move', rect=(30, 95, 110, 108), kinds=(), dy=-18.292, order=0),
 dict(page=417, id='23.13', x=XL, y=82.29, top=91, bot=73, max_lines=1, tex=F2313, order=1),
 dict(page=418, id='23.13b', x=56.693, y=758.89, top=768, bot=750, para_x=XL, skip_lines=1, tex=F2313),
 dict(page=418, id='23.14', x=XL, y=598.89, top=608, bot=553,
      tex=r"$\bigstar$ $\bigstar$ $\bigstar$ 由 35 个单位小正方形组成的长方形中, 如图所示, 有两个 \textquotedblleft{}*\textquotedblright{}, 问包含两个 \textquotedblleft{}*\textquotedblright{} 在内的小正方形组成的长方形 (含正方形) 共有多少个？"),
 dict(page=419, id='23.19', y=314.49, top=323, bot=287, edits=[('$B$). 它们共有', '$B$), 它们共有')]),
 # 23.35: general position of lines is "no three concurrent"; first line of 23.34(1) ran 22pt into the margin
 dict(page=424, id='23.34', x=78.51, y=740.69, top=750, bot=713, pre=r'\xeCJKsetup{CJKglue={\hskip 0pt plus 2pt}}\emergencystretch=6em ', edits=[]),
 dict(page=424, id='23.35', y=424.09, top=433, bot=397, edits=[('任三条不共线', '任三条不共点')]),
 dict(page=427, id='24.9', y=758.89, top=768, bot=735,
      tex=r"在 $1,11,111,\ldots ,\underbrace{11\ldots 1}_{n\text{ 个}1},\ldots$ 中, 是否有 2007 的倍数？"),
 dict(page=431, id='24.27', y=324.89, top=334, bot=298, edits=[('有连续的一天恰好', '有连续的 $n$ 天恰好')]),
 dict(page=433, id='24.34', y=108.69, top=118, bot=63, edits=[('如图 $,A$、', '如图,$A$、')]),
 dict(page=434, id='24.35', y=545.89, top=555, bot=482, edits=[('有 20 人.100 米', '有 20 人. 100 米')]),
 # 25.6: "问" for "间" (twice); the cube figure referred to by "如图" is not in the book
 dict(page=436, id='25.6', y=598.89, top=608, bot=553,
      edits=[('如图, 把正方体形', '把正方体形'), ('每个小房问走到', '每个小房间走到'), ('任何一问去', '任何一间去')]),
]
