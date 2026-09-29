# 贺麟中译黑格尔经典著作：AZW3 → 出版级 PDF

`source/hegel-collection.azw3` 是合集（《小逻辑》《黑格尔早期神学著作》《精神现象学》《哲学史讲演录》），
`out/` 里是转换结果：

| 文件 | 内容 |
|---|---|
| `out/00-贺麟中译黑格尔经典著作（合集）.pdf` | 合集封面 + 总目录 + 四本书（3248 页） |
| `out/01-小逻辑.pdf` | 423 页 |
| `out/02-黑格尔早期神学著作.pdf` | 488 页 |
| `out/03-精神现象学.pdf`（上、下卷） | 677 页 |
| `out/04-哲学史讲演录.pdf`（第一至四卷） | 1655 页 |

每本书按 **正文前（封面、书名页、版权页、目录、出版说明/序跋）→ 正文（按篇/章/节，章末注释）→ 正文后（附录、索引、后记、注释、书后插图）**
的顺序生成；合集 PDF 只是把四本书拼在封面和总目录之后，每本书保留自己的页码与目录。

## 版式

- 大 32 开（397 × 575 pt ≈ 140 × 203 mm），左右页边距相同（51.5 pt）。
- 正文思源宋体（Noto Serif CJK SC）五号 10.5 pt，行距 17 pt，每页 **27 行**，版心 28 字宽；希腊文用 Noto Serif（含多调字形）。
- 七级标题各用**互不相同的字体族**，且都不与正文（思源宋体）相同：一级思源黑体粗（Noto Sans CJK SC）、二级霞鹜文楷粗（LXGW WenKai）、
  三级文泉驿正黑（WenQuanYi Zen Hei）、四级文鼎楷体粗（AR PL UKai）、五级文鼎报宋粗（AR PL SungtiL）、六级文泉驿微米黑粗（WenQuanYi Micro Hei）、
  七级文鼎明体粗（AR PL UMing）；§ 编号用思源黑体中，引文/诗行用楷体。文鼎、文泉驿字体原本只有常规字重，`tools/fonts.py` 用 skia-pathops 把轮廓加粗成真正的粗体
  （不用浏览器的“伪粗体”，否则 PDF 里会变成 Type3 字体）。
- 注释、索引、版权页用 8.5–9 pt 小字（40 行/页的密网格），最后一行基线与正文页的最后一行基线严格重合。
- 页眉（单页书名 / 双页章名）、页脚页码（前置部分小写罗马数字，正文起阿拉伯数字），PDF 书签与页码标签齐全。

## 五条验收标准是怎么保证的（`docs/QA-report.md` 有实测数字）

1. **前后置部分制式**：版权页（CIP 一页）、目录（多级、点线、页码、可点击）、序跋、索引（小字悬挂缩进）、注释（编号列+回链）、附录、版本说明页。
2. **每页底部基线对齐、标题不落页底**：整本书按“27 行网格”排，行由 Chromium 量出，分页由自写的动态规划求解器决定——
   每个段落有 7 档肉眼几乎看不出的字距（±0.012/0.024/0.036 em）可选，标题前空行可 ±1，用它们把每页恰好排满；
   标题及其后至少两行同页；末页不少于 3 行；实测：4 本书 **0 页需要拉伸**、0 个标题落页底、每个非模块末页的最后一行基线都是同一个 y（516.0 pt）。
3. **封面与链接保留**；长标题用中文分词（rjieba）避免断词，按标点/虚词平衡换行；日期、署名、书信抬头、诗行、章末“* * *”等独立短行的对齐见 `docs/dispositions.md`。
4. **行末空白**：两端对齐行的行末余量靠字距微调消化；行内希腊文小图已转成文字；只有极少数因外文长词造成的松行（>3 字宽者约万分之 4），
   其中最松的一批用“单词内软连字符”处理；没有孤立的角标/标点行；没有只剩 1–2 字的末页。
