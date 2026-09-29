"""Acceptance numbers for the four trade books (16开).
    BOOK_SCRATCH=<dir> BOOK_GEOM=k16 python -m tools.bk_report 2        one book; writes <scratch>/out/report.json
    python -m tools.bk_report --write <scratch-root>                    merge the four report.json files into docs/16k/QA-report.md
"""
import os
import re
import sys
import json
import collections
import pymupdf
from . import style, build, check, book as B, qa, bk, bk_extract as BE
from .measure import Measurer
from .model import runs_text

IGN = qa.IGN


def counter(t):
    return collections.Counter(c for c in t if c not in IGN)


def source_counter(b):
    """Characters of the source parts of book b that end up in the book (contents / copyright / cover pages excluded)."""
    C = bk.CFG[b]
    parts = [n for n, _ in C['front']]
    for x in C['body']:
        parts += list(x) if isinstance(x, (list, tuple)) else [x]
    parts += [x[0] if isinstance(x, tuple) else x for x in C['back']] + list(C.get('endnotes', ()))
    c = collections.Counter()
    for n in parts:
        for it in BE.items(bk.P(n)):
            if it['k'] == 'img':
                continue
            if set(it['cls'].split()) & set(C.get('cls_skip', ())) or ''.join(r['t'] for r in it.get('runs', [])).strip() in C.get('skip_text', ()):
                continue
            if it['k'] == 'table':
                for row in it['rows']:
                    for cell in row:
                        for r in cell:
                            if not r.get('i'):
                                c += counter(r['t'].replace(' ', ''))
                continue
            if re.fullmatch(r'[—－-]{6,}', ''.join(r['t'] for r in it['runs']).strip()):
                continue                                    # the dashed rule above the notes of book 4 (dropped on purpose)
            for r in it['runs']:
                if r.get('i'):
                    continue
                c += counter(r['t'].replace(' ', ''))
    return c


def block_counter(cfg):
    c = collections.Counter()
    for m in cfg['modules']:
        if m.kind == 'text' and m.mid not in ('toc', 'copyright'):
            for b in m.blocks:
                if b['k'] in ('img', 'space'):
                    continue
                if b.get('id', '').endswith('#top') and b['style'] == 'h1' and runs_text(b['runs']) == '注　释':
                    continue
                if b.get('style') == 'idxhead' and m.mid.startswith('notes'):
                    continue
                c += counter(runs_text(b['runs']).replace('⁠', '').replace(' ', ''))
        elif m.kind == 'page' and hasattr(m, 'lines'):
            for t in m.lines:
                c += counter(t.replace('⁠', '').replace(' ', ''))
    return c


START = set('，。、；：！？）》」』”’】〕')
END = set('（《「『“‘【〔')


def kinsoku(cfg):
    bad, n = [], 0
    for mod in cfg['modules']:
        if mod.kind != 'text' or not mod.lbs:
            continue
        for lb in mod.lbs:
            if lb.block['k'] != 'p':
                continue
            vi = mod.plan['variants'][lb.idx]
            text = runs_text(lb.block['runs'])
            for s in lb.starts[vi][1:]:
                n += 1
                if text[s] in START or text[s - 1] in END:
                    bad.append((mod.mid, text[max(0, s - 6):s + 4]))
    return bad, n


def book(b, m):
    cfg = bk.book(b)
    bb = B.BookBuilder(cfg, m)
    bb.typeset_all()
    bb.sequence()
    B.fill_toc_labels(bb, cfg['toc'])
    pdf = os.path.join(style.SCRATCH, 'out', f'b{b}.pdf')
    pc = check.pdf_checks(pdf, bb)
    fid = qa.fidelity(bb, pdf)
    rep_tot = collections.Counter()
    n_loose = n_lines = 0
    for mod in cfg['modules']:
        if mod.kind != 'text':
            continue
        rep = check.module_report(mod)
        for k, val in rep.items():
            rep_tot[k] += len(val)
        for lb in mod.lbs:
            if lb.block['k'] == 'p' and lb.st['align'] == 'j':
                vi = mod.plan['variants'][lb.idx]
                for j in range(len(lb.starts[vi]) - 1):
                    n_lines += 1
                    w = lb.st['W'] - (lb.st['left'] + lb.st['right'] + (lb.st['first'] if j == 0 else 0)) * lb.st['fs']
                    if (w - lb.nat[vi][j]) / lb.st['fs'] > 3.0:
                        n_loose += 1
    kin, nkin = kinsoku(cfg)
    doc = pymupdf.open(pdf)
    links = sum(len(p.get_links()) for p in doc)
    sizes = {(round(p.rect.width, 2), round(p.rect.height, 2)) for p in doc}
    src = source_counter(b)
    have = block_counter(cfg)
    miss, extra = src - have, have - src
    fonts = collections.Counter()
    for p in doc:
        for pg in p.get_text('dict')['blocks']:
            for l in pg.get('lines', []):
                for s in l['spans']:
                    if s['text'].strip():
                        fonts[round(s['size'], 1)] += len(s['text'])
    return dict(b=b, title=bk.TITLES[b], pages=len(doc), sizes=sorted(sizes), links=links,
                ref_bottom=pc['ref_bottom'], bad_bottom=len(pc['bad_bottom']), type3=len(pc['type3']),
                rep=dict(rep_tot), loose=n_loose, lines=n_lines, kin=len(kin), nkin=nkin, fid=len(fid), fid_head=[str(x)[:120] for x in fid[:4]],
                miss=dict(miss.most_common(12)), n_miss=sum(miss.values()), extra=dict(extra.most_common(12)), n_extra=sum(extra.values()),
                body_size=fonts.most_common(1)[0][0])


