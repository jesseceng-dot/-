"""Generate docs/16k/dispositions.md (what was changed / decided in the four 16开 books), from the data the conversion uses.
    BOOK_SCRATCH=<dir> BOOK_GEOM=k16 python -m tools.bk_docs <book 1-4>      per-book facts -> <dir>/out/facts.json
    python -m tools.bk_docs --write <scratch-root>                            merge the four facts.json files into docs/16k/dispositions.md
"""
import os
import re
import sys
import collections
from . import style, bk, bk_extract as BE, bk_text as BT

DOC = os.path.join(style.ROOT, 'docs', '16k')


def table(rows, head):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return out


def repairs(b):
    """Counts of the automatic text repairs of book b."""
    C = bk.CFG[b]
    c = collections.Counter()
    for n in [n for n, _ in C['front']] + list(C['body']) + list(C['back']):
        for it in BE.items(bk.P(n)):
            for r in it.get('runs') or []:
                if r.get('i'):
                    continue
                t = r['t']
                c['ascii_punct'] += len(BT._RE_ASCII_PUNCT.findall(t)) + len(BT._RE_ASCII_PUNCT_END.findall(t))
                c['apos'] += len(BT._RE_APOS.findall(t))
                c['space_close'] += len(BT._RE_SPACE_CLOSE.findall(t))
                if (r.get('h') or r.get('a')) and BT.marker_text(t, C['marker']):
                    c['markers'] += 1
            c['items_' + it['k']] += 1
    return c


def counts(b):
    cfg = bk.book(b)
    mods = cfg['modules']
    n_chap = sum(1 for m in mods if m.kind == 'text' and m.zone == 'body' and not m.mid.startswith('notes'))
    n_part = sum(1 for m in mods if m.kind == 'page' and getattr(m, 'part', False))
    n_plate = sum(1 for m in mods if m.mid.startswith('plate-page'))
    n_note = sum(1 for m in mods if m.mid.startswith('notes'))
    return n_chap, n_part, n_plate, n_note


def book_facts(b):
    n_chap, n_part, n_plate, n_note = counts(b)
    return dict(b=b, title=bk.TITLES[b], chap=n_chap, part=n_part, plate=n_plate, note=n_note, rep=dict(repairs(b)),
                inplace=len(bk.CFG[b]['inplace']), tail=len(bk.CFG[b]['tail']))