5. **序号与标题间距、原书字符**：序号后的间隔用全角/宽空格实体字符，不会被 HTML/CSS/PDF 吞掉；正文文字逐字符核对无出入。

## 复现与局部重排

```
apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra fonts-lxgw-wenkai fonts-noto-core fonts-wqy-zenhei fonts-wqy-microhei \
    fonts-arphic-ukai fonts-arphic-uming fonts-arphic-gbsn00lp fonts-arphic-gkai00mp                                 # 字体
pip install playwright pymupdf pypdf fonttools lxml beautifulsoup4 pillow mobi pyphen rjieba skia-pathops
python -m tools.unpack                   # AZW3 解包为 XHTML + 图片（KindleUnpack）
python tools/fonts.py                    # 子集化字体，并把 CFF 字体转成 TrueType（否则 Chromium 会把它们嵌成 Type3）
python -c "from tools import fonts; [fonts.embolden(s, d) for d, s in fonts.BOLD_FROM.items()]"   # 生成文鼎/文泉驿的真粗体
python -m tools.make_all --dest=out      # 四本书 + 合集
python -m tools.build book3              # 只重排一本（约 30 秒；四本书最长 2 分钟）
python -m tools.build book3 --redo=part0041   # 只重排某一章（其余章节读缓存）
python -m tools.report                   # 生成 docs/QA-report.md
python -m tools.index_report             # 生成 docs/index-pages.md（索引页码换算的方法与精度）
```

结构：`tools/extract.py` 解析 XHTML；`normalize.py` 标题层级/间距、断段合并、诗行与署名对齐、尾注拆分、错字与丢字外文词还原；
`greekfix.py` 希腊文逐词还原表；`indexmap.py` 索引页码换算（印刷页 → PDF 页）；
`books.py` 每本书的模块配置（前/正文/后、每章的修正规则）；`measure.py` + `layout.py` + `typeset.py` 量行与分页求解；
`render.py` 逐行绝对定位输出 HTML；`book.py` 装配（目录、页码、页眉）；`post.py` 把占位链接改写为 PDF 内部链接、加书签；
`collection.py` 合并并生成总目录；`check.py`/`qa.py`/`charcheck.py` 验收检查。

## 需要你知道的

- **索引页码**：原书索引里的页码是商务印书馆版的印刷页码，电子书里没有印刷页码标记，所以这里是**反推换算**的：先在正文里查条目词的位置来校准
  “印刷页 ↔ 正文位置”，再把每个页码换成本 PDF 页码（可点击）。换算的方法、命中率和留一法检验精度见 `docs/index-pages.md`，逐条对照见 `docs/index-page-map/`；
  索引开头有一段小字说明。条目词在正文里找不到的，按前后页码内插，可能与原书页码相差一页。
- 全部改动与无法还原的地方见 `docs/dispositions.md`；希腊文小图的逐张核对见 `docs/greek-ocr.md`。


---

# 康德文集（注释版）（套装共 10 册）：AZW3 → 出版级 PDF

`source/kant-collection.azw3` 是中国人民大学出版社 2016 年版《康德文集（注释版）》（李秋零译注）的 10 册合集，
`out/kant/` 是转换结果：每册各成一本，另有一个合集 PDF（封面 + 总目录 + 十册，各册保留自己的页码与目录）。

