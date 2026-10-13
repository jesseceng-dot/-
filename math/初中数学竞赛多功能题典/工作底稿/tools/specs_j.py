SPECS = [
 dict(page=442, id='25.29', y=758.89, top=768, bot=713, edits=[('涂且黑色', '涂成黑色')]),
 dict(page=445, id='26.6', y=543.99, top=553, bot=535, edits=[('商是 $a.$ 余数是', '商是 $a,$ 余数是')]),
 # 26.11: the unknown n printed as a closing quote
 dict(page=446, id='26.11', y=402.29, top=411, bot=375, edits=[(r'求\textquotedblright{} 的最小值', '求 $n$ 的最小值')]),
 dict(page=448, id='26.20', y=205.69, top=215, bot=178, edits=[('如果研表示', '如果 $m$ 表示')]),
 dict(page=449, id='26.22', y=580.59, top=590, bot=535, edits=[('失败记 0 分', '失败积 0 分')]),
 # 26.25: closing quote printed as a double prime
 dict(page=450, id='26.25', x=78.51, y=722.39, top=731, bot=695,
      edits=[(r"\textquotedblleft{}$n\times n''(n\ge 5)$ 的方格纸", r"\textquotedblleft{}$n\times n$\textquotedblright{}$(n\ge 5)$ 的方格纸")]),
 dict(page=450, id='26.27', y=365.69, top=375, bot=320, edits=[]),
 dict(page=452, id='27.1', y=707.19, top=716, bot=662, edits=[('谁放完最后一枚. 使得', '谁放完最后一枚, 使得')]),
 # 27.3: the question asks for a point set; it was joined to the proof by a comma and ended with a period
 dict(page=452, id='27.3', y=332.29, top=341, bot=305,
      edits=[('至少有 1991 个红点, 能否找到恰有 1991 个红点的点.', '至少有 1991 个红点. 能否找到恰有 1991 个红点的点集？')]),
 # 27.5: radius sqrt(3)/3 set at 8pt by a patch, radical sign hanging through the fraction bar
 dict(page=453, id='27.5', y=758.89, top=770, bot=732,
      tex=r"平面上给定 $3$ 个点. 已知其中任意两点的距离不超过 $1$, 证明：这 $3$ 个点被一个半径为 $\dfrac{\sqrt{3}}{3}$ 的圆覆盖."),
 dict(page=453, id='27.7', y=402.29, top=411, bot=375, edits=[('小于 $1$ 证明：', '小于 $1.$ 证明：')]),
 dict(page=453, id='27.8', y=223.99, top=233, bot=197, edits=[]),
 # 28.1: patch lines: "两个数. 换成", "n - / 1" split over two lines
 dict(page=458, id='28.1', y=669.09, top=678, bot=642, edits=[('任意两个数. 换成', '任意两个数, 换成'), ('$n-$ $1$ 次操作', '$n-1$ 次操作')]),
 dict(page=458, id='28.2', y=490.79, top=500, bot=463, edits=[('叠在一起.', '叠在一起？')]),
 dict(page=459, id='28.5', y=758.89, top=768, bot=732, edits=[('跳到它的相邻格', '跳到它的相邻点')]),
 # 28.13: every inner grid line must cut through some domino (not every domino)
 dict(page=461, id='28.13', y=758.89, top=768, bot=732, edits=[('必穿过任何骨牌', '必穿过某个骨牌')]),
 dict(page=461, id='28.14', y=580.59, top=590, bot=553, edits=[]),
 dict(page=461, id='28.15', y=402.29, top=411, bot=375, edits=[]),
 # 28.20 (last line, continued from p462): fraction m^2/2 set at 8pt by a patch
 dict(page=463, id='28.20', x=56.693, y=758.89, top=770, bot=748, single=True,
      tex=r"填数是 $0$, 则该行与该列的数之和不小于 $m$, 求证：表中所有数之和不小于 $\dfrac{m^{2}}{2}.$"),
 dict(page=463, id='28.22', y=402.29, top=411, bot=338, edits=[('这样的交换进行', '这样的变换进行')]),
 # 28.26: "他们的回答有真有假." broken over three lines
 dict(page=464, id='28.26', y=258.19, top=267, bot=213,
      tex=r"某班甲、乙两名同学因一件事件发生纠纷. 老师找了 4 位在场同学调查情况, 他们的回答有真有假."),
 # 28.38: continuation line indented
 dict(page=468, id='28.38', y=580.59, top=590, bot=553,
      tex=r"能否把 $1,2,\ldots ,10$ 这 10 个数分别放在圆周上, 使得任意相邻两数之差的绝对值为 3、4 或 5？把 10 改成 13、14, 结论分别如何？"),
 dict(page=469, id='28.42', y=580.59, top=590, bot=517, edits=[('这 $n-1$ 球队', '这 $n-1$ 个球队')]),
 # 28.43(3): patch line: fraction at script size, spacing unlike (1), (2)
 dict(page=469, id='28.43(3)', x=78.51, y=292.59, top=302, bot=282, single=True,
      tex=r"(3) 证明：若 ($a,b$) 是 \textquotedblleft{}和谐\textquotedblright{} 的, 且 $\dfrac{a}{b}$ 是有理数, 则 $a$、$b$ 都是有理数."),
 dict(page=470, id='29.1', y=707.19, top=716, bot=680, edits=[('认识其中的二个人', '认识其中的两个人')]),
 dict(page=470, id='29.4', y=153.99, top=163, bot=145, edits=[('它们的朋友数目', '他们的朋友数目')]),
 # 29.9: label and star alone on their line
 dict(page=472, id='29.9', x=102.795 + 10.298 + 2.727, y=758.89, top=768, bot=713,
      tex=r"已知九个人 $A_{1},A_{2},\ldots ,A_{9}$ 中,$A_{1}$ 和两个人握过手,$A_{2}$、$A_{3}$ 各和四个人握过手,$A_{4}$、$A_{5}$、$A_{6}$、$A_{7}$ 各和五个人握过手,$A_{8}$、$A_{9}$ 各和六个人握过手. 证明：这九个人中一定可以找出三个人, 他们相互握过手."),
 # 29.18: the figures (a), (b) referred to are not in the book; the facts are stated in the text
 dict(page=474, id='29.18', y=287.59, top=297, bot=242, edits=[('至少有一个交叉路口, 如图 ($a$). 又已知', '至少有一个交叉路口. 又已知'), ('至少有一个交叉路口, 如图 ($b$). 利用', '至少有一个交叉路口. 利用')]),
 # 30.13: the triangle lies inside the convex figure
 dict(page=478, id='30.13', y=755.49, top=766, bot=744, edits=[('的凸形可以放进', '的凸形内可以放进')]),
 dict(page=480, id='30.21', y=723.39, top=732, bot=696, edits=[('任意 4 固定点', '任意 4 个固定点')]),
 dict(page=482, id='30.29', y=755.49, top=766, bot=720, obase=[755.49, 732.59],
      tex=r"在边长为 $1$ 的正三角形内或边上有 6 点, 则必定有两点之间的距离不大于 $\dfrac{1}{2}.$ 如果把 \textquotedblleft{}6\textquotedblright{} 改成 \textquotedblleft{}5\textquotedblright{}, 结论仍然成立; 改成 \textquotedblleft{}4\textquotedblright{}, 则必定有两点之间距离不大于 $\dfrac{1}{\sqrt{3}}.$"),
 dict(page=483, id='30.35', y=381.89, top=391, bot=355, edits=[]),
]
