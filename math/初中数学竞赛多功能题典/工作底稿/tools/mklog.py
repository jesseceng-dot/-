"""mklog.py out.md : build the correction log (校勘说明) from the per-page findings."""
import re, sys, os
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = []
for nr, line in enumerate(open(os.path.join(B, 'findings.md'), encoding='utf-8').read().split('\n'), 1):
    if '|' not in line or nr < 3:
        continue
    # columns are separated by " | "; absolute-value bars in the text are not
    cols = [c.strip() for c in line.split(' | ')]
    if len(cols) < 5:
        continue
    rows.append(dict(nr=nr, page=cols[0], id=cols[1], cat=cols[2], desc=' | '.join(cols[3:-1]), act=cols[-1]))

# final decisions where the working notes were provisional or the result differs
FIX = {
 31: ('已改：p104–108、116、117 的 5.12–5.27、5.60、5.63 共 18 题 27 处（含 5.17 方程组、5.26(2)）右竖线改为普通竖线，'
      '与其后的运算符、关系符恢复应有间距；全书其余各处扫描无此问题'),
 47: '改为正体“h”，与数值间加空（同第三节“单位符号”条）',
 74: '改为正体“m”，与数值间加空（同第三节“单位符号”条）',
 118: '句点后补词间空',
 167: '“.”改“,”',
 5: '补结论“证明: 一定存在一个三边长都是有理数的直角三角形, 它的面积等于 A.”（第(2)问为第(1)问之逆，原文只有条件）',
 43: '“…”后补句号；两行合并为一段重排',
 103: '随所在行重排补全：p209、224、227、228、263、273、277、295、302、341；p259、262 两处位于旧补丁白框之下，版面不显示，未动',
 110: '重新断行（首行在“△CYP,”后断开，全段三行）',
 111: ('已重新断行：p156 6.123、p209 10.2、p211 10.10、p214 10.18、p225 11.30、p240 11.79、p270 13.3、p293 15.6、'
       'p299 15.32、p302 15.42、p369 19.71、p424 23.34(1)；p195 9.18 经复核为行末标点的空白半身，字面不出版心，未改；'
       'p41 2.83 行末“+”伸出约 5pt，长分式之间没有合适断点，记录未改'),
 114: 'p269 的 3 个随 12.103 行重排清除；p376 页码以书中页码字体重写（外观不变，文本可检索）',
 124: '次行重排（补“N 为”之间字距）；“边长为 4”的 4 与全书正文数字用法一致，未改',
 137: '两行重排：首行在“AB⊥FD,”后断开；页面外被白框遮住的残留原字与多余的“⊥”一并清除',
 144: '首行重排：改“B′、B″”；旧补丁重复叠印的“射”一并清除',
 147: ('句中误用的改“,”（9.12、11.6、11.68、16.24 等）；句末的在句点后补词间空（11.55、12.28、12.98、14.24、14.42、'
       '14.43、16.13(2)、17.18、17.50）'),
 170: '删去该行（编辑工作备注，不属正文），本页内容随之上移一行，回到各章首题的标准位置。原文：“前 17 个问题, 有所缺漏, 待后续补充完善.”',
 171: '体例记录不改（本组为后补题目，标点体例与全书不同）；其中 17.1“凸n 边形”的缺字距已补',
 172: '补字距（“边长为 1 的”）',
 180: '改为“第三条高的长为整数, 求这条高之长的所有可能值.”（推定，见第四节）',
 182: ('已改：第 344–385 页约 110 处（18.6–18.28、19.2–19.139 各题）删去多余空格，所在行重排；p246、258、275、277、284、'
       '287、300 扫描命中处经复核为字母斜体修正或撇号造成的正常间距，未改'),
 199: '首行重排（补“使得 m”“为 n”字距）；两小问之间补“;”（续行在 p377）',
 200: '清除补丁字形，以书中页码字体重写“371”（外观不变，文本可检索）',
 202: '星号与题文并回题号行，本页下方内容随之上移一行',
 228: ('23.11、23.14 星号与题文并回题号行，下方内容上移一行；23.13 为跨页段落，为不牵动 p418 的版面，题号下移到原题文行，'
       '题文接排（23.12 与 23.13 之间因此多出一行空白）'),
 232: '6.68 已补画；23.22–23.24 无法补（见第五节）；25.6、29.18 删去指向缺图的“如图”',
 260: '合并（“他们的回答有真有假.”成为一段的末行），下方内容上移一行',
 267: '删去两处“如图 (a)”“如图 (b)”',
 272: '12.103 重排时统一为“∼”；12.87、12.93 未重排，记录',
 274: '已改：p119 5.72、p126 6.13、p154 6.117、p173 7.52 改为正体并与数值留空',
 112: ('记录，不改：系原书源码 B^{\'} 产生的二级上标撇号，各题内部一致、不影响辨认；统一须重排约 170 处，'
       '收益小于风险。本次重排的行一律沿用原题撇号形式（如 9.21、12.7、14.24、14.33、15.70、13.22）'),
}
EXTRA = [
 dict(page='p236', id='11.67', cat='多（标点）', desc='“求证：直线 B₂C₁、C₂A₁、A₂B₁, 所构成的三角形上”：逗号把定语与中心语“所构成的三角形”隔开',
      act='删去该逗号'),
 dict(page='p348–349', id='18.23', cat='特殊字符（字体）', desc='“有正整数 x < x′ < y′ < y, x + y = x′ + y′ = n”中后几个“<”“+”“=”为正文字体，不是数学符号，且“<”被拆到下一行行首',
      act='改为统一的数学式，跨页段落重排'),
 dict(page='p398', id='21.14', cat='特殊字符（字体）', desc='“其中 p、q 为正整数, (p,q)=1”的括号和等号为正文字体', act='改为数学式（与“删(1)”同行处理）'),
 dict(page='p331', id='17.18', cat='间距（句点后）', desc='“∠BAC = 2∠ABC.P 是平面上任意一点”句点紧接下句字母', act='句点后补词间空'),
 dict(page='p424', id='23.34(1)', cat='排版（行超出版心）', desc='首行折线名 A₁A₂…A₆ 不能断开，整行伸出版心约 22pt', act='在“例如折线”后断行，首行用字距撑满'),
]
UNCHANGED_PAT = re.compile(r'^(记录[，,]?\s*不改|记录（|记录$|不改；|待定$)')


