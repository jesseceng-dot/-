# 工作底稿

《初中数学竞赛多功能题典》校勘的工作记录与脚本。结论以上级目录的《校勘说明》为准。

## 逐页校勘记录.md

通读全书时的逐条记录，格式为“页码(PDF) | 题号 | 类别 | 问题 | 处理”。“处理”栏是当时的工作结论；后来经复核改变或细化的条目，最终结论记在 `tools/mklog.py` 的 `FIX` 表中。《校勘说明》第二、三、五节由 `mklog.py` 据此生成。

## tools/

| 脚本 | 作用 |
|---|---|
| `pdfedit.py`、`engine.py` | 解析、改写页面内容流（字形、线条、补丁白框），把新排的字形映射到书中已嵌入的字体 |
| `texlayout.py` | 用 XeLaTeX 按原书参数排版（版心、行距、字体、中西文间距等），读回每个字形的位置 |
| `totex.py`、`vis.py` | 由页面字形还原一段文字的 LaTeX 源（重排的起点）；可见文字提取 |
| `para.py`、`disp.py` | 段落重排（对齐原书基线，只替换发生变化的行，行数变化时移动下方内容）；显示公式重排 |
| `run.py` | 执行修改规格；`--selftest` 不施改，只检验未改的原文能否逐字形重现 |
| `specs1.py`、`specs_a.py`…`specs_l.py` | 全部修改规格，每条注明题号和理由 |
| `specs_fig.py`、`figs.py` | 插图的修改与补绘 |
| `final.py` | 由底本一次生成修订版 |
| `mkfonts.py` | 从底本提取所嵌的华文宋体、黑体、楷体子集，补上 Unicode cmap，供排版模拟使用 |
| `mklog.py` | 由逐页记录生成《校勘说明》的明细表 |
| `cmpfinal.py`、`vdiff.py`、`pair.py`、`crop.py` | 核验：修订版（`final.pdf`）与各批输出、底本逐页比对；改前改后对照图 |
| `barscan.py`、`dunscan.py`、`angles3.py`、`colonscan.py`、`overfull.py`、`supscan.py`、`figscan.py` 等 | 全书扫描（绝对值竖线、顿号前空格、∠ 缺横线、冒号、超出版心、上下标、插图等） |

## 复现

以下命令都在 `工作底稿/` 目录下运行。

1. 环境：TeX Live（xelatex，含 ctex、xeCJK、fontspec、amsmath）、TeX Gyre Termes、AR PL SungtiL GB；Python 3，以及 pikepdf、PyMuPDF、fontTools、Pillow、numpy。
2. 把底本放在 `工作底稿/src/book.pdf`，建立排版工作目录 `工作底稿/tex/`。
3. `python3 tools/mkfonts.py`：生成 `tex/fonts/ST{Song,Heiti,Kaiti}Book.ttf`。这些字体是底本所嵌字体的子集，版权属原字体厂商，不随仓库分发。
4. `python3 tools/final.py 修订版.pdf`：施加全部修改，同时写出修改日志 `修订版.pdf.log`。
5. 可选：`python3 tools/run.py --selftest specs_e` 检验某一批规格的原文重现情况；`python3 tools/run.py specs_e outE.pdf` 单独施加某一批规格。
