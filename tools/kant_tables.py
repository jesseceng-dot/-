"""第 1 册里用空格（NBSP）排成四象限的几张表（无的划分表、谬误推理表、自由范畴表）：
电子书里是若干行居中文字，列对齐全靠空格；这里按原文重建为“书后插图”里的小表（矢量文字），正文处只留“见书后插图N”。
"""
import html as _html
from .model import run, runs_html
from . import style

# id -> dict(title=[lines], q=[q1, q2, q3, q4], part, first, last)   (first/last = item indexes in kant_extract.items(part))
# every line is a list of runs (so that note markers stay linked)


def L(t, **kw):
    return [run(t, **kw)]


TABLES = {
    'table:12:512': dict(part=12, first=512, last=522, title=[L('无'), L('作为')],
                         q=[[L('没有对象的空概念'), L('ens rationis［理性的存在者］')],
                            [L('一个概念的空对象'), L('nihil privativum［阙如的无］')],
                            [L('没有对象的空直观'), L('ens imaginarium［想象的存在者］')],
                            [L('没有概念的空对象'), L('nihil negativum［否定性的无］')]]),
    'table:12:600': dict(part=12, first=600, last=607, title=[],
                         q=[[L('灵魂是实体'), [run('⁠(115)', s=1, h='part0012#m115', a='part0012#w115')]],
                            [L('灵魂在其质上是单纯的')],
                            [L('灵魂就其所在的不同时间'), L('而言是数目上同一的，亦即'), L('单一性（非复多性）')],
                            [L('灵魂处于同空间中可能的对象的关系中'), [run('⁠(116)', s=1, h='part0012#m116', a='part0012#w116')]]]),
    'table:12:744': dict(part=12, first=744, last=761, title=[],
                         q=[[L('关系的无条件的统一性'), L('亦即'), L('自身不是依存的'), L('而是'), L('自存的')],
                            [L('质的无条件的统一性'), L('亦即'), L('不是实在的整体'), L('而是'), L('单纯的'),
                             [run('⁠(125)', s=1, h='part0012#m125', a='part0012#w125')]],
                            [L('时间中的复多性中的无条件的统一性'), L('亦即'), L('不是在不同的时间里数目上不同的'), L('而是'), L('作为同一个主体')],
                            [L('空间中的存在的无条件的统一性'), L('亦即不是作为对它外面的诸多事物的意识'), L('而是'),
                             L('仅仅对它自己的存在的意识'), L('对其他事物的意识纯然是对它的表象的意识')]]),
    'table:16:114': dict(part=16, first=114, last=132, title=[L('善与恶的概念方面的自由范畴表')],
                         q=[[L('量', b=1), L('主观的、按照准则的（个人的意志意见）'), L('客观的、按照原则的（规范）'), L('先天地既是客观的又是主观的自由原则（法则）')],
                            [L('质', b=1), L('践行的实践规则（praeceptivae［指令性的］）'), L('舍弃的实践规则（prohibitivae［禁止性的］）'), L('例外的实践规则（exceptivae［除外性的］）')],
                            [L('关系', b=1), L('与人格的关系'), L('与个人状态的关系'), L('个人与其他个人的状态的交互关系')],
                            [L('模态', b=1), L('允许的事情和不允许的事情'), L('义务和违背义务的事情'), L('完全的义务和不完全的义务')]]),
}
FIRST = {(t['part'], t['first']): (k, t['last']) for k, t in TABLES.items()}
FS, LH = 9.5, 13.5
COLW = style.TEXT_W / 2 - 10


def _w(ch):
    return FS if ord(ch) > 0x2000 else FS * 0.52


def _lines(runs, width):
    n, cur = 1, 0.0
    for r in runs:
        for ch in r['t']:
            cur += _w(ch)
            if cur > width:
                n += 1
                cur = _w(ch)
    return n


def _q_h(q, width):
    return sum(_lines(l, width) for l in q) * LH + 6


def size(tid):
    t = TABLES[tid]
    w = style.TEXT_W
    h = sum(_lines(l, w) for l in t['title']) * LH + (6 if t['title'] else 0)
    h += _q_h(t['q'][0], w) + max(_q_h(t['q'][1], COLW), _q_h(t['q'][2], COLW)) + _q_h(t['q'][3], w) + 4 * 15
    return w, h


def anchors(tid):
    return [r['a'] for q in TABLES[tid]['q'] for l in q for r in l if r.get('a')]


def html(tid):
    """Inner HTML (positioned by the caller): a 2-column grid with the four cells numbered 1–4."""
    t = TABLES[tid]
    w, h = size(tid)

    def cell(no, lines, cls, span=False):
        body = ''.join(f'<div>{runs_html(l)}</div>' for l in lines)
        return (f'<div style="{"grid-column:1/3;" if span else ""}text-align:center;padding:2pt 0 3pt">'
                f'<div style="font-family:HeiTi;font-size:8pt;color:#555">{no}.</div>{body}</div>')
    title = ''.join(f'<div style="text-align:center;font-family:HeiTi;font-weight:700;font-size:10pt">{runs_html(l)}</div>' for l in t['title'])
    q = t['q']
    return (f'<div style="width:{w}pt;font-family:KaiTi,SongBody,serif;font-size:{FS}pt;line-height:{LH}pt">{title}'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;column-gap:20pt;align-items:start">'
            f'{cell(1, q[0], "", True)}{cell(2, q[1], "")}{cell(3, q[2], "")}{cell(4, q[3], "", True)}</div></div>')
