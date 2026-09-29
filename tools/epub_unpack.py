"""Unpack an EPUB into the same layout the AZW3 unpacker produces:  <scratch>/unpack/x/mobi8/OEBPS/{Text/partNNNN.xhtml, Images/*}.
Spine items are numbered in reading order (partNNNN), links between them are rewritten to 'partNNNN.xhtml#frag', images are flattened
into Images/ (basename kept; a numeric prefix is added when two files share a name).
    BOOK_SCRATCH=<dir> python -m tools.epub_unpack <book.epub>
"""
import os
import re
import sys
import shutil
import zipfile
import urllib.parse
from lxml import etree
from . import style

NS = {'c': 'urn:oasis:names:tc:opendocument:xmlns:container', 'o': 'http://www.idpf.org/2007/opf'}
XH = 'http://www.w3.org/1999/xhtml'


def main(src):
    root = os.path.join(style.SCRATCH, 'unpack', 'x')
    tmp = os.path.join(style.SCRATCH, 'epub_raw')
    for d in (root, tmp):
        if os.path.exists(d):
            shutil.rmtree(d)
    with zipfile.ZipFile(src) as z:
        z.extractall(tmp)
    cont = etree.parse(os.path.join(tmp, 'META-INF', 'container.xml'))
    opf_rel = cont.xpath('//c:rootfile/@full-path', namespaces=NS)[0]
    opf_path = os.path.join(tmp, opf_rel)
    base = os.path.dirname(opf_path)
    opf = etree.parse(opf_path)
    man = {i.get('id'): (i.get('href'), i.get('media-type')) for i in opf.xpath('//o:manifest/o:item', namespaces=NS)}
    spine = [man[i.get('idref')][0] for i in opf.xpath('//o:spine/o:itemref', namespaces=NS) if i.get('idref') in man]
    out = os.path.join(root, 'mobi8', 'OEBPS')
    os.makedirs(os.path.join(out, 'Text'))
    os.makedirs(os.path.join(out, 'Images'))
    # images (every image-type manifest item), names flattened
    img_name = {}
    used = set()
    for href, mt in man.values():
        if mt and mt.startswith('image/'):
            p = os.path.normpath(os.path.join(base, urllib.parse.unquote(href)))
            b = os.path.basename(p)
            n = b
            k = 1
            while n in used:
                n = f'{k}_{b}'
                k += 1
            used.add(n)
            img_name[p] = n
            if os.path.exists(p):
                shutil.copy(p, os.path.join(out, 'Images', n))
    part_of = {}
    for i, href in enumerate(spine):
        part_of[os.path.normpath(os.path.join(base, urllib.parse.unquote(href)))] = f'part{i:04d}'
    for p, part in part_of.items():
        tree = etree.parse(p, etree.XMLParser(recover=True, huge_tree=True))
        rt = tree.getroot()
        for el in rt.iter():
            if not isinstance(el.tag, str):
                continue
            tag = etree.QName(el).localname
            if tag == 'a' and el.get('href'):
                h = el.get('href')
                if h.startswith(('http:', 'https:', 'mailto:')):
                    continue
                f, _, frag = h.partition('#')
                if not f:
                    el.set('href', f'{part}.xhtml' + ('#' + frag if frag else ''))
                else:
                    q = os.path.normpath(os.path.join(os.path.dirname(p), urllib.parse.unquote(f)))
                    if q in part_of:
                        el.set('href', f'{part_of[q]}.xhtml' + ('#' + frag if frag else ''))
            elif tag in ('img', 'image'):
                for att in ('src', '{http://www.w3.org/1999/xlink}href', 'href'):
                    s = el.get(att)
                    if s:
                        q = os.path.normpath(os.path.join(os.path.dirname(p), urllib.parse.unquote(s)))
                        if q in img_name:
                            el.set(att, 'Images/' + img_name[q])
        data = etree.tostring(rt, encoding='utf-8', xml_declaration=True)
        with open(os.path.join(out, 'Text', part + '.xhtml'), 'wb') as f:
            f.write(data)
    with open(os.path.join(out, 'spine.txt'), 'w', encoding='utf8') as f:
        for i, href in enumerate(spine):
            f.write(f'part{i:04d}\t{href}\n')
    print('unpacked', len(spine), 'parts,', len(img_name), 'images to', root)


if __name__ == '__main__':
    main(sys.argv[1])
