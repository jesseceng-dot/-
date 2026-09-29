"""Generate docs/kant/*.md (dispositions, Greek table, inline-image transcriptions) from the data the conversion uses."""
import os
import re
import collections
from . import style, kant, kant_text as KT, kant_struct as KS, kant_extract as KE, kant_tables

DOC = os.path.join(style.ROOT, 'docs', 'kant')


def table(rows, head):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return out


def greek_doc():
    rows = [(f'`{a}`', f'`{b}`') for a, b in KT.GREEK.items() if not a.startswith('χατ')]
    lines = ['# 希腊文还原表', '',
             '电子书里的希腊文是无重音的转写文字：词末 ς 写成 s / c / ζ，个别字母被错成拉丁字母或形近字母（ν 代 υ、θ 代 τ、π 代 ρ、V 代 ς 等）。',
             '下面逐词列出还原前后的写法；还原依据是词义（括号里的中文/拉丁文释义）与标准写法，重音和气符按标准正字法补上。',
             '同一句在不同册里的不同错法（例如 `χατ\' αληθειαυ` / `χατ\' αληθεια`）合并为同一个还原结果。', '']
    lines += table(rows, ['电子书原文', '还原为'])
    lines += ['', '没有改动的：`Kουξ\'Oμπαξ`（祭司呼叫语，拉丁字母 K、O 与希腊字母形近，读音标注 Konx Ompax，保持原样，只把撇号统一为 ’）。']
    return lines


def images_doc():
    lines = ['# 内联小图（着重号文字、公式）的转写', '',
             '电子书里有 26 张夹在句子中间的小图：5 张是带着重号的文字（第 1 册序言），21 张是公式（第 8 册各章注释里的计算式，第 10 册一个希腊字母）。',
             '按“行内小图转成文字”的办法处理：着重号文字用 CSS `text-emphasis`（字下加点）排回原位，公式转成带上下标、根号横线的文字。', '',
             '## 着重号文字（第 1 册 序）', '']
    lines += table([(k, v) for k, v in KT.EMPH.items()], ['图', '文字'])
    lines += ['', '## 公式与符号', '', '记号：`^{}` 上标，`_{}` 下标，`⟦⟧` 根号下的内容（排成括号），`/` 分数线（横排）。', '']
    lines += table([(k, f'`{v}`') for k, v in KT.FORMULA.items()], ['图', '转写'])
    lines += ['', '说明：',
              '- `image04207`：图中分母写作 X₂（下标 2），而同一段文字里说“在 X 处的重力”，重力按距离平方递减，故转写为 X²（图上的下标是排版笔误）；',
              '- `image04200`：图中根号下为 “Y 21000 Y³”，按图照录；',
              '- `image04205`、`image04234`：图中数字里的窄空格（0.01 672、130 000）去掉，与正文里同一数字（0.01672）一致；',
              '- 因为公式是横排的，分数写成 a/b，需要时加括号，不再上下叠排。']
    return lines


