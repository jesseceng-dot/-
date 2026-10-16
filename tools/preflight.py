"""Pre-flight survey of an unpacked ebook -- run it right after unpacking, before writing the book's configuration.

    BOOK_SCRATCH=<dir> python -m tools.preflight [--book N] [--max 8]

It prints, in one go, what the earlier conversions had to find out by hand:
  1. metadata and the reading order (parts, their size and first heading);
  2. tag / class statistics (which classes are headings, quotes, captions, notes ...);
  3. the note apparatus: note marks, note bodies and their back-links;
  4. every picture: pixel size, resolution, how often and where it is used -- inside a line of text (an inline picture:
     it has to be transcribed to text, exactly) or as a paragraph of its own (a figure); SVG pictures with their <desc>;
  5. fonts embedded in the ebook and private-use characters (coined glyphs);
  6. characters the book fonts lack (Song body, Hei headings, Kai quotes, Latin/Greek) -- these would print as a
     fallback face or as empty boxes, so they need a font or a composed glyph (tools/fonts.py compose_*);
  7. mechanical text issues: half-width punctuation in Chinese, full-width punctuation in Latin, odd spaces
     (U+2002, NBSP, spaces between Chinese characters), Latin words glued to figures, straight quotes, unbalanced
     brackets, separately formatted Latin words (<i>A</i> <i>History</i>).
With --book N the transcriptions already configured (bk.CFG[N]['img_text']) are taken into account.
The ebook is untrusted input: it is parsed without entity resolution or network access.
"""
import collections
import glob
import os
import re
import sys
from lxml import etree

SCRATCH = os.environ.get('BOOK_SCRATCH', '')
OEBPS = os.path.join(SCRATCH, 'unpack/x/mobi8/OEBPS')
TEXT_DIR = os.path.join(OEBPS, 'Text')
IMG_DIR = os.path.join(OEBPS, 'Images')
XH = '{http://www.w3.org/1999/xhtml}'
PARSER = etree.XMLParser(recover=True, huge_tree=True, resolve_entities=False, no_network=True)
CJK = '\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff'
BLOCKS = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th', 'dt', 'dd', 'blockquote', 'aside', 'figcaption',
          'caption', 'section', 'pre'}
FONTS = {   # family used by the pipeline -> (font file, ttc face name)
    'SongBody (正文宋体)': ('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc', 'Noto Serif CJK SC'),
    'HeiTi (标题黑体)': ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 'Noto Sans CJK SC'),
    'KaiTi (引文楷体)': ('/usr/share/fonts/truetype/lxgw-wenkai/LXGWWenKai-Regular.ttf', None),
    'Noto Serif (西文/希腊文)': ('/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf', None),
}


def ln(e):
    return etree.QName(e).localname if isinstance(e.tag, str) else ''


def parts():
    return sorted(glob.glob(os.path.join(TEXT_DIR, 'part*.xhtml')))


def body_of(path):
    root = etree.parse(path, PARSER).getroot()
    b = root.find('.//' + XH + 'body')
    return b if b is not None else root


def text_of(el, img_mark='\u25a1'):
    """Text of an element; pictures inside it shown as img_mark."""
    out = []
    for node in el.iter():
        if not isinstance(node.tag, str):
            continue
        if ln(node) in ('img', 'image'):
            out.append(img_mark)
        if node.text and ln(node) not in ('style', 'script'):
            out.append(node.text)
        if node is not el and node.tail:
            out.append(node.tail)
    return ''.join(out)


def block_of(el):
    p = el.getparent()
    while p is not None and ln(p) not in BLOCKS:
        p = p.getparent()
    return p


def show(rows, n):
    for r in rows[:n]:
        print('    ' + r)
    if len(rows) > n:
        print(f'    …（另有 {len(rows) - n} 处）')


def img_info(name):
    path = os.path.join(IMG_DIR, name)
    if not os.path.exists(path):
        return 'missing file'
    if name.lower().endswith('.svg'):
        try:
            r = etree.parse(path, PARSER).getroot()
            desc = next((''.join(x.itertext()).strip() for x in r.iter() if ln(x) == 'desc'), '')
            return f"SVG {r.get('width')}x{r.get('height')} viewBox={r.get('viewBox')} desc={desc[:40]!r}"
        except Exception as e:
            return f'SVG (unreadable: {e})'
    try:
        from PIL import Image
        im = Image.open(path)
        dpi = im.info.get('dpi')
        return f'{im.format} {im.size[0]}x{im.size[1]} {im.mode}' + (f' {int(dpi[0])}dpi' if dpi else '')
    except Exception as e:
        return f'unreadable ({e})'


_SMALL = {}