| 文件 | 内容 | 页数 | 大小 |
|---|---|---|---|
| `out/kant/00-康德文集（注释版）（合集）.pdf` | 合集：封面 + 总目录 + 十册（各册保留自己的页码、目录与书签） | 6822 | 41.4 MB |
| `out/kant/01-康德三大批判合集.pdf` | 康德三大批判合集 | 1203 | 5.4 MB |
| `out/kant/02-康德人类学文集.pdf` | 康德人类学文集 | 371 | 2.7 MB |
| `out/kant/03-康德道德哲学文集.pdf` | 康德道德哲学文集 | 936 | 5.1 MB |
| `out/kant/04-康德历史哲学文集.pdf` | 康德历史哲学文集 | 245 | 1.9 MB |
| `out/kant/05-康德政治哲学文集.pdf` | 康德政治哲学文集 | 407 | 2.8 MB |
| `out/kant/06-康德美学文集.pdf` | 康德美学文集 | 457 | 2.4 MB |
| `out/kant/07-康德认识论文集.pdf` | 康德认识论文集 | 1368 | 7.5 MB |
| `out/kant/08-康德自然哲学文集.pdf` | 康德自然哲学文集 | 1091 | 9.1 MB |
| `out/kant/09-康德宗教哲学文集.pdf` | 康德宗教哲学文集 | 572 | 3.1 MB |
| `out/kant/10-康德教育哲学文集.pdf` | 康德教育哲学文集 | 156 | 1.4 MB |

## 版式（与《贺麟中译黑格尔经典著作》同一套）

- 大 32 开（397 × 575 pt），左右页边距相同；正文思源宋体五号 10.5 pt，每页 27 行、行距 17 pt，注释/版权页用 8.5–9 pt 小字（40 行/页的密网格），末行基线与正文页重合。
- **标题最多九级，每级各用不同的字体族，且都不与正文相同**：一级思源黑体粗、二级霞鹜文楷粗、三级文泉驿正黑、四级文鼎楷体粗、五级文鼎报宋粗、六级文泉驿微米黑粗、
  七级文鼎明体粗、八级文鼎简中楷粗、九级 Droid Sans Fallback 粗（前六种之外的字体原本只有常规字重，`tools/fonts.py` 用 skia-pathops 加粗轮廓，不用浏览器伪粗体，避免 Type3 字体）。
- 每册：封面 → 半书名页 → 书名页 → 版权页 → 目录（点线、页码、可点击，作品名加粗，篇章缩进在作品名之下）→ 前言（李秋零）→ 序（苗力田）及其注释 → 正文 →
  书后插图；作品名、“相关论述”等整页为分隔页；页眉（单页书名 / 双页篇名）、页脚页码（前置部分罗马数字）、PDF 书签与页码标签齐全。
- 注释紧随所属篇章，用小字号、编号列 + 回链排；相邻短篇的注释合并为一组（每篇前有小标题），不出现只有几行的注释页。
- 图表：独立的图和表（判断表、范畴表、几何示意图、自然哲学图 1–26 等）一律移到书后插图，**每页一图**（页首“插图 N”，页底“↩ 返回正文（第N页）”，与黑格尔各册的插图页同一版式），正文原处是蓝字黄框的“见书后插图N”（可点击）；
  第 1 册里用空格排成四象限的 4 张表按原文重建为矢量表；夹在句子里的 26 张小图（着重号文字、公式）转成文字（着重号用 `text-emphasis`），见 `docs/kant/inline-images.md`。
- 文字：私用区字符、三连破折号、全角标点前后多余空格、断行连字符、无重音的希腊文等逐类修复，全部列在 `docs/kant/dispositions.md`、`docs/kant/greek.md`。
  第 8 册《自然地理学》“鱼”一节里电子书的缺字占位符 NFDA1–4，按编者注和鱼名考订为 𫚕（舟鰤）、𫚉（魟）、𩽾𩾌（鮟鱇），依据与把握程度见 `docs/kant/dispositions.md` 第 6 节；
  思源宋体没有 𫚉，`tools/fonts.py` 的 `compose_hong` 用它自己的笔画合成一个宋体字形。

## 验收（`docs/kant/QA-report.md` 有逐册实测数字）

五条验收标准与黑格尔各册相同：每页文字页（含注释页）末行基线严格相同；标题不落页底、标题后至少两行；封面与链接保留；长标题按词平衡换行；
序号与标题之间用不会被吞掉的全角空格；没有孤立标点/角标行、没有只剩 1–2 字的末页；逐字符核对正文无出入（改动全部有说明）。

## 复现

