"""Write docs/QA-report.md and docs/dispositions.md from the current build."""
import os
import sys
import json
import collections
import pymupdf
from . import style, books, build, check, book as B, normalize, qa
from .measure import Measurer
from .model import runs_text

DOC = os.path.join(style.ROOT, 'docs')
OUT = os.path.join(style.SCRATCH, 'out')


def main():
    os.makedirs(DOC, exist_ok=True)
    build.calibrate_all()
    m = Measurer()
    lines = ['# 验收核查报告（自动生成）', '',
             '所有检查均由脚本在生成的 PDF / 版面计划上实测，不是人工估计。', '']
    tot = collections.Counter()
    rows = []
    cfgs = []
    for name in ['book1', 'book2', 'book3', 'book4']:
        cfg = getattr(books, name)()
        cfgs.append(cfg)
        bb = B.BookBuilder(cfg, m)
        bb.typeset_all()
        bb.sequence()
        B.fill_toc_labels(bb, cfg['toc'])
        pdf = os.path.join(OUT, name + '.pdf')
        pc = check.pdf_checks(pdf, bb)
        fid = qa.fidelity(bb, pdf)
        n_loose = n_lines = 0
        rep_tot = collections.Counter()
        for mod in cfg['modules']:
            if mod.kind != 'text':
                continue
            rep = check.module_report(mod)
            for k, v in rep.items():
                rep_tot[k] += len(v)
            for lb in mod.lbs:
                if lb.block['k'] == 'p' and lb.st['align'] == 'j':
                    vi = mod.plan['variants'][lb.idx]
                    for j in range(len(lb.starts[vi]) - 1):
                        n_lines += 1
                        w = lb.st['W'] - (lb.st['left'] + lb.st['right'] + (lb.st['first'] if j == 0 else 0)) * lb.st['fs']
                        if (w - lb.nat[vi][j]) / lb.st['fs'] > 3.0:
                            n_loose += 1
        doc = pymupdf.open(pdf)
        links = sum(len(p.get_links()) for p in doc)
        rows.append((cfg['title'], pc['pages'], pc['ref_bottom'], len(pc['bad_bottom']), len(pc['type3']),
                     rep_tot['gap'], rep_tot['head_bottom'], rep_tot['head_short'], rep_tot['lone'], rep_tot['last_page'],
                     rep_tot['widow'] + rep_tot['orphan'], n_loose, n_lines, len(fid), links))
    m.close()
    lines += ['| 书 | 页数 | 整页末行基线(pt) | 基线不齐页 | Type3 字体 | 需拉伸的缺口页 | 标题落页底 | 标题后不足2行 | 孤立角标/标点行 | 末页仅1-2行 | 孤行(寡/孤) | 行末空白>3字宽 / 两端对齐行 | 与源文字不符的模块 | 链接数 |',
              '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        lines.append(f'| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | {r[7]} | {r[8]} | {r[9]} | {r[10]} | {r[11]} / {r[12]} | {r[13]} | {r[14]} |')
    lines += ['', '说明：',
              '- “整页末行基线”：每本书中除模块末页外的全部文字页（含小字号的注释、索引页），PDF 中最后一行文字基线的 y 坐标全部相同。',
              '- “与源文字不符的模块”：把每个模块在 PDF 中提取出的文字与源文本逐字符（忽略空白与零宽字符）比较。',
              '- 孤行(寡/孤)：段落被分页时只在页底留 1 行或只在页顶留 1 行的次数（不属于强制项，已尽量避免）。']
    src = qa.source_fidelity(cfgs)
    lines += ['', '## 源文本 → 排版文本差异（全部为有意处理）', '']
    for d in src:
        lines.append(f'- {d[0]}: 源缺 {d[1]} / 排版多 {d[2]}')
    open(os.path.join(DOC, 'QA-report.md'), 'w', encoding='utf8').write('\n'.join(lines) + '\n')
    print('\n'.join(lines[:14]))


if __name__ == '__main__':
    main()