def dispositions():
    from . import kant_report
    lines = ['# 康德文集：转换时的取舍与改动（自动汇总）', '',
             '按“电子书转换时产生的明显错误才改，有疑问的保持原样”的原则处理；下面每一类都可以在代码里找到对应规则。', '']
    lines += ['## 1. 结构', '',
              '- 每册各自成书：封面 → 半书名页 → 书名页 → 版权页 → 目录 → 前言（李秋零）→ 序（苗力田）及其注释 → 正文各篇 → 书后插图。',
              '- 电子书把一部作品拆成许多小文件；按标题层级重新并合：太短的相邻小文件并入前一章（`JOIN`），只有标题和题词的文件成为“分隔页”'
              '（作品名/“相关论述”整页），每个模块从新页起排。',
              '- 注释：原书每个文件末尾附该文件的注释。这里紧随篇章排“注释”；相邻的短小篇章的注释合在一起（每篇之前加小标题），避免只有几行的注释页。',
              '- 目录：源电子书的目录（分册目录、返回总目录链接）不再使用，重新生成带点线、页码和链接的目录。', '']
    lines += ['## 2. 标题层级', '',
              '源文件用 h1–h6 标签，也用 p.h7/h8/z1/z22/z3/ch/bold/jz/cuti/center1/yinwen-c 等段落类当标题，且同一编号（如“一、”）在不同作品里层级不同。'
              '规则：每个标题得到一个“源层级”（标签号，或按类与文字模式给的层级），每个模块内把出现过的层级压成连续的 1–9 级；第 1 级为模块标题。'
              '个别作品按部件另行指定：', '']
    rows = [(n, '；'.join(f'`{pat}`→{lv}' for pat, lv in ov)) for n, ov in sorted(KS.OVERRIDES.items())]
    lines += table(rows, ['部件', '正则 → 源层级'])
    lines += ['', '被当成标题的信件称呼、题词行等改回普通行：', '']
    lines += table([(n, '；'.join(f'`{pat}`→{st}' for pat, st in fx)) for n, fx in sorted(KS.STYLE_FIX.items())], ['部件', '正则 → 样式'])
    lines += ['', '并合成同一模块的部件：', '']
    lines += table([(f'part{a:04d}', '、'.join(f'part{b:04d}' for b in bs)) for a, bs in sorted(KS.JOIN.items())], ['起始', '并入'])
    lines += ['', '## 3. 标题文字的更正', '']
    lines += table([(f'part{n:04d}', f'`{o}`', f'`{nw}`') for (n, o), nw in sorted(KS.TITLE_FIX.items())], ['部件', '电子书原文', '更正为'])
    lines += ['', '另外，标题文字被录入两遍的（如“论书籍翻印的不合法性论书籍翻印的不合法性”）去掉重复。', '']
    lines += ['## 4. 文字层面的修复', '',
              '| 类别 | 处理 | 次数 |', '|---|---|---|']
    c = collections.Counter()
    for v in range(1, 11):
        KT.set_volume(v)
        a, b = KS.VOL_PARTS[v]
        for n in range(a, b + 1):
            for it in KE.items(KS.P(n)):
                for r in it['runs']:
                    if r.get('i'):
                        c['inline'] += 1
                        continue
                    t = r['t']
                    for k in KT.PUA:
                        c['pua'] += t.count(k)
                    c['dash3'] += len(KT.DASH3.findall(t))
                    for k in KT.GREEK:
                        c['greek'] += t.count(k)
                    for k in KT.WORDS:
                        c['words'] += t.count(k)
    lines += [f'| 私用区字符 | 对照其他册同一段正文的正常写法还原为 ä â ô ß Ä ç - . ’ * 和罗马数字 ⅩⅢ ⅩⅣ | {c["pua"]} |',
              f'| 三连破折号 | 第 1 册用 ——— 表示破折号，其余各册为 ——，统一为 —— | {c["dash3"]} |',
              f'| 希腊文 | 见 `greek.md` | {c["greek"]} |',
              f'| 外文词断行连字符/缺字 | 印刷版行末拆开的拉丁文词接回（comple-xa → complexa 等），François 缺软音符、Dreßkammer 等 | {c["words"]} |',
              '| 多余空格 | 全角标点前后的空格（“》 ，”）、书名号/括号内侧空格、破折号旁空格一律去掉；第 1 册数字之间的空格（“1 7 8 1 年”）去掉；NBSP 排版缩进去掉 | 见下 |',
              '| 缩写点 | “G﹒Chr﹒Recard”里的小写句点改为 “.”，缩写词后补空格（Joh. Friedr.） | |',
              '| 全角尖括号 | 第 7 册（part0194）文献引注里的 ＜纯粹理性批判＞、＜导论＞ 写成全角小于/大于号，改为书名号《》（共 3 对）；数学里的“（a+b）＞a”（第 1、7 册）保持 ＞ | 3 |',
              '| 内联小图 | 见 `inline-images.md` | 26 |', '']
    lines += ['## 5. 图与表', '',
              '- 独立的图、表（判断表、范畴表、几何示意图、自然哲学图 1–26 等）一律移到各册书末“书后插图”，正文原处留蓝字黄框的“见书后插图N”，点击跳转，每幅图下有“返回正文（第N页）”。',
              '- 第 1 册里用空格排成四象限的 4 张表（无的划分表、谬误推理表两张、自由范畴表）按原文重建为矢量小表，同样放进书后插图。', '']
    lines += ['## 6. 保持原样、无法还原的', '',
              '- 第 8 册《自然地理学》“鱼”一节里的 NFDA1–NFDA4（共 9 处，电子书的缺字占位符，原书应为生僻的鱼名用字）无法确定是哪个字，保持原样；',
              '- 第 8 册注释里公式 `image04200` 的根号下原文如此（Y 21000 Y³），未擅改；',
              '- 第 3 册里“纯粹实践理性的要素论”作为《纯然理性界限内的宗教》的标题是电子书的误置，已按第 9 册更正为“纯然理性界限内的宗教”。', '']
    return lines


def main():
    os.makedirs(DOC, exist_ok=True)
    for name, fn in (('greek.md', greek_doc), ('inline-images.md', images_doc), ('dispositions.md', dispositions)):
        with open(os.path.join(DOC, name), 'w', encoding='utf8') as f:
            f.write('\n'.join(fn()) + '\n')
    print('written to', DOC)


if __name__ == '__main__':
    main()