def status(r):
    if r['nr'] in FIX:
        return FIX[r['nr']]
    return r['act']


def unchanged(r):
    a = status(r)
    return bool(re.match(r'^记录', a)) or a.startswith('不改') or a.startswith('体例记录不改')


def pdf_pages(p):
    return [int(x) for x in re.findall(r'\d+', p)]


def book_page(p):
    ns = pdf_pages(p)
    if not ns:
        return '—'
    return '–'.join(str(n - 5) for n in ns[:2]) if len(ns) > 1 and '/' not in p else '/'.join(str(n - 5) for n in ns[:2])


def key(r):
    ns = pdf_pages(r['page'])
    return (ns[0] if ns else 10 ** 6, r.get('nr', 10 ** 6))


changed = [r for r in rows if not r['page'].startswith('全书') and not unchanged(r)] + EXTRA
changed.sort(key=key)
global_rows = [r for r in rows if r['page'].startswith('全书')]
kept = [r for r in rows if not r['page'].startswith('全书') and unchanged(r)]

esc = lambda s: s.replace('|', '\\|')
out = []
out.append('## 二、逐条修改明细（按页码）\n')
out.append('页码为 PDF 页码，括号内为书上印的页码（PDF 页码减 5）。“问题”一栏引用原书文字，“处理”一栏为本次所作修改。\n')
out.append('| 序号 | 页码 | 题号 | 类别 | 问题 | 处理 |')
out.append('|---|---|---|---|---|---|')
for i, r in enumerate(changed, 1):
    out.append('| %d | %s（%s） | %s | %s | %s | %s |' % (i, r['page'], book_page(r['page']), r['id'], esc(r['cat']), esc(r['desc']), esc(status(r) if 'nr' in r else r['act'])))
out.append('\n## 三、全书性问题的处理\n')
out.append('| 问题 | 情况 | 处理 |')
out.append('|---|---|---|')
for r in global_rows:
    out.append('| %s | %s | %s |' % (esc(r['cat']), esc(r['desc']), esc(status(r))))
out.append('\n## 五、记录而未改动的问题\n')
out.append('| 页码 | 题号 | 类别 | 情况 | 说明 |')
out.append('|---|---|---|---|---|')
for r in sorted(kept, key=key):
    out.append('| %s（%s） | %s | %s | %s | %s |' % (r['page'], book_page(r['page']), r['id'], esc(r['cat']), esc(r['desc']), esc(status(r))))
open(sys.argv[1], 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('changed rows:', len(changed), 'global:', len(global_rows), 'kept:', len(kept))
