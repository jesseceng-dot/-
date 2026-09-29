"""Accuracy report for the conversion of index page numbers (writes docs/index-pages.md).

For every index the report lists how many references were resolved by finding the term in the text (`term`: the term
occurs once, `term1`; or several times and the occurrence whose predicted printed page is closest to the listed page
was taken), by interpolation of the page model (`interp`), as page ranges (`range`), and how many were left as printed
(`none`, letter references).  The page model itself is validated by leaving each calibration anchor out in turn and
comparing the printed page the model predicts for its position with the true one.
"""
import copy
import os
import sys
from . import books, indexmap, style

BOOKS = [('book1', '《小逻辑》'), ('book2', '《黑格尔早期神学著作》'), ('book3', '《精神现象学》'), ('book4', '《哲学史讲演录》')]


def main(out='docs/index-pages.md'):
    rows = []
    for name, title in BOOKS:
        cfg = getattr(books, name)()
        by_id = {m.mid: m for m in cfg['modules']}
        sib = [m for m in cfg['modules'] if m.idxmap]
        for mod in sib:
            mod.src_blocks = copy.deepcopy(mod.blocks)
        for mod in sib:
            refs, resolved = indexmap.resolve_module(mod, by_id.__getitem__, sib)
            st = mod.idx_stats
            v = indexmap.validate(mod, by_id.__getitem__, sib)
            name = mod.title + (f'（{mod.volume}）' if mod.volume else '')
            rows.append((title, name, len(refs), st, v))
            print(title, name, len(refs), st, v, flush=True)
    lines = ['# 索引页码换算：方法与实测精度（自动生成）', '',
             '原书索引条目后的页码是印刷版页码；电子书里没有印刷页码标记，无法直接对应。`tools/indexmap.py` 用索引自身反推：', '',
             '1. 条目词在正文中只出现一次（或出现次数恰等于该条目列出的页数）时，它的位置与印刷页码同时已知，作为“锚点”；',
             '2. 每章用锚点做局部加权回归（并剔除与全书页码增长速率不符的锚点），得到“正文位置 → 印刷页”的对应；',
             '3. 每个页码引用：在正文中找该条目词（子条目短语、外文词优先），取其预测印刷页与所列页码最接近的一处；找不到就取模型对该印刷页预测的位置；',
             '4. 位置所在的 PDF 页即新页码（带内部链接）；页码范围（如 116—30）取两端；同一页重复列出的合并为一个。', '',
             '| 书 | 索引 | 页码引用数 | 正文中找到条目词 | 由模型内插 | 页码范围 | 未换算 | 锚点数 | 留一法：预测印刷页误差≤0.5页 | ≤1页 | ≤2页 |',
             '|---|---|---|---|---|---|---|---|---|---|---|']
    for title, name, n, st, v in rows:
        found = st.get('term', 0) + st.get('term1', 0)
        anch = sum(st.get('anchors', {}).values())
        f = lambda k: f'{v[k] * 100:.0f}%' if v.get('n') else '—'
        lines.append(f'| {title} | {name} | {n} | {found} | {st.get("interp", 0)} | {st.get("range", 0)} | '
                     f'{st.get("none", 0) + st.get("skip", 0)} | {anch} | {f("within_half")} | {f("within_one")} | {f("within_two")} |')
    lines += ['', '说明：', '- “留一法”一行是对页码模型的检验：把每个锚点依次拿掉，看模型对它的位置预测的印刷页与真值差多少（1 个印刷页约 700 字，与 1 个 PDF 页大小相当）。',
              '- “未换算”包括《哲学史讲演录》第四卷人名索引里“信14”这类指向黑格尔书信集页码的引用（不在本书正文里），保持原样。',
              '- 逐条换算结果见 `docs/index-page-map/*.csv`（原页码 → 本 PDF 页码 → 方法）。']
    with open(out, 'w', encoding='utf8') as fh:
        fh.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
