"""Corrections list of one book: the proof-reading corrections of tools/bk_fixes.py with their notes, by chapter.
    BOOK_SCRATCH=<dir> BOOK_GEOM=k16 python -m tools.bk_errata 16          -> docs/16k/errata/<nn>-<title>.md
"""
import os
import re
import sys
import collections
from . import style, bk, bk_extract as BE, bk_fixes as BF

DOC = os.path.join(style.ROOT, 'docs', '16k', 'errata')


GROUPS = [                      # summary groups of the note labels
    ('错字', ('错字', '错误')),
    ('漏字', ('漏字',)),
    ('多字', ('多字',)),
    ('标点', ('标点',)),
    ('用字、用词规范', ('用字', '用词', '量词', '数字用法', '数字用法统一')),
    ('排版与符号', ('排版', '符号', '符号统一', '公式')),
    ('错译、语序与术语（据英文原著）', ('错译', '语序', '语句', '术语')),
    ('事实性错误', ('事实性错误', '事实', '史实')),
    ('人名、译名', ('人名', '译名', '译名统一', '书名统一')),
    ('书名、篇名与书目', ('书名', '篇名', '书目', '书目格式', '引文页码')),
    ('外文核对（拉丁、法、德、俄文与学名）', ('原文核对', '拉丁文', '法文', '学名')),
]


def category(note):
    """The label of a note ('错字：…' -> '错字'; a note of a label only -> that label); several labels joined by '/'
    count under the first."""
    m = re.match(r'([^：:（(，]{1,8})[：:]', note)
    return (m.group(1) if m else note if len(note) <= 8 else '其他').split('/')[0]


def group(label):
    return next((g for g, labels in GROUPS if label in labels), '其他')


def code(s):
    """A table cell showing the exact characters (spaces and punctuation matter); a string of white space only is
    named by its code points."""
    s = str(s)
    if s and not s.strip():
        return ' '.join(f'U+{ord(c):04X}' for c in s)
    s = s.replace('\n', '⏎').replace('|', '\\|')
    tick = '``' if '`' in s else '`'
    pad = ' ' if s.startswith('`') or s.endswith('`') else ''
    return f'{tick}{pad}{s}{pad}{tick}' if s else '（空）'


def describe(f):
    """(where, old, new) of one correction."""
    kind = f[1]
    if not isinstance(kind, str):                                  # a regular expression
        return '', code('/' + kind.pattern + '/'), code(f[2])
    if kind not in BF.SPECIAL:
        return '', code(kind), code(f[2])
    if kind == 'HEAD':
        return '', code(f[2] + '…'), f'排为第 {f[3]} 级标题'
    if kind == 'PARA':
        return '', code(f[2] + '…' + f[3]), f'自 {code(f[3])} 起另起一段' + (f'（{code(f[4])} 排为说话人）' if len(f) == 6 else '')
    if kind == 'JOIN':
        return '', code('…' + f[2]) + ' ⏎ ' + code(f[3] + '…'), '两段合为一段'
    if kind == 'CELL':
        return f'表格（首格为 {code(f[2])} 的一行）第 {f[3] + 1} 列', code(f[4]), code(f[5])
    return '', ' '.join(code(x) for x in f[2:-1] if isinstance(x, (str, int))), kind


def part_titles(b):
    """Part number -> title of the chapter (module) it belongs to."""
    C = bk.CFG[b]
    cfg = bk.book(b)
    title = {m.mid: m.title for m in cfg['modules']}
    out = {}
    groups = [n for n, _ in C['front']] + list(C['body']) + [x[0] if isinstance(x, tuple) else x for x in C['back']]
    for g in groups:
        ns = list(g) if isinstance(g, (list, tuple)) else [g]
        t = title.get(bk.P(ns[0]), '')
        for n in ns:
            out[n] = t
    order = [n for g in groups for n in (list(g) if isinstance(g, (list, tuple)) else [g])]
    if C.get('copyright') is not None:
        out[C['copyright']] = '版权页'
        order.insert(0, C['copyright'])
    return out, order


def parts_of(spec, order):
    if spec == '*':
        return None
    if isinstance(spec, int):
        return [spec]
    return [n for n in order if n in set(spec)] or list(spec)


def write(b):
    C = bk.CFG[b]
    fixes = BF.FIXES.get(C['scratch'], [])
    titles, order = part_titles(b)
    rank = {n: i for i, n in enumerate(order)}
    cats = collections.Counter(category(f[-1]) for f in fixes)
    grouped = collections.Counter()
    labels = collections.defaultdict(list)
    for k, v in cats.most_common():
        grouped[group(k)] += v
        labels[group(k)].append(f'{k} {v}')
    groups = collections.OrderedDict()
    for f in sorted(fixes, key=lambda f: -1 if f[0] == '*' else min(rank.get(n, 999) for n in parts_of(f[0], order))):
        ps = parts_of(f[0], order)
        key = '全书（各章通用的统一改法）' if ps is None else '、'.join(dict.fromkeys(titles.get(n, f'part{n:04d}') for n in ps))
        groups.setdefault(key, []).append(f)
    BE._fixes('part0000')
    unused = [f for f in (BE._FIX or []) if not BE.FIX_USED.get(id(f))]
    lines = [f'# 《{C["title"]}》勘误表', '']
    if C.get('errata_note'):
        lines += [C['errata_note'], '']
    lines += [f'{"" if C.get("errata_note") else "通读全书时"}改正的问题共 **{len(fixes)}** 条（每条是 `tools/bk_fixes.py` 里的一条改正规则，抽取电子书文字时应用；'
             f'生成时逐条核对：{"全部规则都在原文中找到并已应用" if not unused else f"{len(unused)} 条未匹配"}）。'
             '“原文”是电子书里的文字（为便于定位，常连同前后几个字一起列出），“改为”是 PDF 里的文字；“全书”一节的规则对每一章都适用。'
             '核对依据：上下文与全书用字、用词的一致性，英文原著（错译、事实、人名、书目），以及常识与工具书（史实、学名、外文）。', '',
             '## 分类统计', '', '| 类别 | 条数 | 其中（按说明里的标签） |', '|---|---|---|']
    lines += [f'| {g} | {grouped[g]} | {"、".join(labels[g])} |' for g in [g for g, _ in GROUPS] + ['其他'] if grouped[g]]
    lines += [f'| 合计 | {len(fixes)} | |']
    lines += ['']
    for key, fs in groups.items():
        lines += [f'## {key}', '', '| # | 原文 | 改为 | 说明 |', '|---|---|---|---|']
        for i, f in enumerate(fs, 1):
            where, old, new = describe(f)
            note = f[-1].replace('|', '\\|')
            lines.append(f'| {i} | {(where + "：") if where else ""}{old} | {new} | {note} |')
        lines.append('')
    os.makedirs(DOC, exist_ok=True)
    out = os.path.join(DOC, f'{b:02d}-{C["file"]}.md')
    with open(out, 'w', encoding='utf8') as fh:
        fh.write('\n'.join(lines) + '\n')
    return out, len(fixes), len(unused)


if __name__ == '__main__':
    print(*write(int(sys.argv[1])))