```
python -m tools.unpack source/kant-collection.azw3      # 需 BOOK_SCRATCH=<工作目录>
BOOK_FONT_DIR=<字体目录> python tools/fonts.py           # 子集字体 + 真粗体（fonts.py 里的 BOLD_FROM）
python -m tools.kant_make_all --dest=out/kant            # 十册 + 合集
python -m tools.kant_build 3 --redo=part0058             # 只重排第 3 册的某个模块
python -m tools.kant_report                              # 验收数字 -> docs/kant/QA-report.md
python -m tools.kant_docs                                # dispositions / greek / inline-images
```

结构：`tools/kant_extract.py` 解析 XHTML；`kant_struct.py` 标题层级、短行样式、模块单元（分隔页/并合/拆分）；`kant_text.py` 文字修复、希腊文、公式转写；
`kant_tables.py` 第 1 册的四象限表；`kant.py` 每册的模块装配（注释分组、书后插图、目录）；`kant_build.py` / `kant_collection.py` / `kant_make_all.py` 构建；
`kant_report.py` / `kant_docs.py` 验收与文档。排版引擎（`layout.py` / `measure.py` / `typeset.py` / `render.py` / `book.py`）与黑格尔各册共用。


---

# 《杜威著作精选11种》：AZW3 → 出版级 PDF

`source/dewey-selection.azw3` 是华东师范大学出版社《杜威著作精选》的 11 种合集（学校与社会、明天的学校、民主与教育、作为经验的艺术、哲学的改造、经验与自然、确定性的寻求、心理学、伦理学、我们如何思维、人性与行为），
`out/dewey/` 是转换结果：每册各成一本，另有一个合集 PDF（封面 + 总目录 + 十一册，各册保留自己的页码与目录）。

| 文件 | 内容 | 页数 | 大小 |
|---|---|---|---|
| `out/dewey/00-杜威著作精选11种（合集）.pdf` | 合集：封面 + 总目录 + 十一册（各册保留自己的页码、目录与书签） | 3473 | 26.5 MB |
| `out/dewey/01-学校与社会.pdf` | 学校与社会 | 116 | 1.7 MB |
| `out/dewey/02-明天的学校.pdf` | 明天的学校 | 211 | 4.1 MB |
| `out/dewey/03-民主与教育.pdf` | 民主与教育 | 396 | 2.2 MB |
| `out/dewey/04-作为经验的艺术.pdf` | 作为经验的艺术 | 407 | 3.2 MB |
| `out/dewey/05-哲学的改造.pdf` | 哲学的改造 | 164 | 1.3 MB |
| `out/dewey/06-经验与自然.pdf` | 经验与自然 | 451 | 2.3 MB |
| `out/dewey/07-确定性的寻求.pdf` | 确定性的寻求 | 281 | 1.6 MB |
| `out/dewey/08-心理学.pdf` | 心理学 | 386 | 2.3 MB |
| `out/dewey/09-伦理学.pdf` | 伦理学 | 504 | 3.4 MB |
| `out/dewey/10-我们如何思维.pdf` | 我们如何思维 | 273 | 2.3 MB |
| `out/dewey/11-人性与行为.pdf` | 人性与行为 | 272 | 2.0 MB |

## 版式（与黑格尔、康德各册同一套）

- 大 32 开（397 × 575 pt），左右页边距相同；正文思源宋体五号 10.5 pt，每页 27 行、行距 17 pt，注释/版权页用 8.5–9 pt 小字，末行基线与正文页重合；标题最多四级，每级各用不同的字体族（一级思源黑体粗、二级霞鹜文楷粗、三级文泉驿正黑、四级文鼎楷体粗）。
- 每册：封面 →（前折页）→ 书名页 → 版权页 → 目录（点线、页码、可点击）→ 主编序及各篇序跋 → 正文各章（“第N部分”为整页分隔页）→ 章末注释（小字号、编号列 + 回链）→ 译后记/附录/校后记 → 书后插图 →（后折页、封底）。
- **整页图不后置**：封面、书名页（整页图，含杜威签名与译者）、折页与封底、章节页头图（《明天的学校》序页上的照片）都留在原位置；只有夹在正文中间的照片、儿童画和示意图后置，
  **一页一图**，页首“插图 N　图注”，页底“↩ 返回正文（第N页）”，正文原处是图注加蓝字黄框的“见书后插图N”（可点击）。