DOC = os.path.join(style.ROOT, 'docs', '16k')


def write_markdown(root):
    rows = [json.load(open(os.path.join(root, bk.CFG[b]['scratch'], 'out', 'report.json'), encoding='utf8')) for b in sorted(bk.CFG)]
    os.makedirs(DOC, exist_ok=True)
    lines = ['# 四本 16 开书：验收核查报告（自动生成）', '',
             '所有数字由脚本在生成的 PDF 与版面计划上实测（`python -m tools.bk_report`），不是人工估计。', '',
             '| 书 | 页数 | 页面尺寸(pt) | 正文字号(pt) | 整页末行基线(pt) | 基线不齐页 | Type3 字体 | 补空行的页 | 标题落页底 | 标题后不足2行 | 孤立角标/标点行 | 末页仅1–2行 | 孤行(寡/孤) | 行末空白>3字宽 / 两端对齐行 | 行首行尾禁则违规 / 行数 | 与源文字不符的模块 | 链接数 |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        rep = r['rep']
        size = ' × '.join(f'{x:g}' for x in r['sizes'][0]) + ('' if len(r['sizes']) == 1 else f'（另有 {len(r["sizes"]) - 1} 种）')
        lines.append(f"| {r['b']} {r['title']} | {r['pages']} | {size} | {r['body_size']} | {r['ref_bottom']} | {r['bad_bottom']} | {r['type3']} | {rep.get('gap', 0)} | "
                     f"{rep.get('head_bottom', 0)} | {rep.get('head_short', 0)} | {rep.get('lone', 0)} | {rep.get('last_page', 0)} | {rep.get('widow', 0) + rep.get('orphan', 0)} | "
                     f"{r['loose']} / {r['lines']} | {r['kin']} / {r['nkin']} | {r['fid']} | {r['links']} |")
    lines += ['', '说明：',
              '- 页面：170 × 240 mm（16开）= 481.89 × 680.31 pt，与所附样张 PDF 的页面框相同；Chromium 打印时把页面取整为 481.92 × 679.92 pt，生成后逐页把页面框改回精确值（上边不动）；',
              '- “整页末行基线”：每本中除模块末页外的全部文字页（含小字号的注释页），PDF 中最后一行文字基线的 y 坐标全部相同；',
              '- “补空行的页”：求解器在允许的字距微调范围内也凑不满的页。这样的页不拉伸行距，而是把缺的 1–2 行空白加在该页最后一个标题的上方，末行基线仍落在同一位置；',
              '- “与源文字不符的模块”：把每个模块在 PDF 中提取出的文字与排版文本逐字符比较（行末外文词的连字符 “-” 是排版时加的，属预期差异）；',
              '- 行首行尾禁则：求解后的每一行首字不是句读/右括号，行尾不是左括号（由 Chromium 的换行规则保证，这里逐行复核）；',
              '- “正文字号”是全书出现字数最多的字号：正文一律 10.5 pt；第 1 本大量摘录巴菲特致股东的信，引文（缩进两字）是 10 pt，字数比正文还多，所以最常见字号是 10.0；',
              '- 第 4 本的 1 页“基线不齐”是附录一年表的最后一页：年表后面紧接一张整页曲线图，图（留在原位，不缩小不拆分）放不下，这一页在表格结束处提前收尾；',
              '- 第 4 本的 5 个“补空行的页”都在附录一年表里（每行是一个不能拆开的表格行，凑不满整页时行距略微放开，末行基线不变）；',
              '- 含整页表格图的附录页（第 1 本附录一至四）本身不是文字页，不参与末行基线比较。', '',
              '## 源文本 → 排版文本的字符差异', '',
              '“源缺”是指电子书里有、排版文本里没有的字符（都是有意的改动：注释角标的方括号/圆括号统一、半角标点改全角、多余空格、行内小图转写等），'
              '“排版多”是排版文本里新增的字符（角标括号、“见书后插图N”提示等）。逐类说明见 `dispositions.md`。', '']
    for r in rows:
        lines.append(f"- 第{r['b']}册《{r['title']}》：源缺 {r['n_miss']}（{r['miss']}）；排版多 {r['n_extra']}（{r['extra']}）")
    with open(os.path.join(DOC, 'QA-report.md'), 'w', encoding='utf8') as f:
        f.write('\n'.join(lines) + '\n')


def main(b):
    build.calibrate_all()
    m = Measurer()
    r = book(b, m)
    m.close()
    rep = r['rep']
    print(f"book {b} {r['title']}: pages {r['pages']} sizes {r['sizes']} body {r['body_size']} bottom {r['ref_bottom']} bad_bottom {r['bad_bottom']} type3 {r['type3']} "
          f"gap {rep.get('gap')} head_bottom {rep.get('head_bottom')} head_short {rep.get('head_short')} lone {rep.get('lone')} last {rep.get('last_page')} "
          f"widow/orphan {rep.get('widow', 0) + rep.get('orphan', 0)} loose {r['loose']}/{r['lines']} kinsoku {r['kin']}/{r['nkin']} fid {r['fid']} links {r['links']}")
    print('    source-only chars:', r['miss'], r['n_miss'])
    print('    typeset-only chars:', r['extra'], r['n_extra'])
    for x in r['fid_head']:
        print('    fidelity:', x)
    json.dump(r, open(os.path.join(style.SCRATCH, 'out', 'report.json'), 'w', encoding='utf8'), ensure_ascii=False)
    return r


if __name__ == '__main__':
    if sys.argv[1] == '--write':
        write_markdown(sys.argv[2])
    else:
        main(int(sys.argv[1]))
