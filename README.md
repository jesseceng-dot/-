# 贺麟中译黑格尔经典著作：AZW3 → 出版级 PDF

`source/hegel-collection.azw3` 是合集（《小逻辑》《黑格尔早期神学著作》《精神现象学》《哲学史讲演录》），
`out/` 里是转换结果：

| 文件 | 内容 |
|---|---|
| `out/00-贺麟中译黑格尔经典著作（合集）.pdf` | 合集封面 + 总目录 + 四本书（3243 页） |
| `out/01-小逻辑.pdf` | 422 页 |
| `out/02-黑格尔早期神学著作.pdf` | 488 页 |
| `out/03-精神现象学.pdf`（上、下卷） | 678 页 |
| `out/04-哲学史讲演录.pdf`（第一至四卷） | 1650 页 |

每本书按 **正文前（封面、书名页、版权页、目录、出版说明/序跋）→ 正文（按篇/章/节，章末注释）→ 正文后（附录、索引、后记、注释、书后插图）**
的顺序生成；合集 PDF 只是把四本书拼在封面和总目录之后，每本书保留自己的页码与目录。

## 版式

- 大 32 开（397 × 575 pt ≈ 140 × 203 mm），左右页边距相同（51.5 pt）。
- 正文思源宋体（Noto Serif CJK SC）五号 10.5 pt，行距 17 pt，每页 **27 行**，版心 28 字宽；希腊文用 Noto Serif（含多调字形）。
- 标题各级用不同字体，且都不与正文相同：一级思源黑体粗、二级霞鹜文楷粗、三级思源黑体中、四级楷体粗、五至七级黑/楷体常规；
  § 编号用思源黑体中。引文/诗行用楷体。
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
apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra fonts-lxgw-wenkai fonts-noto-core   # 字体
pip install playwright pymupdf pypdf fonttools lxml beautifulsoup4 pillow mobi pyphen rjieba
python -m tools.unpack                   # AZW3 解包为 XHTML + 图片（KindleUnpack）
python tools/fonts.py                    # 子集化并把 CFF 字体转成 TrueType（否则 Chromium 会把它们嵌成 Type3）
python -m tools.make_all --dest=out      # 四本书 + 合集
python -m tools.build book3              # 只重排一本（约 30 秒；四本书最长 2 分钟）
python -m tools.build book3 --redo=part0041   # 只重排某一章（其余章节读缓存）
python -m tools.report                   # 生成 docs/QA-report.md
```

结构：`tools/extract.py` 解析 XHTML；`normalize.py` 标题层级/间距、断段合并、诗行与署名对齐、尾注拆分；
`books.py` 每本书的模块配置（前/正文/后、每章的修正规则）；`measure.py` + `layout.py` + `typeset.py` 量行与分页求解；
`render.py` 逐行绝对定位输出 HTML；`book.py` 装配（目录、页码、页眉）；`post.py` 把占位链接改写为 PDF 内部链接、加书签；
`collection.py` 合并；`check.py`/`qa.py`/`charcheck.py` 验收检查。

## 需要你知道的

- 索引条目里的页码（如“绝对理念381”“上254”）是**原书商务印书馆版页码**，与本 PDF 页码无关（原电子书里没有对应关系，无法自动换算）。
- 全部改动与疑似原书错字见 `docs/dispositions.md`；希腊文小图的逐张核对见 `docs/greek-ocr.md`。