- 文字：原书斜体强调的楷体、拉丁文斜体、注释角标与回链、行内小图（着重的希腊文单词、一个生僻字、根号）全部转成文字；私用区字符还原、直撇号改为 ’；全部改动列在 `docs/dewey/dispositions.md`、`docs/dewey/inline-images.md`。

## 验收（`docs/dewey/QA-report.md` 有逐册实测数字）

五条验收标准与黑格尔、康德各册相同：整页文字页（含注释页）末行基线严格相同（516.0 pt）；标题不落页底、标题后至少两行；封面与链接保留；序号与标题之间的空隙不会被吞掉；没有孤立标点/角标行、没有只剩 1–2 字的末页；逐字符核对正文无出入（改动全部有说明）。

## 复现

```
python -m tools.unpack source/dewey-selection.azw3      # 需 BOOK_SCRATCH=<工作目录>
BOOK_FONT_DIR=<字体目录> python tools/fonts.py           # 子集字体 + 真粗体
python -m tools.dewey_make_all --dest=out/dewey         # 十一册 + 合集
python -m tools.dewey_build 3 --redo=part0041           # 只重排第 3 册的某个模块
python -m tools.dewey_report                            # 验收数字 -> docs/dewey/QA-report.md
python -m tools.dewey_docs                              # dispositions / inline-images
```

结构：`tools/dewey_extract.py` 解析 XHTML；`dewey_text.py` 文字修复与行内小图转写；`dewey.py` 每册的模块装配（部件表、标题层级、注释分组、书后插图、目录）；
`dewey_build.py` / `dewey_collection.py` / `dewey_make_all.py` 构建；`dewey_report.py` / `dewey_docs.py` 验收与文档。排版引擎（`layout.py` / `measure.py` / `typeset.py` / `render.py` / `book.py`）与黑格尔、康德各册共用。

---

# 四本 16 开书：AZW3 → 出版级 PDF

`source/` 里的四本电子书转成 170 × 240 mm（16 开）的 PDF，放在 `out/16k/`：

| 文件 | 书 | 页数 |
|---|---|---|
| `01-巴菲特致股东的信.pdf` | 《巴菲特致股东的信·投资原则篇》（〔美〕杰里米·米勒 著，郝旭奇 译，中信出版集团） | 252 |
| `02-财富、贫穷与政治.pdf` | 《财富、贫穷与政治》（〔美〕托马斯·索维尔 著，孙志杰 译，浙江教育出版社） | 186 |
| `03-工作、消费主义和新穷人.pdf` | 《工作、消费主义和新穷人》（〔英〕齐格蒙特·鲍曼 著，郭楠 译，上海社会科学院出版社） | 114 |
| `04-股票大作手回忆录.pdf` | 《股票大作手回忆录》（〔美〕埃德温·勒菲弗 著，丁圣元 译，凤凰出版社） | 280 |

## 版式（以样张 PDF 为标准）

- 页面 **481.89 × 680.31 pt**（与样张的页面框逐位相同）；正文思源宋体 **10.5 pt（五号）**（样张实测 10.46 pt）；每页 32 行 × 34 字，行距 17 pt，左右页边距相同；
- 所有整页文字页（含小字号的注释页）末行基线相同（615.0 pt）；标题不落页底、标题后至少两行；没有孤立标点/角标行、没有只剩 1–2 字的末页；
- 引文、多级标题、目录、页眉页脚、书签、链接与黑格尔、康德、杜威各册同一套排法；
- **整页图不后置**：封面、书名页图、作为整个章节页的图（第 1 本附录的收益表图、第 4 本附录一的曲线图、第 3 本末页的二维码）留在原位；夹在正文中间的图表后置到书末，一页一图，页首“插图 N　图注”，页底“↩ 返回正文（第N页）”，正文原处是图题加蓝字黄框的“见书后插图N”（可点击）；
- 全部改动列在 `docs/16k/dispositions.md`，验收数字（逐本实测）在 `docs/16k/QA-report.md`。

