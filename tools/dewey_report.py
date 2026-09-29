"""Acceptance numbers for the Dewey volumes (writes docs/dewey/QA-report.md) and the text difference source -> typeset."""
import os
import sys
import collections
import pymupdf
from . import style, build, check, book as B, qa, dewey, dewey_extract as DE
from .measure import Measurer
from .model import runs_text

IGN = qa.IGN


def counter(t):
    return collections.Counter(c for c in t if c not in IGN)


def source_counter(v):
    """Characters of the source parts of volume v that end up in the book (contents / copyright / cover pages excluded)."""
    V = dewey.VOL[v]
    parts = list(V['front']) + list(V['body']) + list(V['back'])
    c = collections.Counter()
    for n in parts:
        for it in DE.items(dewey.P(n)):
            if it['k'] == 'img':
                continue
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
                c += counter(runs_text(b['runs']).replace('⁠', ''))
        elif m.kind == 'page' and hasattr(m, 'lines'):
            for t in m.lines:
                c += counter(t.replace('⁠', ''))
    return c


START = set('，。、；：！？）》」』”’】〕')
END = set('（《「『“‘【〔')


def kinsoku(cfg):
    """Lines (of the solved plans) that start with a closing mark or end with an opening mark."""
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


def volume(v, m):
    cfg = dewey.book(v)
    bb = B.BookBuilder(cfg, m)
    bb.typeset_all()
    bb.sequence()
    B.fill_toc_labels(bb, cfg['toc'])
    pdf = os.path.join(style.SCRATCH, 'out', f'd{v}.pdf')
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
    src = source_counter(v)
    have = block_counter(cfg)
    miss, extra = src - have, have - src
    return dict(v=v, cfg=cfg, pc=pc, fid=fid, rep=rep_tot, loose=n_loose, lines=n_lines, links=links,
                miss=miss, extra=extra, pages=len(doc), kin=kin, nkin=nkin)


DOC = os.path.join(style.ROOT, 'docs', 'dewey')


def write_markdown(rows):
    os.makedirs(DOC, exist_ok=True)
    lines = ['# 杜威著作精选：验收核查报告（自动生成）', '',
             '所有数字由脚本在生成的 PDF 与版面计划上实测（`python -m tools.dewey_report`），不是人工估计。', '',
             '| 册 | 页数 | 整页末行基线(pt) | 基线不齐页 | Type3 字体 | 补空行的页 | 标题落页底 | 标题后不足2行 | 孤立角标/标点行 | 末页仅1–2行 | 孤行(寡/孤) | 行末空白>3字宽 / 两端对齐行 | 行首行尾禁则违规 / 行数 | 与源文字不符的模块 | 链接数 |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        pc, rep = r['pc'], r['rep']
        lines.append(f"| {r['v']} {dewey.TITLES[r['v']]} | {r['pages']} | {pc['ref_bottom']} | {len(pc['bad_bottom'])} | {len(pc['type3'])} | {rep['gap']} | "
                     f"{rep['head_bottom']} | {rep['head_short']} | {rep['lone']} | {rep['last_page']} | {rep['widow'] + rep['orphan']} | "
                     f"{r['loose']} / {r['lines']} | {len(r['kin'])} / {r['nkin']} | {len(r['fid'])} | {r['links']} |")
    lines += ['', '说明：',
              '- “整页末行基线”：每册中除模块末页外的全部文字页（含小字号的注释页），PDF 中最后一行文字基线的 y 坐标全部相同；',
              '- “补空行的页”：求解器在允许的字距微调范围内也凑不满的页。这样的页不拉伸行距，而是把缺的 1–2 行空白加在该页最后一个标题的上方，末行基线仍落在同一位置；',
              '- “与源文字不符的模块”：把每个模块在 PDF 中提取出的文字与排版文本逐字符比较（行末外文词的连字符 “-” 是排版时加的，属预期差异）；',
              '- 行首行尾禁则：求解后的每一行首字不是句读/右括号，行尾不是左括号（由 Chromium 的换行规则保证，这里逐行复核）。', '',
              '## 源文本 → 排版文本的字符差异', '',
              '每册的“源缺”是指电子书里有、排版文本里没有的字符（都是有意的改动：私用区字符还原为 æ ä ö、直撇号改为 ’、拉丁词后多余的空格、行内小图的转写等），'
              '“排版多”是排版文本里新增的字符（还原后的字符、行内小图转写出的希腊文、书后插图的提示文字“见书后插图N”等）。逐类说明见 `dispositions.md`。', '']
    for r in rows:
        lines.append(f"- 第{r['v']}册：源缺 {sum(r['miss'].values())}（{dict(r['miss'].most_common(8))}）；排版多 {sum(r['extra'].values())}（{dict(r['extra'].most_common(8))}）")
    with open(os.path.join(DOC, 'QA-report.md'), 'w', encoding='utf8') as f:
        f.write('\n'.join(lines) + '\n')


def main(vols=None):
    build.calibrate_all()
    m = Measurer()
    rows = []
    for v in vols or range(1, 12):
        r = volume(v, m)
        rows.append(r)
        pc, rep = r['pc'], r['rep']
        print(f"vol {v} {dewey.TITLES[v]}: pages {r['pages']} bottom {pc['ref_bottom']} bad_bottom {len(pc['bad_bottom'])} type3 {len(pc['type3'])} "
              f"gap {rep['gap']} head_bottom {rep['head_bottom']} head_short {rep['head_short']} lone {rep['lone']} last {rep['last_page']} "
              f"widow/orphan {rep['widow'] + rep['orphan']} loose {r['loose']}/{r['lines']} kinsoku {len(r['kin'])}/{r['nkin']} fid {len(r['fid'])} links {r['links']}")
        print('    source-only chars:', dict(r['miss'].most_common(12)), sum(r['miss'].values()))
        print('    typeset-only chars:', dict(r['extra'].most_common(12)), sum(r['extra'].values()))
        if r['fid']:
            print('    fidelity:', r['fid'][:4])
    m.close()
    if vols is None:
        write_markdown(rows)
    return rows


if __name__ == '__main__':
    main([int(a) for a in sys.argv[1:]] or None)
