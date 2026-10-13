"""mkfonts.py [outdir] : rebuild tex/fonts/ST{Song,Heiti,Kaiti}Book.ttf, the CJK font subsets
embedded in src/book.pdf, as installable TrueType fonts (glyphs and metrics as embedded; a
Unicode cmap built from the ToUnicode CMaps), so that XeLaTeX sets CJK text with the book's
own advance widths."""
import os, re, sys
import pikepdf
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from io import BytesIO
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(B, 'tex', 'fonts')


def tounicode(data):
    m = {}
    hexs = lambda s: int(s, 16)
    for blk in re.findall(r'beginbfchar(.*?)endbfchar', data, re.S):
        for a, b in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
            m[hexs(a)] = bytes.fromhex(b).decode('utf-16-be')
    for blk in re.findall(r'beginbfrange(.*?)endbfrange', data, re.S):
        for a, b, c in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<[0-9A-Fa-f]+>|\[[^\]]*\])', blk):
            lo, hi = hexs(a), hexs(b)
            if c.startswith('<'):
                u = bytes.fromhex(c[1:-1]).decode('utf-16-be')
                for k in range(hi - lo + 1):
                    m[lo + k] = u[:-1] + chr(ord(u[-1]) + k)
            else:
                for k, d in enumerate(re.findall(r'<([0-9A-Fa-f]+)>', c)):
                    m[lo + k] = bytes.fromhex(d).decode('utf-16-be')
    return m


fams = {}
pdf = pikepdf.open(os.path.join(B, 'src', 'book.pdf'))
for page in pdf.pages:
    for _, f in (page.Resources.get('/Font') or {}).items():
        if f.get('/Subtype') != '/Type0':
            continue
        fam = str(f.BaseFont).split('+')[-1]
        if not fam.startswith('ST'):
            continue
        d = f.DescendantFonts[0]
        ff = d.FontDescriptor.get('/FontFile2')
        if ff is None or '/ToUnicode' not in f:
            continue
        data = ff.read_bytes()
        e = fams.setdefault(fam, {'font': data, 'map': {}})
        if len(data) > len(e['font']):
            e['font'] = data
        e['map'].update(tounicode(f.ToUnicode.read_bytes().decode('latin-1')))
os.makedirs(out, exist_ok=True)
for fam, e in sorted(fams.items()):
    tt = TTFont(BytesIO(e['font']))
    order = tt.getGlyphOrder()
    cmap = {}
    for cid, u in e['map'].items():
        if len(u) == 1 and cid < len(order):
            cmap.setdefault(ord(u), order[cid])
    t = newTable('cmap'); t.tableVersion = 0; t.tables = []
    for pid, eid, fmt in ((3, 1, 4), (0, 3, 4)) + (((3, 10, 12),) if max(cmap) > 0xFFFF else ()):
        st = CmapSubtable.newSubtable(fmt); st.platformID, st.platEncID, st.language = pid, eid, 0
        st.cmap = {k: v for k, v in cmap.items() if fmt == 12 or k <= 0xFFFF}
        t.tables.append(st)
    tt['cmap'] = t
    if 'post' not in tt:            # required by xdvipdfmx; subsets are embedded without it
        po = tt['post'] = newTable('post')
        po.formatType, po.italicAngle, po.underlinePosition, po.underlineThickness = 3.0, 0.0, -100, 50
        po.isFixedPitch = po.minMemType42 = po.maxMemType42 = po.minMemType1 = po.maxMemType1 = 0
    name = fam + 'Book'
    if 'name' not in tt:
        tt['name'] = newTable('name'); tt['name'].names = []
    for nid in (1, 4, 6):
        tt['name'].setName(name, nid, 3, 1, 0x409)
    tt['name'].setName('Regular', 2, 3, 1, 0x409)
    tt.save(os.path.join(out, name + '.ttf'))
    print(name, len(order), 'glyphs', len(cmap), 'mapped')