## 复现

```
python -m tools.unpack source/<书>.azw3                  # 需 BOOK_SCRATCH=<该书的工作目录>
BOOK_SCRATCH=<dir> BOOK_FONT_DIR=<dir>/fonts python tools/fonts.py    # 子集字体
python -m tools.bk_make_all --scratch=<根目录> --dest=out/16k         # 四本（每本一个工作目录 q1…q4）
python -m tools.bk_report <1-4>  ;  python -m tools.bk_report --write <根目录>
python -m tools.bk_docs <1-4>    ;  python -m tools.bk_docs --write <根目录>
```

结构：`tools/bk_extract.py` 解析 XHTML；`bk_text.py` 文字修复；`bk.py` 每本的模块装配（部件表、标题层级、注释分组、书后插图、目录、末页二维码）；
`bk_build.py` / `bk_make_all.py` 构建；`bk_report.py` / `bk_docs.py` 验收与文档。页面几何由环境变量 `BOOK_GEOM=k16` 选择（`d32` 是原来的大 32 开）。排版引擎与前几套书共用。

## 第 5–10 册（同一套 16 开版式）

同样的页面（481.89 × 680.31 pt）、字号（10.5 pt）、行数（32 行 × 34 字）、末行基线（615.0 pt）和图表处理办法，另外六本书放在 `out/16k/`：

| 文件 | 书 | 页数 |
|---|---|---|
| `05-叫魂.pdf` | 《叫魂：1768年中国妖术大恐慌》（〔美〕孔飞力 著，陈兼、刘昶 译，上海三联书店；EPUB） | 263 |\n| `06-狂热分子.pdf` | 《狂热分子：码头工人哲学家的沉思录》（〔美〕埃里克·霍弗 著，梁永安 译，广西师范大学出版社；EPUB） | 157 |\n| `07-漫步华尔街.pdf` | 《漫步华尔街（原书第12版）》（〔美〕伯顿·G.马尔基尔 著，张伟 译，机械工业出版社） | 433 |\n| `08-失控.pdf` | 《失控：机器、社会与经济的新生物学》（〔美〕凯文·凯利 著，东西文库 译，新星出版社） | 549 |\n| `09-血酬定律.pdf` | 《血酬定律：中国历史中的生存游戏》（吴思 著，语文出版社） | 299 |\n| `10-政治学通识.pdf` | 《政治学通识》（包刚升 著，北京大学出版社） | 405 |

- 第 5、6 册是 EPUB，先由 `tools/epub_unpack.py` 解成与 AZW3 相同的目录结构，其余流水线共用；
- 第 5、6、9 册的封面用另行提供的封面图（`source/covers/`）替换电子书自带封面；
- 一章由多个文件组成的书（第 5、7 册），各文件合并成一个章节，章内的注释按章连续编号；第 5 册的图标角标、第 6 册的“【注释】”块、第 8 册的“〔n〕”、第 10 册每讲后的注释都统一成页内 `[n]` 与章末注释互相链接；
- 各册的具体取舍（哪些整页图留在原位、行内小图的转写、标题整理、电子书制作方页面的处理）见 `docs/16k/dispositions.md` 第 4b 节，验收数字见 `docs/16k/QA-report.md`；
- 复现：`python -m tools.epub_unpack <book.epub>`（EPUB）或 `python -m tools.unpack <book.azw3>`，其余同上，`bk.CFG` 里第 5–10 项是这六本书的配置。
