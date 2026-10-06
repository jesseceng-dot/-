"""费曼物理学讲义（新千年版，中文 AZW3）：把一卷的各章抽成可对照的线性文本。

    BOOK_SCRATCH=<dir> python -m tools.flp_extract 1  ->  <dir>/zh_v1.json

每章: {part, title, blocks: [{k: h|p|img|cap|note, id, text, imgs}]}
text 里：斜体照写；下标 _{…}、上标 ^{…}；行内图片 ⟦图名⟧；行末的方程编号照原文（如“（9.4）”）。
"""
import os
import re
import sys
import json
from lxml import etree

SCRATCH = os.environ['BOOK_SCRATCH']
OEBPS = os.path.join(SCRATCH, 'unpack/x/mobi8/OEBPS')
VOL_PARTS = {1: range(10, 62), 2: range(73, 115), 3: range(126, 148)}
XH = '{http://www.w3.org/1999/xhtml}'


def ln(e):
    return etree.QName(e).localname


def lin(el):
    out = []

    def rec(n):
        if n.text:
            out.append(n.text)
        for c in n:
            if not isinstance(c.tag, str):
                if c.tail:
                    out.append(c.tail)
                continue
            t = ln(c)
            cls = c.get('class') or ''
            if t == 'img':
                out.append('⟦' + os.path.basename(c.get('src', '')) + '⟧')
            elif t == 'br':
                out.append('\n')
            elif 'math-sub' in cls:
                out.append('_{'); rec(c); out.append('}')
            elif 'math-super' in cls:
                out.append('^{'); rec(c); out.append('}')
            else:
                rec(c)
            if c.tail:
                out.append(c.tail)

    rec(el)
    return re.sub(r'[ \t\r\n]+', ' ', ''.join(out)).strip()


def chapter(part):
    path = os.path.join(OEBPS, 'Text', f'part{part:04d}.xhtml')
    root = etree.parse(path, etree.XMLParser(recover=True, huge_tree=True)).getroot()
    body = root.find('.//' + XH + 'body')
    blocks = []
    title = ''

    def walk(nodes):
        nonlocal title
        for el in nodes:
            if not isinstance(el.tag, str):
                continue
            t = ln(el)
            cls = el.get('class') or ''
            if t in ('h1', 'h2', 'h3', 'h4'):
                txt = lin(el)
                if t == 'h1' and not title:
                    title = txt
                blocks.append(dict(k='h', lvl=int(t[1]), id=el.get('id', ''), text=txt))
            elif t == 'p':
                txt = lin(el)
                imgs = [os.path.basename(i.get('src', '')) for i in el.iter() if isinstance(i.tag, str) and ln(i) == 'img']
                if not txt and not imgs:
                    continue
                k = 'cap' if 'picture-txt' in cls else ('note' if 'note' in cls or 'footnote' in cls else 'p')
                blocks.append(dict(k=k, text=txt, imgs=imgs, cls=cls))
            elif t == 'img':
                blocks.append(dict(k='img', text='⟦' + os.path.basename(el.get('src', '')) + '⟧', imgs=[os.path.basename(el.get('src', ''))], cls=cls))
            elif t in ('div', 'section', 'blockquote', 'ul', 'ol', 'li', 'table', 'tbody', 'tr', 'td'):
                walk(el)
            else:
                txt = lin(el)
                if txt:
                    blocks.append(dict(k='p', text=txt, imgs=[], cls=cls))

    walk(body)
    return dict(part=part, title=title, blocks=blocks)


def main(vol):
    chs = [chapter(p) for p in VOL_PARTS[vol]]
    json.dump(chs, open(os.path.join(SCRATCH, f'zh_v{vol}.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    n = sum(len(c['blocks']) for c in chs)
    print(f'vol {vol}: {len(chs)} chapters, {n} blocks, {sum(len(b["text"]) for c in chs for b in c["blocks"])} chars')


if __name__ == '__main__':
    main(int(sys.argv[1]))
