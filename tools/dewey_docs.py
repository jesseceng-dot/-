"""Generate docs/dewey/*.md (dispositions, inline-image transcriptions) from the data the conversion uses."""
import os
import re
import collections
from . import style, dewey, dewey_extract as DE, dewey_text as DT

DOC = os.path.join(style.ROOT, 'docs', 'dewey')


def table(rows, head):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return out


INLINE_NOTES = {
    'image01826.jpeg': ('第 4 册 第 80 部件（海伦·凯勒的引文：“比如 ⟨鸟⟩ 蛋紫色光亮的外壳”）', '𮭥 U+2EB65（简化的“䳍”，共＋鸟）',
                        '图里是简化的“鸟”旁的一个生僻字。把 Noto Serif/Sans CJK 的全部汉字逐个与图比对，构件相同的只有 䳍（U+4CCD，共＋鳥）；'
                        '䳍 是䳍形目（tinamou，南美的一类鸟）的用字，这类鸟的蛋壳有紫色的光泽，与引文的“蛋紫色光亮的外壳”吻合；'
                        '简化字形是 𮭥（Unicode 扩展 F 区），与图一致，所以用它。思源宋体没有这个字，`tools/fonts.py` 的 `compose_tinamou` 用宋体自己的笔画（共、鸡的鸟旁）合成'),
    'image01835.jpeg': ('第 6 册 第 116 部件（“4、+、√−1 （四、加号、负一的平方根）”）', '√ + 上横线的 −1', '根号下带横线，排成“√”加上方有横线的“−1”'),
    'image01843.jpeg': ('第 9 册 第 188 部件（亚里士多德的“友谊”）', 'φιλία', ''),
    'image01844.jpeg': ('第 9 册 第 188 部件（“融洽”）', 'ὁμόνοια', '图上两个 ο 的重音符号可见，首字母的气符与重音叠在一起，按标准写法补全'),
    'image01845.jpeg': ('第 9 册 第 188 部件（大度 high-mindedness）', 'μεγαλοψυχία', ''),
    'image01846.jpeg': ('第 9 册 第 192 部件（目的论 teleological）', 'τέλος', ''),
    'image01847.jpeg': ('第 9 册 第 193 部件（快乐主义 Hedonism）', 'ἡδονή', ''),
    'image01848.jpeg': ('第 9 册 第 193 部件（禁欲主义 Asceticism）', 'ἄσκησις', ''),
    'image01854.jpeg': ('第 10 册 第 219 部件（培根的“假相”）', 'εἴδωλα', ''),
    'image01855.jpeg': ('第 10 册 第 226 部件（认识 / 知道）', 'γνῶναι', ''),
    'image01856.jpeg': ('第 10 册 第 226 部件', 'εἰδέναι', ''),
    'image01857.jpeg': ('第 10 册 第 226 部件（法文）', 'connaître', ''),
    'image01858.jpeg': ('第 10 册 第 233 部件（“逻辑”来自逻各斯）', 'λόγος', '词末 ς'),
}


def images_doc():
    lines = ['# 行内小图的转写', '',
             '电子书里有 13 张夹在句子中间的小图：1 张是电子书字库里没有的汉字，1 张是公式，11 张是希腊文/法文单词。'
             '按“行内小图转成文字”的办法处理：转成文字后排回原位，希腊文和法文与正文里的拉丁文一样用斜体。', '']
    rows = []
    for k, (where, text, note) in INLINE_NOTES.items():
        rows.append((f'`{k}`', where, text, note))
    lines += table(rows, ['图', '出处', '转写为', '说明'])
    lines += ['', '整页的图（封面、书名页、折页、封底）不是行内图，见 `dispositions.md` 第 2 节。']
    return lines


