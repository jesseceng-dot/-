# 本仓库：电子书（AZW3 / EPUB）→ 出版级 PDF

**开工前先读 `docs/转换手册.md`**：里面有用户全部要求的汇总（按时间，后提的覆盖先提的）、标准版式、一步步的流程、出过的问题及解决办法、验收目标和交付清单。下面只列必须记住的几条。

## 必须遵守

- **版式**：16 开 481.89 × 680.31 pt；正文思源宋体 10.5 pt，每页 32 行 × 34 字、行距 17 pt，整页末行基线 615.0 pt；左右页边距相同；各级标题字体互不相同，也都不与正文相同；不得出现 Type3 字体。
- **强制验收**：
  - 连续页面的页底不许留白，章节末页除外；标题不落页底；
  - 不许出现孤立的标点或角标行，不许一两个字单独成页；
  - 行末不留空白；序号与标题之间的间隔不能被吞掉；
  - 题词、署名、日期、出处等短行对齐正确；
  - 原书链接、封面全部保留。
- **行内小图必须精确转成文字**：生僻字查构形数据定码位并对照上下文核实；卦爻符号逐条识别爻线。一个都不能漏：`bk_report` 的 `img_dropped` 必须为空。
- **插图**：留在正文原位；会让页底留白的图移到书末，一页一图，与正文双向链接。整页图（封面、书名页、章节页图）留在原位。
- **校订**：只在用户要求时通读校订（第 11–16 册要求过）。第 17 册起用户说“其他不需要你校订了，直接转换”；已发现的明显错误照改，PDF 里只出现改后的文字。拿不准时按最近的说法做，并在汇报里说明是怎么理解的。
- **不要动杜威**的文件和 PDF；仓库里用户自传的《初中数学竞赛多功能题典_最终校勘版.pdf》不要动。
- 不建 PR（除非用户要求）。只推送到 `claude/azw3-to-pdf-conversion-nsqcsk`，网络失败按 2/4/8/16 秒重试。提交信息末尾两行：
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
  `Claude-Session: https://claude.ai/code/session_01ENFEPRUbYncLvSsSC5V43Y`
  不在提交信息、代码、文档里写模型标识。GitHub 单个文件上限 100 MB，超过的用 7z 分卷（每卷约 45 MB）。
- 用中文汇报；工作时间长时简短报告进度。

## 流程（命令详见手册第 3 节）

```
Q=<临时目录>/qNN                                   # 目录名 qNN 也是 tools/bk_fixes.py 里 FIXES 的键
BOOK_SCRATCH=$Q python -m tools.epub_unpack <book.epub>      # AZW3 用 tools.unpack
BOOK_SCRATCH=$Q python -m tools.preflight                    # 预检：结构、注释、每张图、缺字、标点空格问题
BOOK_SCRATCH=$Q BOOK_FONT_DIR=$Q/fonts python -m tools.fonts --shared     # 新会话：全部字体
# 写 tools/bk.py 的 CFG[NN]（img_text、部件分配、段落类）和 FIXES['qNN']；再跑 preflight --book NN
export BOOK_SCRATCH=$Q BOOK_GEOM=k16 BOOK_FONT_DIR=$Q/fonts
python -m tools.bk_build NN && python -m tools.bk_report NN
python -m tools.qa_pdf $Q/out/bNN.pdf && python -m tools.qa_marks NN
python -m tools.sheet $Q/out/bNN.pdf $Q/s.png --pages 1-80 --cols 10 --dpi 30    # 逐页目检，重点页放大
python -m tools.bk_errata NN                                 # 勘误表；再写 docs/16k/NN-书名.md 和 README 一节
```

交付：`out/16k/NN-书名.pdf`，源文件放 `source/`，然后 `python -m py_compile tools/*.py`，提交，推送，用中文汇报。汇报写明：页数，改了什么、没改什么，转写了什么，验收数字，需要用户决定的事。

## 代码地图

- `tools/bk.py`：每本书的配置 `CFG` 与模块装配。`bk_extract.py`：解析 XHTML。`bk_text.py`：文字修复。`bk_fixes.py`：勘误与规范化规则。
- 排版引擎：`layout.py`（基线网格与分页求解）、`typeset.py`、`book.py`（缓存、加宽字距档重试）、`render.py`（打印）、`style.py`（字体与样式）、`fonts.py`（子集、拼合缺字）、`special.py`（封面、书后插图等特殊页）、`normalize.py`（标题断行等）。
- 验收：`bk_report.py`、`qa_pdf.py`、`qa_marks.py`、`sheet.py`、`preflight.py`。校订：`proof_dump.py`、`proof_scan.py`。调试：`modplan.py`。
- 文档：`docs/16k/NN-书名.md`（每本书的说明与验收）、`docs/16k/errata/`、`docs/16k/dispositions.md`、`docs/转换手册.md`。