def write(facts):
    import json
    lines = ['# 四本 16 开书：转换时的取舍与改动（自动汇总）', '',
             '按“电子书转换时产生的明显错误才改，有疑问的保持原样”的原则处理，逐项列出。', '']
    lines += ['## 1. 页面和字号（以样张 PDF 为标准）', '',
              '样张 `…144…pdf`（一页 PDF）的页面框为 481.89 × 680.31 pt（170 × 240 mm，即 16 开），正文是宋体，字号实测 10.46 pt（约为五号 10.5 pt）。这四本书按同样的标准排：',
              '',
              '- 页面 **481.89 × 680.31 pt**，与样张的页面框逐位相同（Chromium 打印时会把页面四舍五入成 481.92 × 679.92 pt，生成后逐页把页面框改回精确值，上边不动，所以所有基线位置不受影响）；',
              '- 正文思源宋体 **10.5 pt（五号）**，每行 34 字（版心宽 357 pt，左右页边距相同，各 62.4 pt），每页 32 行、行距 17 pt（版心高 544 pt，天头 76 pt、地脚约 60 pt）；',
              '- 注释、版权页、书后插图页上的图注等用 8.5–9 pt 小字，小字页按 47 行的小格排，末行基线仍与正文页重合（615.0 pt）；',
              '- 引文（缩进两字、10 pt 楷体/宋体）、章节标题（最多四级，各级字体族不同）、目录、页眉页脚、书签、链接均与黑格尔、康德、杜威各册同一套排法；',
              '- 版式代码里页面几何由环境变量 `BOOK_GEOM` 选择：`d32` 是原来的大 32 开，`k16` 是这里的 16 开；引擎其余部分不变。', '']
    rows = [(f['b'], f['title'], f['chap'], f['part'], f['note'], f['plate'], f['inplace'], f['tail']) for f in facts]
    lines += ['## 2. 结构', '']
    lines += table(rows, ['册', '书名', '章/篇（模块）', '“第N部分”分隔页', '注释模块', '书后插图', '留在原位的整页图', '末页原样保留的图'])
    lines += ['',
              '- 每本：封面 → 书名页 → 版权页 → 目录（点线、页码、可点击）→ 序言/前言 → 正文各章 → 章末注释（小字号、编号列 + 回链）→ 附录/致谢 → 书后插图；',
              '- 前置部分（序、导言、目录）用小写罗马数字页码，正文从 1 起；PDF 书签、页码标签与目录一致；',
              '- 第 1 本的“智慧锦囊”标题下有电子书里的装饰线，装饰线与标题、后面的正文不拆开；',
              '- 第 3 本的“第一/二/三部分”是整页分隔页；末页是出版社的两个二维码（公众号、官方微店），原样保留；',
              '- 第 4 本附录一的年表（3 列，行内小表）排成带悬挂缩进的定宽列，两张道琼斯指数曲线图留在附录一原位；',
              '- 第 2 本共 679 条尾注，按章成组排在每章之后，页内 [n] 与注释互相链接；']
    lines += ['', '## 3. 整页图与书后插图', '',
              '- **不后置（留在原位）**：封面、书名页图、作为整个章节页的图——第 1 本附录一至四的收益表图（每个附录一页至两页）、第 4 本附录一的两张曲线图、第 3 本末页的二维码；',
              '- **后置**：夹在正文中间的图表（第 1 本 7 张复利/收益表，第 3 本 0 张，第 4 本 18 张道琼斯指数图）移到书末，**一页一图**，页首“插图 N”和图注，页底“↩ 返回正文（第N页）”；'
              '正文原处是图题加蓝字黄框的“见书后插图N”（可点击）；',
              '- 第 1 本书后插图 1–3 是原书里三处各用一次的同一张复利表（三处上下文不同，图文件不同但内容相同），照原书各排一页；',
              '- 第 3 本原书末尾的两个二维码在电子书里既出现在最后一章之后又是尾页，这里只留尾页一份。', '']
    lines += ['## 4. 文字层面的修复（自动）', '',
              '电子书的文字很干净，需要处理的只有：', '',
              '| 类别 | 处理 | 第1册 | 第2册 | 第3册 | 第4册 |', '|---|---|---|---|---|---|']
    def row(label, what, key):
        return f'| {label} | {what} | ' + ' | '.join(str(f['rep'].get(key, 0)) for f in facts) + ' |'
    lines += [row('半角标点', '夹在汉字之间的 `, ; : ! ?` 改为全角 `，；：！？`', 'ascii_punct'),
              row('直撇号', "Buffett's、Poor's 等的 ASCII 撇号改为 ’", 'apos'),
              row('全角标点前的空格', '“（Genesis ）”这类拉丁词后多余的空格去掉', 'space_close'),
              row('注释角标', '第 1、3 册统一为 `[n]`，第 2 册（电子书里是裸数字）加方括号为 `[n]`，第 4 册为 `(n)`；角标不落在行首，点击跳到注释、注释处可回跳', 'markers')]
    lines += ['',
              '- 电子书里用 `<i>`、斜体 span 标出的外文和书刊名，用思源宋体的西文斜体（Noto Serif Italic）；楷体强调（第 1 本的说明页、第 3 本的问答等）用楷体（霞鹜文楷）；',
              '- 标题里的强制换行去掉，序号与标题之间统一为一个不会被吞掉的空隙（“第一章　……”“一　……”“附录一　……”）；',
              '- 第 4 本注释前电子书里的一行虚线（20 个破折号，共 9 处）是装饰，不排；',
              '- 第 1 本的“本书引用……已获其允许”说明页和献词页保持原文原序，献词居中排；',
              '- 正文里的空行（电子书里的空段落）改为“下一段前空一行”，页首自动吞掉、页底自动收缩，不会留下末行基线不齐的页。', '']
    lines += ['## 5. 保持原样的', '',
              '- 原书里的明显笔误不改（如有疑问保持原样，数字和专名尤其如此）；',
              '- 图里的文字（各表、曲线图上的数字）是图像，无法改动，保持原图；',
              '- 版权页按电子书原文排，不改。', '']
    with open(os.path.join(DOC, 'dispositions.md'), 'w', encoding='utf8') as f:
        f.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    import json
    b = sys.argv[1]
    if b == '--write':
        root = sys.argv[2]
        facts = [json.load(open(os.path.join(root, bk.CFG[k]['scratch'], 'out', 'facts.json'), encoding='utf8')) for k in sorted(bk.CFG)]
        os.makedirs(DOC, exist_ok=True)
        write(facts)
        print('written to', DOC)
    else:
        f = book_facts(int(b))
        os.makedirs(os.path.join(style.SCRATCH, 'out'), exist_ok=True)
        json.dump(f, open(os.path.join(style.SCRATCH, 'out', 'facts.json'), 'w', encoding='utf8'), ensure_ascii=False)
        print(f)