def small(name, limit=100):
    """A picture no higher than `limit` px (an SVG: user units): a glyph, a symbol or a formula, not a figure."""
    if name not in _SMALL:
        path = os.path.join(IMG_DIR, name)
        h = 0
        try:
            if name.lower().endswith('.svg'):
                r = etree.parse(path, PARSER).getroot()
                v = re.match(r'[\d.]+', r.get('height') or '') or re.match(r'[\d.]+', ((r.get('viewBox') or '0 0 0 0').split() + ['0'] * 4)[3])
                h = float(v.group(0)) if v else 0
            else:
                from PIL import Image
                h = Image.open(path).size[1]
        except Exception:
            h = 0
        _SMALL[name] = 0 < h <= limit
    return _SMALL[name]


def cmap_of(path, face):
    from fontTools.ttLib import TTFont, TTCollection
    if not os.path.exists(path):
        return None
    if path.endswith('.ttc'):
        fonts = TTCollection(path).fonts
        f = next((x for x in fonts if x['name'].getDebugName(4) == face), fonts[0])
    else:
        f = TTFont(path)
    return set(f.getBestCmap())


def main():
    args = sys.argv[1:]
    book = int(args[args.index('--book') + 1]) if '--book' in args else None
    nmax = int(args[args.index('--max') + 1]) if '--max' in args else 8
    if not os.path.isdir(TEXT_DIR):
        sys.exit(f'no unpacked text under {TEXT_DIR} (unpack first: python -m tools.epub_unpack / tools.unpack)')
    C = None
    if book is not None:
        from . import bk
        C = bk.CFG[book]

    # 1. metadata and parts
    print('# 1. 元数据与阅读顺序')
    for opf in glob.glob(os.path.join(SCRATCH, 'epub_raw', '**', '*.opf'), recursive=True) + glob.glob(os.path.join(OEBPS, '*.opf')):
        r = etree.parse(opf, PARSER).getroot()
        meta = [(ln(x), (x.text or '').strip()) for x in r.iter() if isinstance(x.tag, str) and
                etree.QName(x).namespace == 'http://purl.org/dc/elements/1.1/' and (x.text or '').strip()]
        print('  ', os.path.relpath(opf, SCRATCH), '：', '；'.join(f'{k}={v}' for k, v in meta))
    files = parts()
    print(f'  {len(files)} 个部件（partNNNN），按阅读顺序：')
    tags, classes, heads = collections.Counter(), collections.Counter(), []
    texts = {}
    for f in files:
        b = body_of(f)
        name = os.path.basename(f)[:-6]
        t = re.sub(r'\s+', ' ', text_of(b)).strip()
        texts[name] = b
        h = next((re.sub(r'\s+', ' ', text_of(x)).strip() for x in b.iter() if ln(x) in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')), '')
        n_img = sum(1 for x in b.iter() if ln(x) in ('img', 'image'))
        print(f'    {name}  {len(t):7d} 字  图 {n_img:3d}  {(h or t)[:36]!r}')
        for x in b.iter():
            if not isinstance(x.tag, str):
                continue
            k = ln(x) + ('.' + x.get('class') if x.get('class') else '')
            tags[k] += 1
            if ln(x) in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                heads.append(f"{name} {k}: {re.sub(chr(10), ' ', text_of(x)).strip()[:40]!r}")

    # 2. tags and classes
    print('\n# 2. 标签与类（出现次数）')
    for k, v in tags.most_common():
        if v >= 2 or not k.startswith(('span', 'a', 'br')):
            print(f'    {v:6d}  {k}')
    print('  标题（前若干个）：')
    show(heads, nmax * 4)

    # 3. notes
    print('\n# 3. 注释')
    marks, bodies, back = [], [], 0
    pat_mark = re.compile(r'^\s*[\[［(（〔]?\s*(?:注|註|校)?\s*\d{1,4}\s*[\]］)）〕]?\s*$|^[①-⑳㉑-㊿]$')
    for name, b in texts.items():
        for a in b.iter():
            if ln(a) != 'a' or not a.get('href'):
                continue
            t = text_of(a).strip()
            sup = any(ln(x) == 'sup' for x in a.iter()) or (a.getparent() is not None and ln(a.getparent()) == 'sup')
            if '#' in a.get('href') and (sup or pat_mark.match(t)):
                blk = block_of(a)
                cls = (blk.get('class') or '') if blk is not None else ''
                ty = (blk.get('{http://www.idpf.org/2007/ops}type') or '') if blk is not None else ''
                is_body = blk is not None and (blk is not None and (re.search(r'note|foot|fn|zhu|endnote', cls + ty, re.I) or ln(blk) == 'aside')
                                               or text_of(blk).strip().startswith(t))
                (bodies if is_body else marks).append(f'{name} {t!r} → {a.get("href")}  [{ln(blk) if blk is not None else "?"}.{cls}]')
                if is_body:
                    back += 1
    print(f'  正文角标 {len(marks)} 个，注释条目（带回链）{len(bodies)} 条')
    print('  角标样例：'); show(marks, nmax)
    print('  注释条目样例：'); show(bodies, nmax)
    asides = sum(1 for b in texts.values() for x in b.iter() if ln(x) == 'aside')
    if asides:
        print(f'  <aside> 元素 {asides} 个（EPUB3 脚注/尾注）')

    # 4. pictures
    print('\n# 4. 图片')
    use = collections.defaultdict(list)
    icons = collections.Counter()
    for name, b in texts.items():
        for x in b.iter():
            if ln(x) not in ('img', 'image'):
                continue
            src = x.get('src') or x.get('{http://www.w3.org/1999/xlink}href') or x.get('href') or ''
            src = os.path.basename(src)
            if any(ln(y) == 'a' and (y.get('{http://www.idpf.org/2007/ops}type') == 'noteref'
                                     or 'duokan-footnote' in (y.get('class') or '')) for y in x.iterancestors()):
                icons[src] += 1                                 # an icon as a note mark (EPUB3 / duokan footnote): no text to transcribe
                continue
            blk = block_of(x)
            bt = text_of(blk) if blk is not None else ''
            rest = bt.replace('\u25a1', '').strip()
            where = 'inline' if rest and small(src) else 'alone'       # a big picture beside text: a figure with its caption
            if blk is not None and ln(blk) in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                where = 'heading'
            i = bt.find('\u25a1')
            ctx = re.sub(r'\s+', ' ', bt[max(0, i - 16):i + 17]) if rest else ''
            use[src].append((name, where, ctx, x.get('alt') or ''))
    inline = [s for s, us in use.items() if any(u[1] != 'alone' for u in us)]
    alone = [s for s, us in use.items() if s not in inline]
    unused = sorted(set(os.listdir(IMG_DIR)) - set(use)) if os.path.isdir(IMG_DIR) else []
    tr = (C or {}).get('img_text', {})
    if icons:
        print(f'  注释角标图标（不是文字，转换时换成编号角标）{len(icons)} 种、{sum(icons.values())} 处：{" ".join(sorted(icons))}')
    print(f'  行内小图（夹在文字里，必须精确转成文字）{len(inline)} 种、{sum(len(use[s]) for s in inline)} 处'
          + (f'；已配置转写 {sum(1 for s in inline if s in tr)} 种' if C else ''))
    for s in sorted(inline):
        us = use[s]
        mark = ('  ✓ ' + repr(tr[s]) if s in tr else '  ✗ 未转写') if C else ''
        print(f'    {s:28s} {img_info(s):34s} ×{len(us):<3d}{mark}')
        for u in us[:2]:
            print(f'        {u[0]} {u[1]}: …{u[2]}…' + (f'  alt={u[3]!r}' if u[3] else ''))
    print(f'  独立成段的图（插图、整页图、封面）{len(alone)} 种：')
    for s in sorted(alone):
        us = use[s]
        print(f'    {s:28s} {img_info(s):34s} ×{len(us):<3d} {" ".join(sorted(set(u[0] for u in us)))[:60]}')
    if unused:
        print(f'  正文没有引用的图片 {len(unused)} 个（封面、被替换掉的旧图等）：')
        for s in unused[:nmax * 3]:
            print(f'    {s:28s} {img_info(s)}')

    # 5. embedded fonts, private use
    print('\n# 5. 电子书自带字体与私用区字符')
    fonts = [f for f in glob.glob(os.path.join(SCRATCH, 'epub_raw', '**', '*'), recursive=True)
             if f.lower().endswith(('.ttf', '.otf', '.woff', '.woff2'))]
    fonts += [f for f in glob.glob(os.path.join(OEBPS, '**', '*'), recursive=True) if f.lower().endswith(('.ttf', '.otf'))]
    print('  自带字体：', [os.path.relpath(f, SCRATCH) for f in fonts] or '无')
    allt = collections.Counter()
    ctxs = {}
    for name, b in texts.items():
        t = text_of(b, '')
        allt.update(t)
        for m in re.finditer('[\ue000-\uf8ff\U000f0000-\U0010ffff\ufffd]', t):
            ctxs.setdefault(m.group(), f'{name} …{t[max(0, m.start() - 10):m.end() + 10]}…')
    pua = {c: n for c, n in allt.items() if 0xE000 <= ord(c) <= 0xF8FF or ord(c) >= 0xF0000 or c == '\ufffd'}
    print(f'  私用区/替换字符 {len(pua)} 种：')
    show([f'U+{ord(c):04X} ×{n}  {ctxs.get(c, "")}' for c, n in sorted(pua.items())], nmax * 2)
    for m in sorted(set(re.findall(r'NFDA\d+', ' '.join(text_of(b, '') for b in texts.values())))):
        print(f'  缺字占位符 {m}（电子书字库缺字，需考订补字）')

    # 6. font coverage
    print('\n# 6. 字体缺字（这些字会落到备用字体或印成空框）')
    want = collections.Counter({c: n for c, n in allt.items() if ord(c) > 0x7f and not c.isspace()})
    for v in tr.values():
        for x in (v if isinstance(v, list) else [v]):
            for c in (x[0] if isinstance(x, tuple) else x):
                want[c] += 1
    cmaps = {k: cmap_of(*v) for k, v in FONTS.items()}
    song = cmaps['SongBody (正文宋体)'] or set()
    miss = [c for c in want if ord(c) not in song and not (0xE000 <= ord(c) <= 0xF8FF) and unicodedata_cat(c) not in ('Cc', 'Cf', 'Zs')]
    for c in sorted(miss, key=ord):
        others = [k.split()[0] for k, cm in cmaps.items() if cm and ord(c) in cm]
        print(f'    {c} U+{ord(c):04X} ×{want[c]:<4d} {uname(c)[:40]:40s} 有此字的字体：{", ".join(others) or "无"}')
    if not miss:
        print('    无')

    # 7. text issues
    print('\n# 7. 文字层面的机械问题（排版规范化的候选，逐条核对后再写进 bk_fixes）')
    P = {
        '半角标点夹在汉字旁': rf'[{CJK}][,;:!?](?!\d)|[,;:!?][{CJK}]',
        '半角括号用于中文': rf'[{CJK}]\(|\)[{CJK}]',
        '西文中的全角句点、冒号、分号': r'[A-Za-z][．：；][A-Za-z]|[A-Z]．',
        '汉字之间的空格（章节序号后的除外）': rf'(?<!^第.)(?<!^第..)(?<!^第...)(?<!^第....)[{CJK}，。、；：）][ \u3000]+[{CJK}（“]',
        'U+2002/2003/2009 等空格': '[\u2002\u2003\u2004\u2005\u2009\u200a]',
        '不换行空格 NBSP': '\u00a0',
        '西文词与数字粘连': r'[a-z]{3,}\d|\d[a-z]{3,}',
        '西文标点后缺空格': r'[a-z][,;:][A-Za-z]',
        '直引号/直撇号': r'["\']',
        '三个半角句点': r'\.\.\.',
        '括号不配对（每段）': None,
    }
    rows = collections.defaultdict(list)
    for name, b in texts.items():
        for blk in b.iter():
            if ln(blk) not in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'div', 'blockquote'):
                continue
            if any(ln(x) in BLOCKS for x in blk.iterchildren() if isinstance(x.tag, str)):
                continue                                   # only innermost blocks
            t = text_of(blk, '')
            for k, p in P.items():
                if p is None:
                    for a, z in ('（）', '()', '《》', '【】', '〔〕'):          # (“” may stay open across the paragraphs of a quotation)
                        if t.count(a) != t.count(z):
                            rows[k].append(f'{name} {a}{z} …{t[:40]}…')
                    continue
                for m in re.finditer(p, t):
                    rows[k].append(f'{name} …{t[max(0, m.start() - 12):m.end() + 12]}…')
        raw = etree.tostring(b, encoding='unicode')
        for m in re.finditer(r'</(i|em|b|strong|span)>(\s+)<(i|em|b|strong|span)\b', raw):
            rows['分别加格式的相邻西文词（词间空格要保留）'].append(f'{name} …{re.sub("<[^>]+>", "", raw[max(0, m.start() - 40):m.end() + 40])[:50]}…')
    for k in list(P) + ['分别加格式的相邻西文词（词间空格要保留）']:
        print(f'  {k}：{len(rows[k])}')
        show(rows[k], nmax)

    # tables, links
    print('\n# 8. 表格与外部链接')
    for name, b in texts.items():
        for tb in (x for x in b.iter() if ln(x) == 'table'):
            trs = [r for r in tb.iter() if ln(r) == 'tr']
            ncol = max((sum(int(c.get('colspan', 1) or 1) for c in r if ln(c) in ('td', 'th')) for r in trs), default=0)
            head = re.sub(r'\s+', ' ', text_of(tb))[:40]
            print(f'    {name} 表格 {len(trs)} 行 × {ncol} 列  {head!r}')
    ext = [(name, a.get('href')) for name, b in texts.items() for a in b.iter() if ln(a) == 'a' and (a.get('href') or '').startswith('http')]
    print(f'  外部链接 {len(ext)} 个：', [h for _, h in ext[:nmax]])


def unicodedata_cat(c):
    import unicodedata
    return unicodedata.category(c)


def uname(c):
    import unicodedata
    return unicodedata.name(c, '')


if __name__ == '__main__':
    main()
