F1823 = r"已知梯形 $ABCD$ 中, $AD<BC,E$、$F$ 分别在 $AB$、$CD$ 上, $EF\parallel AD\parallel BC,$ $ED\parallel BF,$ 如果 $AD$、$EF$、$BC$ 均为正整数, 称该梯形为 ``整数梯形''. 现对于正整数 $n,$ 有正整数 $x<x'<y'<y,x+y=x'+y'=n,$ 且 $x$、$y$ 为一 ``整数梯形'' 的上、下底, $x'$、$y'$ 为另一 ``整数梯形'' 的上、下底, 求 $n$ 的最小值."
SPECS = [
 # chapter 17: editorial working note left in the text ("the first 17 problems are incomplete,
 # to be completed later"); removed, the page content moves up to the usual chapter-start position
 dict(page=325, id='ch17note', kind='remove', rect=(70, 700, 340, 717), order=0),
 dict(page=325, id='ch17shift', kind='shift', y_from=700, delta=18.30, order=1),
 # 17.1 (after the shift above): missing space in "凸n 边形"
 dict(page=325, id='17.1', y=707.19, top=719, bot=698, order=2,
      tex=r"一个凸 $n$ 边形的内角中，恰好有 4 个钝角，求 $n$ 的最大值．"),
 dict(page=327, id='17.8', y=463.49, top=472, bot=436, edits=[]),
 # 17.49: triangle name missing at the start
 dict(page=338, id='17.49', y=309.39, top=318, bot=282,
      tex=r"如图, 在 $\triangle ABC$ 中,$D$、$E$ 分别是边 $BC$、$AB$ 上的点, 且 $\angle 1=\angle 2=\angle 3.$ 如果 $\triangle ABC$、$\triangle EBD$、$\triangle ADC$ 的周长依次为 $m$、$m_{1}$、$m_{2},$"),
 # 17.50: point name O missing at the start; "H,I" with a comma; sentence end "AB.D"
 dict(page=339, id='17.50', y=758.89, top=768, bot=732,
      tex=r"$O$ 为 $\triangle ABC$ 内一点, 过 $O$ 引三条边的平行线 $DE\parallel BC,FG\parallel CA,HI\parallel AB.$ $D$、$E$、$F$、$G$、$H$、$I$ 为各边上的点 (如图), 记 $S_{1}$ 为六边形 $DGHEFI$ 的面积,$S_{2}$ 为 $\triangle ABC$ 的面积. 证明：$S_{1}\ge \dfrac{2}{3}S_{2}.$"),
 # 17.57: patch angle sign reduced to a raised slash; "sin" and its argument split over two lines
 dict(page=341, id='17.57', y=758.89, top=768, bot=732,
      tex=r"已知 $\triangle ABC$ 三边分别为 $a$、$b$、$c,$ 其中 $b$、$c$ 确定,$D$ 为 $BC$ 中点,$\angle ADC=\theta ,$ 求 $\sin \theta$ 的最大值 ($a$ 不固定, 用 $b$、$c$ 表示)."),
 # 17.59: degree sign not raised; "b.a" with a period
 dict(page=341, id='17.59', y=131.59, top=141, bot=104,
      tex=r"$\triangle ABC$ 内 (或边界上) 有一点 $D,\angle ADC+\angle ABC=180^\circ ,CD=AB=a,AC=b,a<b<2a,$ 求 $S_{\triangle ABC}-S_{\triangle ACD}$ 的最大值 (用 $a$、$b$ 表示, 需分情况讨论)."),
 dict(page=342, id='17.60', y=758.89, top=768, bot=713, edits=[(r'60\circ ,', r'60^\circ ,'), (r'90\circ$', r'90^\circ$')]),
 # 18.1: the condition "integer" was lost (a blank in the line); restored
 dict(page=343, id='18.1', y=707.19, top=716, bot=698,
      tex=r"已知 $\triangle ABC$ 的两条高长分别是 5、15, 第三条高的长为整数, 求这条高之长的所有可能值."),
 dict(page=344, id='18.6', y=598.89, top=608, bot=572, edits=[('( $p$ 奇素数)', '($p$ 奇素数)')]),
 dict(page=344, id='18.7', y=338.09, top=347, bot=311, xtol=0.3, edits=[]),
 dict(page=346, id='18.13', y=758.89, top=768, bot=732, xtol=0.3, edits=[]),
 dict(page=346, id='18.14', y=458.09, top=467, bot=431, xtol=0.3, edits=[]),
 dict(page=347, id='18.17', y=580.59, top=590, bot=553, xtol=0.3, edits=[]),
 dict(page=347, id='18.18', y=265.79, top=275, bot=238, xtol=0.3, edits=[]),
 # 18.19 (last line, continued from p347): "举了" for "举出"
 dict(page=348, id='18.19', x=56.693, y=758.89, top=768, bot=750, single=True, tex=r"两条直角边的可取值 (如不止一组解, 只需举出一组即可)."),
 dict(page=348, id='18.20', y=598.89, top=608, bot=590, xtol=0.3, edits=[]),
 dict(page=348, id='18.21', y=438.89, top=448, bot=412, xtol=0.3, edits=[]),
 dict(page=348, id='18.22', y=260.59, top=270, bot=236, xtol=0.3, edits=[]),
 # 18.23: relation signs of "x<x'<y'<y, x+y=x'+y'=n" partly set in the text font (p349)
 dict(page=348, id='18.23', y=82.29, top=91, bot=73, max_lines=1, xtol=0.3, tex=F1823),
 dict(page=349, id='18.23b', x=56.693, y=758.89, top=768, bot=713, para_x=151.733, skip_lines=1, xtol=0.3, tex=F1823),
 # 18.25: continuation line indented as a new paragraph
 dict(page=349, id='18.25', y=281.19, top=290, bot=254,
      tex=r"已知 $PA$、$PB$ 为圆的切线, 割线过 $P,$ 与圆交于 $M$、$N,$ 与 $AB$ 交于 $S,$ 若 $PA$、$PM$、$MS$、$SN$ 均为正整数, 求 $PA$ 的最小值."),
 dict(page=350, id='18.27', y=598.89, top=608, bot=572, edits=[]),
 # 18.28: "1 ／ 3" with a full-width slash
 dict(page=350, id='18.28', y=333.49, top=342, bot=288, xtol=0.3, edits=[('的 1 ／ 3, 其顶点', r'的 $\dfrac{1}{3},$ 其顶点')]),
 dict(page=353, id='19.2', y=509.09, top=518, bot=500, xtol=0.3, edits=[]),
 # 19.6: 2^2 printed as "22"
 dict(page=354, id='19.6', y=598.89, top=608, bot=590, edits=[('$3^{n}+1$ ( $n$ 为正整数) 能被 2 或 22 整除', '$3^{n}+1$ ($n$ 为正整数) 能被 2 或 $2^{2}$ 整除')]),
 dict(page=354, id='19.7', y=438.89, top=448, bot=430, xtol=0.3, edits=[]),
 dict(page=354, id='19.9', y=118.79, top=128, bot=110, xtol=0.3, edits=[]),
 dict(page=355, id='19.10', y=753.39, top=770, bot=740, xtol=0.3, edits=[]),
 dict(page=357, id='19.24', y=82.09, top=91, bot=73, xtol=0.3, edits=[]),
 dict(page=358, id='19.25', y=758.89, top=768, bot=732, xtol=0.3, edits=[]),
 dict(page=358, id='19.27', y=418.29, top=427, bot=409, xtol=0.3, edits=[]),
 dict(page=358, id='19.28', y=256.99, top=266, bot=248, xtol=0.3, edits=[]),
 # 19.30: "1,343" reads as one thousand three hundred forty-three
 dict(page=359, id='19.30', y=580.59, top=590, bot=535, edits=[('例如： 1,343 及', '例如：1、343 及')]),
 dict(page=360, id='19.35', y=383.99, top=393, bot=375, edits=[('共有多少个.', '共有多少个？')]),
]