def dispositions():
    from . import dewey_report
    lines = ['# 杜威著作精选11种：转换时的取舍与改动（自动汇总）', '',
             '按“电子书转换时产生的明显错误才改，有疑问的保持原样”的原则处理。', '']
    rows = []
    for v in sorted(dewey.VOL):
        V = dewey.VOL[v]
        cfg = dewey.book(v)
        mods = cfg['modules']
        n_chap = sum(1 for m in mods if m.kind == 'text' and m.zone == 'body' and not m.mid.startswith('notes'))
        n_part = sum(1 for m in mods if m.kind == 'page' and getattr(m, 'part', False))
        n_plate = sum(1 for m in mods if m.mid.startswith('plate-page'))
        n_note = sum(1 for m in mods if m.mid.startswith('notes'))
        rows.append((v, dewey.TITLES[v], n_chap, n_part, n_plate, n_note))
    lines += ['## 1. 结构', '']
    lines += table(rows, ['册', '书名', '章/篇（模块）', '“第N部分”分隔页', '书后插图', '注释模块'])
    lines += ['',
              '- 每册各自成书：封面 → （前折页）→ 书名页 → 版权页 → 目录 → 主编序及各篇序跋 → 正文各章 → 注释 → 译后记/附录/校后记 → 书后插图 → （后折页、封底）。',
              '- 目录重新生成：点线、页码、可点击；章为一级，章内的一级小节（“I.……”“§1.……”）为二级，“第N部分”整页为分隔页，章排在它下面。',
              '- 注释：原书每章末尾附该章注释，页内 [n] 与注释互相链接。这里保持“章末注释”，注释用小字号、编号列 + 回链排；相邻短章的注释合并为一组'
              '（每章前有小标题），不出现只有几行的注释页。',
              '- 版权页（CIP）：第 2–10 册的电子书把它放在书末（后折页之前），这里统一挪到书名页之后；第 1、11 册本来就在前面。', '']
    lines += ['## 2. 整页图片和插图：什么不后置', '',
              '- **不后置**：本身就是“章节页”的整页图——每册封面（每册一张，风格同套装封面）、书名页（整页图，含杜威签名、译者、主编）、'
              '第 9、10、11 册的前折页/后折页/封底（各占一个文件的整页图）——都保持在电子书里的位置，各占一页；',
              '- **不后置**：紧接在章节标题后、作为该章节页头图的插图（第 2 册《序》里的“一次开卷考试”），留在标题下，图注排在图下；',
              '- **后置**：夹在正文中间的照片、儿童画和示意图（共 ' + str(sum(r[4] for r in rows)) + ' 幅，各册数目见上表“书后插图”列）移到各册书末，一页一图，页首“插图 N　图注”，页底“↩ 返回正文（第N页）”；'
              '正文原处保留图注并加蓝字黄框的“见书后插图N”（可点击）。',
              '- 折页图里前折页（第 9–11 册）是纯色页，也照样保留。', '']
    lines += ['## 3. 标题', '',
              '- 章标题为一级（黑体粗），章内 h3/h4 依次为二级、三级……各级用不同字体族（同黑格尔、康德各册）；“第N部分”是整页分隔页，'
              '不再和第一章挤在同一个文件里；',
              '- 序号与标题之间统一为一个不会被吞掉的空隙：“第一章　……”（全角空格）、“§1. ……”“2. ……”“I. ……”（西文序号后一个空格）、“I　……”；',
              '- 第 9 册《伦理学》第一章在电子书里标题录了两遍（h1 和 h2 都是“第一章 导论”），只留一个；',
              '- 只有罗马数字的小标题（第 5 册 1948 年导言里的 I、II、III、IV）用小号居中的“节号”样式；',
              '- 第 11 册《人性与行为》末尾的“1930年现代图书馆版前言”（电子书里排在第二十六章之后、译后记之前）保持原位置，作为独立的一节；'
              '第 5 册的“25年之后看改造：1948年《哲学的改造》再版导言”同样保持原位置。', '']
    c = collections.Counter()
    for n in range(1, 279):
        for it in DE.items(dewey.P(n)):
            joined = ''.join(r['t'] for r in it['runs'] if not r.get('i'))
            c['space_close'] += len(re.findall(r'(?<=[A-Za-z0-9])[ \u3000]+(?=[）】》”’，。；：！？、])', joined))
            for r in it['runs']:
                if r.get('i'):
                    c['inline'] += 1
                    continue
                t = r['t']
                for k in DT.PUA:
                    c['pua'] += t.count(k)
                c['apos'] += len(re.findall(r"(?<=[A-Za-z])'(?=[A-Za-z]|\s|[）”，。；：])", t))
                c['greek'] += t.count('τεχνη＇')
    lines += ['## 4. 文字层面的修复', '',
              '电子书的文字很干净，需要处理的只有下面几类：', '',
              '| 类别 | 处理 | 次数 |', '|---|---|---|',
              f'| 私用区字符 | Kindle 私用区的外文字母：`\\ue56e`→ö（Höffding、Fröhlich）、`\\ue55b`→æ（Cæsar）、`\\ue562`→ä（Märkel），按同一字库在《康德文集》里的对应关系还原 | {c["pua"]} |',
              f'| 直撇号 | Poetry\'s、O\'Neill、Agnes\' 里的 ASCII 撇号改为 ’ | {c["apos"]} |',
              f'| 全角标点前的空格 | “（Genesis ）”“eudaimonia ”里拉丁词后多余的空格去掉 | {c["space_close"]} |',
              f'| 希腊文 | “τεχνη＇”（无重音，全角撇号代替重音）→ τέχνη | {c["greek"]} |',
              f'| 行内小图 | 见 `inline-images.md` | {c["inline"]} |', '',
              '- 原书用斜体表示的强调，中译本处理为楷体（`span.kaiti`，共 3582 处），这里同样用楷体字（霞鹜文楷）排；拉丁文斜体（`<i>`，1383 处）用思源宋体的西文斜体（Noto Serif Italic）。',
              '- 连续的西文书目（第 9 册各章“参考文献”）改为左对齐（不两端对齐），避免英文长词行出现很大的字间空白。', '']
    lines += ['## 5. 版式', '',
              '- 与黑格尔、康德各册同一套：397 × 575 pt，27 行 × 17 pt，正文思源宋体 10.5 pt；引文/参考文献用楷体 10 pt；注释 8.5 pt；',
              '- 所有整页文字页末行基线相同（516.0 pt），标题不落页底，标题后至少两行，孤立标点/角标行、末页 1–2 字均为 0（数字见 `QA-report.md`）；',
              '- 标题里的注释角标不落在行首（强制换行放到角标之后）。', '']
    lines += ['## 6. 保持原样、无法还原的', '',
              '- 第 4 册海伦·凯勒引文里的行内小图 `image01826`（䳍形目的鸟）：字形匹配和“蛋壳紫色光亮”的语境相符，'
              '但没能对照英文原文核实具体的鸟名（英文原文所在站点无法访问），所以只把它转成对应的字，不加注释；',
              '- 折页上的书目（第 9–11 册后折页）是整页图，文字无法改动，保持原图。', '']
    return lines


def main():
    os.makedirs(DOC, exist_ok=True)
    for name, fn in (('inline-images.md', images_doc), ('dispositions.md', dispositions)):
        with open(os.path.join(DOC, name), 'w', encoding='utf8') as f:
            f.write('\n'.join(fn()) + '\n')
    print('written to', DOC)


if __name__ == '__main__':
    main()
