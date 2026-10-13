SPECS = [
 # 14.6: patch lines lost the bars of three angle signs and split "BC"; duplicated "证明：" before "求证："
 dict(page=277, id='14.6', y=300.19, top=313, bot=273,
      tex=r"$\triangle ABC$ 两内角 $\angle B$、$\angle C$ 平分线分别交对边于 $E$、$F,$ 而 $\angle A$ 的外角平分线交直线 $BC$ 于 $D,$ 求证：$D$、$E$、$F$ 共线."),
 # 14.23: sentence broken into two paragraphs
 dict(page=283, id='14.23', y=208.39, top=217, bot=181,
      tex=r"锐角 $\triangle ABC,$ 向外作 $\triangle ABE$ 和 $\triangle ACF,$ 使得 $AB\bot BE,$\relax$AC\bot CF,\angle EAB=\angle CAF,$ 若 $BF$、$CE$ 交于点 $P,$ 求证：$AP\bot BC.$"),
 # 14.24: sentence end "P." followed by D' without a space (primes here are ^{'})
 dict(page=284, id='14.24', y=758.89, top=773, bot=732,
      tex=r"$\triangle ABC$ 中,$D$、$E$、$F$ 分别在边 $BC$、$CA$、$AB$ 上, 且 $AD$、$BE$、$CF$ 共点于 $P.$ $D^{'}$ 也在 $BC$ 上, 且 $DD^{'}$ 与 $BC$ 的中点重合, 同理定义 $E^{'}$、$F^{'}.$ 求证：$AD^{'}$、$BE^{'}$、$CF^{'}$ 也共点."),
 # 14.33: "射" printed twice over a patch, "B',B''" with a comma
 dict(page=287, id='14.33', y=758.89, top=773, bot=732,
      tex=r"已知 $\triangle ABC$ 及直线 $l,$\relax$A$ 在 $l$ 上的射影为 $A^{'},$\relax$A^{'}$ 在 $BC$ 上的射影为 $A^{''},$ 类似地定义 $B^{'}$、$B^{''}$ 和 $C^{'}$、$C^{''},$ 求证：$A^{'}A^{''}$、$B^{'}B^{''}$ 和 $C^{'}C^{''}$ 共点."),
 # 14.34: 8.7pt gap (covered blank) between the number and the stars
 dict(page=287, id='14.34', x=99.545 + 5.455 + 2.727, y=580.59, top=590, bot=553,
      tex=r"$\bigstar$ $\bigstar$ $\bigstar$ 锐角三角形 $ABC$ 中,$\angle BAC=45^\circ ,$\relax$BE$、$CF$ 是两条高,$H$ 为 $\triangle ABC$ 的垂心,$M$、$K$ 分别是 $BC$、$AH$ 的中点. 证明：$MK$、$EF$ 和 $OH$ 共点, 这里 $O$ 为 $\triangle ABC$ 的外心."),
 dict(page=289, id='14.42', y=289.89, top=299, bot=263, edits=[('于点 $P$、$Q.T$ 为', '于点 $P$、$Q.$ $T$ 为')]),
 dict(page=290, id='14.43', y=758.89, top=768, bot=732, edits=[('$AB<AC.D$、', '$AB<AC.$ $D$、')]),
 # 15.6: patch line ran 8pt into the margin
 dict(page=293, id='15.6', y=580.59, top=590, bot=553,
      tex=r"在 \pgram$ABCD$ 的两边 $AD$ 和 $CD$ 上各取一点 $F$ 和 $E,$ 使得 $AE=CF,$\relax$AE$ 与 $CF$ 交于 $P,$ 求证：$BP$ 是 $\angle APC$ 的平分线."),
 dict(page=294, id='15.11', y=299.99, top=312, bot=273, edits=[]),
 # 15.15: parallelogram sign raised to superscript position by a patch
 dict(page=295, id='15.15', y=402.29, top=416, bot=393,
      tex=r"设 \pgram$ABCD$ 中,$\angle ABC=\theta \le 90^\circ ,$ 点 $P$ 为其内部任一点, 求证："),
 dict(page=297, id='15.24', y=235.59, top=245, bot=208, edits=[('和面积和', '的面积和')]),
 # 15.32: first line ran 8pt into the margin
 dict(page=299, id='15.32', y=205.69, top=215, bot=178,
      tex=r"已知 \pgram$ABCD,$\relax$M$、$N$ 分别在 $AD$、$AB$ 上,$S_{\triangle MDC}=S_{1},$\allowbreak$S_{\triangle AMN}=S_{2},$\allowbreak$S_{\triangle CBN}=S_{3},$ 试用 $S_{1}$、$S_{2}$、$S_{3}$ 表示 $S_{\triangle CMN}.$"),
 dict(page=302, id='15.39', y=755.09, top=764, bot=728, edits=[('在边 $CD$ 上 $BN$ 与', '在边 $CD$ 上,$BN$ 与')]),
 # 15.40: patch destroyed the fractions and the rest of the problem (restored; see the log)
 dict(page=302, id='15.40', y=576.69, top=597, bot=560, obase=[576.69],
      tex=r"已知 $\angle ABC=90^\circ ,$\relax$D$ 在 $AC$ 上, 且 $\dfrac{AB+BD}{BC+BD}=\dfrac{AD}{DC},$ 求证：$BD^{2}=S_{\triangle ABC}.$"),
 # 15.41: K, M midpoints and KLMN a parallelogram give S_KLMN = S_ABCD / 2
 dict(page=302, id='15.41', y=416.69, top=426, bot=389,
      tex=r"点 $K$、$M$ 分别是凸四边形 $ABCD$ 的边 $AB$、$CD$ 的中点, 点 $L$、$N$ 分别在 $BC$、$AD$ 上使四边形 $KLMN$ 为平行四边形, 证明：$S_{ABCD}=2S_{KLMN}.$"),
 # 15.42: first line ran 8pt into the margin
 dict(page=302, id='15.42', y=238.39, top=250, bot=211,
      tex=r"已知 \pgram$ABCD$ 中,$E$、$F$ 分别在 $BC$、$CD$ 上,$P$、$Q$、$R$ 分别为 $AE$、$EF$、$AF$ 的中点, 求证：$BP$、$CQ$、$DR$ 三线共点."),
 # 15.69: name of the quadrilateral missing; paragraph continues on p310
 dict(page=309, id='15.69', y=87.29, top=96, bot=78, max_lines=1,
      tex=r"已知 $E$、$F$、$G$、$H$ 分别为凸四边形 $ABCD$ 的边 $DA$、$AB$、$BC$、$CD$ 的中点,$AG$、$BE$ 交于 $M,$\relax$CE$、$DG$ 交于 $N,$ 求证：$MN\parallel FH$ 或重合."),
 dict(page=310, id='15.69b', x=56.693, y=758.89, top=768, bot=750, para_x=159.858, skip_lines=1,
      tex=r"已知 $E$、$F$、$G$、$H$ 分别为凸四边形 $ABCD$ 的边 $DA$、$AB$、$BC$、$CD$ 的中点,$AG$、$BE$ 交于 $M,$\relax$CE$、$DG$ 交于 $N,$ 求证：$MN\parallel FH$ 或重合."),
 # 15.70: "ACHK、AG" read as five squares
 dict(page=310, id='15.70', y=598.89, top=608, bot=572,
      tex=r"如图, 以锐角 $\triangle ABC$ 的边为边向外作正方形 $ABDE$、$BCFG$、$ACHK,$\relax$AG$、$BH$、$CE$ 围成 $\triangle PQR,$ 而 $AF$、$BK$、$CD$ 围成 $\triangle P^{'}Q^{'}R^{'}$(图中未画出), 求证：$\triangle PQR\cong \triangle P^{'}Q^{'}R^{'}.$"),
 # 15.71: figure drawn 12pt too high (apex label on the text line)
 dict(page=310, id='15.71fig', kind='move', rect=(210, 150, 410, 275), gpred=lambda g: abs(g.size - 8.5) < 0.01, dy=-12),
 dict(page=310, id='15.71A', kind='move', rect=(290, 276, 305, 284), gpred=lambda g: abs(g.size - 8.5) < 0.01, kinds=(), dy=-12),
 dict(page=311, id='15.73', y=758.89, top=768, bot=732, edits=[(r'在 $\triangle ABC$ 在某条中线上', r'在 $\triangle ABC$ 的某条中线上')]),
 # 16.4: sentence broken into two paragraphs
 dict(page=314, id='16.4', y=758.89, top=768, bot=732,
      tex=r"在 $\triangle ABC$ 内取一点 $M$ 使 $\angle MAB=10^\circ ,\angle MBA=30^\circ .$ 设 $\angle ACB=80^\circ ,AC=BC.$ 求 $\angle AMC.$"),
 # 16.6: corner labels A, B of the square printed on the text line
 dict(page=314, id='16.6AB', kind='move', rect=(240, 292, 380, 300), gpred=lambda g: abs(g.size - 8.3) < 0.01, kinds=(), dy=-19.46),
 # 16.7: sentence broken into two paragraphs
 dict(page=314, id='16.7', y=119.09, top=128, bot=73,
      tex=r"如图,$\triangle ABC$ 和 $\triangle ADE$ 是两个不全等的等腰直角三角形,$\angle ABC=\angle ADE=90^\circ ,$ 现固定 $\triangle ABC$ 而将 $\triangle ADE$ 绕点 $A$ 在平面上旋转, 试证：不论 $\triangle ADE$ 旋转到什么位置, 线段 $EC$ 上必存在点 $M$ 使 $\triangle BMD$ 为等腰直角三角形."),
 dict(page=317, id='16.13(2)', x=78.51, y=454.29, top=463, bot=427, edits=[(r'$AD\parallel BC.M$ 是', r'$AD\parallel BC.$ $M$ 是')]),
 # 16.15: sentence broken into two paragraphs
 dict(page=318, id='16.15', y=758.89, top=768, bot=732,
      tex=r"如图,$\angle A=\angle B,$\relax$AA_{1}$、$PP_{1}$、$BB_{1}$ 均垂直于 $A_{1}B_{1},$ 垂足为 $A_{1}$、$P_{1}$、$B_{1},$\relax$AA_{1}=17,$\relax$PP_{1}=16,$\relax$BB_{1}=20,$\relax$A_{1}B_{1}=12.$ 求 $AP+BP$ 的值."),
 dict(page=321, id='16.24', y=206.59, top=216, bot=198, edits=[(r'$PB=3.PD=\sqrt{7},$', r'$PB=3,$\relax$PD=\sqrt{7},$')]),
 # 16.27, 16.30: sentences broken into two paragraphs
 dict(page=322, id='16.27', y=135.49, top=144, bot=108,
      tex=r"如图所示,$P$、$Q$ 是边长为 1 的正方形 $ABCD$ 内两点, 使得 $\angle PAQ=\angle PCQ=45^\circ ,$ 求 $S_{\triangle PAB}+S_{\triangle PCQ}+S_{\triangle QAD}$ 的值."),
 dict(page=324, id='16.30', y=758.89, top=768, bot=725,
      tex=r"如图, 设 $D$ 为锐角 $\triangle ABC$ 内一点, 且 $AC\cdot BD=AD\cdot BC,$\relax$\angle ADB=\angle ACB+90^\circ ,$ 求 $\dfrac{AB \cdot CD}{AC \cdot BD}$ 的值."),
]
