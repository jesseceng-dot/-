"""Prepare TrueType-outline subsets of the fonts used by the book.

Chromium/Skia embeds CFF-flavoured OpenType (Noto CJK) as Type3, which is bulky and
renders poorly. We subset each face to the characters the book needs and convert the
outlines to TrueType (quadratic) so Skia embeds real CIDFontType2 subsets.
"""
import glob, os, sys
from fontTools.ttLib import TTFont, TTCollection
from fontTools import subset
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import table__g_l_y_f
from fontTools.ttLib import newTable

FONT_DIR = os.environ.get('BOOK_FONT_DIR', '/tmp/claude-0/-home-user--/243b6d09-d8f0-55ab-9830-1d98f5b584ee/scratchpad/fonts')

CJK_INDEX = {'SC': 2, 'TC': 3, 'HK': 4}[os.environ.get('BOOK_CJK', 'SC')]      # face of the Noto CJK collections: SC (default) or TC glyph forms
FACES = {
    # name: (path, ttc-index-or-None)
    'SerifSC-Regular': ('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc', CJK_INDEX),
    'SerifSC-Bold':    ('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc', CJK_INDEX),
    'SansSC-Regular':  ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', CJK_INDEX),
    'SansSC-Medium':   ('/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc', CJK_INDEX),
    'SansSC-Bold':     ('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', CJK_INDEX),
    'SansSC-Black':    ('/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc', CJK_INDEX),
    # further heading families (TrueType already): every heading level gets its own family
    'ZenHei-Regular':   ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 0),          # 文泉驿正黑
    'UKai-Regular':     ('/usr/share/fonts/truetype/arphic/ukai.ttc', 0),              # 文鼎楷体 (AR PL UKai CN)
    'SungtiL-Regular':  ('/usr/share/fonts/truetype/arphic-gbsn00lp/gbsn00lp.ttf', None),   # 文鼎报宋 (AR PL SungtiL GB)
    'MicroHei-Regular': ('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 0),          # 文泉驿微米黑
    'UMing-Regular':    ('/usr/share/fonts/truetype/arphic/uming.ttc', 0),              # 文鼎明体 (AR PL UMing CN)
    'KaitiM-Regular':   ('/usr/share/fonts/truetype/arphic-gkai00mp/gkai00mp.ttf', None),   # 文鼎简中楷 (AR PL KaitiM GB), 8th heading level
    'Droid-Regular':    ('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf', None),  # Droid Sans Fallback, 9th heading level
}

def otf_to_ttf(font, max_err=1.0):
    """In-place CFF -> glyf conversion."""
    glyph_order = font.getGlyphOrder()
    gs = font.getGlyphSet()
    glyf = table__g_l_y_f(); glyf.glyphOrder = glyph_order; glyf.glyphs = {}
    for name in glyph_order:
        pen = TTGlyphPen(gs)
        try:
            gs[name].draw(Cu2QuPen(pen, max_err, reverse_direction=True))
            glyf.glyphs[name] = pen.glyph()
        except Exception:
            glyf.glyphs[name] = TTGlyphPen(None).glyph()
    font['loca'] = newTable('loca')
    font['glyf'] = glyf
    del font['CFF ']
    if 'VORG' in font: del font['VORG']
    font['maxp'] = maxp = newTable('maxp')
    maxp.tableVersion = 0x00010000
    maxp.maxZones = 1; maxp.maxTwilightPoints = 0; maxp.maxStorage = 0
    maxp.maxFunctionDefs = 0; maxp.maxInstructionDefs = 0; maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = 0; maxp.maxComponentElements = max(
        (len(g.components if hasattr(g, 'components') else []) for g in glyf.glyphs.values()), default=0)
    maxp.numGlyphs = len(glyph_order)
    maxp.maxPoints = maxp.maxContours = maxp.maxCompositePoints = maxp.maxCompositeContours = 0
    maxp.maxComponentDepth = 0
    font['head'].glyphDataFormat = 0
    font.sfntVersion = '\x00\x01\x00\x00'
    post = font['post']; post.formatType = 2.0; post.extraNames = []; post.mapping = {}
    post.glyphOrder = glyph_order

def corpus_codepoints():
    cps = set(range(0x20, 0x7f)) | set(range(0xa0, 0x100))
    cps |= set(range(0x2000, 0x2070)) | set(range(0x3000, 0x3040)) | set(range(0xff00, 0xfff0))
    cps |= set(range(0x2100, 0x2200)) | set(range(0x2460, 0x2500)) | set(range(0x25a0, 0x2600))
    cps |= set(range(0x0370, 0x0400)) | set(range(0x2150, 0x2190)) | set(range(0x0300, 0x0370))   # (and the combining accents)
    cps |= {0x7560}                       # 畠 (stands behind a private-use glyph of the ebook)
    cps |= set(range(0x1f00, 0x2000)) | set(range(0x2070, 0x20a0)) | set(range(0x2200, 0x2300)) | set(range(0x00c0, 0x0180))
    cps |= {0x03ca, 0x00bd, 0x2153}       # ϊ ½ ⅓ (transcribed formulas)
    cps |= set(range(0x3251, 0x3260)) | set(range(0x32b1, 0x32c0))   # circled numbers 21-50 (translator's note marks)
    cps |= {0x9958}                       # 饘 (an inline glyph image of the ebook of 《叫魂》, transcribed to text)
    cps |= {0x2B695, 0x29F7E, 0x29F8C, 0x2B689}   # 𫚕 𩽾 𩾌 𫚉: fish characters behind the NFDA1-4 placeholders (Kant vol. 8)
    cps |= {0x9DC3}                       # 鷃: its left half 晏 builds 𮭨 (compose_yan)
    scratch = os.environ.get('BOOK_SCRATCH', '/tmp/claude-0/-home-user--/243b6d09-d8f0-55ab-9830-1d98f5b584ee/scratchpad')
    for f in glob.glob(os.path.join(scratch, 'unpack/x/mobi8/OEBPS/Text/*.xhtml')):
        cps |= {ord(c) for c in open(f, encoding='utf8').read()}
    # (BOOK_FONT_KEYS=q41,q42,…: one font directory for several books of one ebook, their corrections and transcriptions all)
    keys = os.environ.get('BOOK_FONT_KEYS', '').split(',') if os.environ.get('BOOK_FONT_KEYS') else [os.path.basename(scratch.rstrip('/'))]
    try:                                  # the replacement texts of the proof-reading corrections (bk_fixes)
        from . import bk_fixes
        for f in [f for key in keys for f in bk_fixes.FIXES.get(key, [])]:
            cps |= {ord(c) for x in f[2:] if isinstance(x, str) for c in x}
    except ImportError:
        pass
    try:                                  # the transcriptions of the ebook's inline glyph pictures (bk.CFG img_text)
        from . import bk
        for C in bk.CFG.values():
            if C.get('scratch') not in keys:
                continue
            for v in C.get('img_text', {}).values():
                for x in (v if isinstance(v, list) else [v]):
                    cps |= {ord(c) for c in (x[0] if isinstance(x, tuple) else x)}
    except ImportError:
        pass
    # GB2312 level-1/2 hanzi for safety (Big5 level 1/2 for a traditional-character book)
    for hi in range(0xb0, 0xf8):
        for lo in range(0xa1, 0xff):
            try: cps.add(ord(bytes([hi, lo]).decode('gb2312')))
            except Exception: pass
    if CJK_INDEX != 2:
        for hi in range(0xa4, 0xfa):
            for lo in list(range(0x40, 0x7f)) + list(range(0xa1, 0xff)):
                try: cps.add(ord(bytes([hi, lo]).decode('big5')))
                except Exception: pass
    return sorted(cps)

def _add_glyph(font, cp, res, name=None):
    """Insert the outline `res` (a pathops.Path) into a TrueType-outline font as the glyph of code point `cp`."""
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    glyf, hmtx, cmap, maxp = font['glyf'], font['hmtx'], font['cmap'], font['maxp']   # decompile before the glyph order grows
    if 'vmtx' in font:
        font['vmtx']
    gs = font.getGlyphSet()
    res.simplify(fix_winding=True)
    res.convertConicsToQuads()
    pen = TTGlyphPen(gs)
    res.draw(pen)
    glyph = pen.glyph()
    name = name or 'uni%X' % cp                 # a name that no CID-named glyph of the Noto fonts can collide with
    order = list(font.getGlyphOrder()) + [name]
    glyph.recalcBounds(glyf)
    hmtx.metrics[name] = (1000, glyph.xMin)
    if 'vmtx' in font:
        font['vmtx'].metrics[name] = (1000, 880 - glyph.yMax)
    glyf.glyphs[name] = glyph
    font.setGlyphOrder(order)
    glyf.glyphOrder = order
    for t in cmap.tables:
        if t.isUnicode() and t.format == 12:
            t.cmap[cp] = name
    maxp.numGlyphs = len(order)
    post = font['post']
    if getattr(post, 'formatType', 0) == 2.0:
        post.glyphOrder = order
    return name


def _outline(font, ch, keep=None):
    import pathops
    gs = font.getGlyphSet()
    p = pathops.Path()
    gs[font.getBestCmap()[ord(ch)]].draw(p.getPen(glyphSet=gs))
    if keep is None:
        return p
    out = pathops.Path()
    for c in p.contours:
        if keep(c.bounds):
            out.addPath(c)
    return out


def compose_hong(font, cp=0x2B689):
    """Noto Serif CJK has no glyph for U+2B689 𫚉 (simplified 魟 hóng: 鱼 + 工); the ebook's NFDA2 placeholder stands for it.
    Build it from the family's own strokes -- the 鱼 radical of 鲸 on the left, the 工 of 红 squeezed into the right half --
    so the character keeps the serif style of the running text instead of falling back to a sans face."""
    left = _outline(font, '鲸', lambda b: b[2] <= 470)          # 鱼 is the left component (x <= 470); 京 lies to its right
    gong = _outline(font, '红', lambda b: b[0] >= 300)          # 工 is the right component; 纟 ends at x = 453
    x0, _, x1, _ = gong.bounds
    sx = 440.0 / (x1 - x0)
    gong = gong.transform(sx, 0, 0, 1.0, 505 - x0 * sx, 0)
    left.addPath(gong)
    return _add_glyph(font, cp, left)


def compose_tinamou(font, cp=0x2EB65):
    """U+2EB65 𮭥 (simplified 䳍, the tinamou; 共 + 鸟) is missing from Noto Serif CJK as well: the 共 of 共 squeezed into the left
    half, the 鸟 taken from the right half of 鸡."""
    gong = _outline(font, '共')
    x0, _, x1, _ = gong.bounds
    sx = 410.0 / (x1 - x0)
    gong = gong.transform(sx, 0, 0, 1.0, 30 - x0 * sx, 0)
    niao = _outline(font, '鸡', lambda b: b[0] >= 390)
    x0, _, x1, _ = niao.bounds
    sx = 505.0 / (x1 - x0)
    niao = niao.transform(sx, 0, 0, 1.0, 470 - x0 * sx, 0)
    gong.addPath(niao)
    return _add_glyph(font, cp, gong)


def _fit(path, box, sy=None):
    """`path` scaled and moved into box = (x0, y0, x1, y1); sy given: that vertical scale, the bottom at y0."""
    x0, y0, x1, y1 = path.bounds
    sx = (box[2] - box[0]) / (x1 - x0)
    sy = sy or (box[3] - box[1]) / (y1 - y0)
    return path.transform(sx, 0, 0, sy, box[0] - x0 * sx, box[1] - y0 * sy)


def compose_huan(font, cp=0x24D2F):
    """U+24D2F 𤴯 (疒 + 丸; 《庄子·大宗师》 “以死为决𤴯溃痈”), which the ebook of 《中国哲学简史》 gives as a picture, is missing
    from Noto Serif CJK: the 疒 of 疔 (its 丁 left out) around the 丸 of 纨, set into the room the 丁 took."""
    frame = _outline(font, '疔', lambda b: not (b[0] >= 300 and b[3] <= 600))
    frame.addPath(_fit(_outline(font, '纨', lambda b: b[0] >= 300), (325, -79, 955, 585)))
    return _add_glyph(font, cp, frame)


def compose_xi(font, cp=0x2B370):
    """U+2B370 𫍰 (讠 + 思, simplified 諰; 《荀子·乐论》 “使其文足以辨而不𫍰”): the 讠 of 谌 beside the 思 of 腮."""
    left = _outline(font, '谌', lambda b: b[0] < 200 and b[2] <= 420)
    si = _outline(font, '腮', lambda b: b[0] >= 270)
    left.addPath(_fit(si, (left.bounds[2] + 20, si.bounds[1], max(si.bounds[2], 955), si.bounds[3]), sy=1.0))
    return _add_glyph(font, cp, left)


def compose_yan(font, cp=0x2EB68):
    """U+2EB68 𮭨 (晏 + 鸟, simplified 鷃; 向秀、郭象注 “斥𮭨之能下”): the 晏 of 鷃 beside the 鸟 of 鹌."""
    yan = _outline(font, '鷃', lambda b: b[2] <= 535 and b[0] < 460)
    yan.addPath(_fit(_outline(font, '鹌', lambda b: b[0] >= 500), (548, -77, 975, 837)))
    return _add_glyph(font, cp, yan)


def compose_gu(font, cp=0x2E774):
    """U+2E774 𮝴 (车 + 瓜, simplified 軱 gū, "a large bone"; 《庄子·养生主》 “技经肯綮之未尝，而况大𮝴乎”), which the ebook of
    《国家的视角》 gives as a picture: the 车 of 轱 beside the 瓜 of 呱."""
    left = _outline(font, '轱', lambda b: b[2] <= 470)
    gua = _outline(font, '呱', lambda b: b[0] >= 200 and b[3] > 800)
    left.addPath(_fit(gua, (left.bounds[2] + 15, gua.bounds[1], 975, gua.bounds[3]), sy=1.0))
    return _add_glyph(font, cp, left)


def compose_corner(font, cp=0x231F):
    """U+231F ⌟ (《气候赌场》 “悬崖形的或⌟形损失函数”, a picture in the ebook) is in no font here: the family's own 」, its
    corner on the baseline, centred in a narrower advance like a letter."""
    p = _outline(font, '」')
    x0, y0, x1, _ = p.bounds
    p = p.transform(1, 0, 0, 1, 150 - x0, -y0)
    name = _add_glyph(font, cp, p)
    font['hmtx'].metrics[name] = (int(300 + x1 - x0), 150)
    return name


def build(name):
    path, idx = FACES[name]
    out = os.path.join(FONT_DIR, name + '.ttf')
    if os.path.exists(out): return out
    font = TTCollection(path).fonts[idx] if idx is not None else TTFont(path)
    opts = subset.Options(); opts.layout_features = ['kern', 'locl', 'ccmp', 'liga']
    opts.notdef_outline = True; opts.name_IDs = ['*']; opts.glyph_names = False
    opts.drop_tables += ['DSIG']
    sub = subset.Subsetter(opts); sub.populate(unicodes=corpus_codepoints()); sub.subset(font)
    if 'CFF ' in font:
        otf_to_ttf(font)
    if name == 'SerifSC-Regular':
        compose_hong(font)
        compose_tinamou(font)
        compose_huan(font)
        compose_xi(font)
        compose_yan(font)
        compose_gu(font)
        compose_corner(font)
    os.makedirs(FONT_DIR, exist_ok=True)
    font.save(out); return out

def geb_rare(src):
    """《哥德尔、艾舍尔、巴赫》: the ebook's own font (OEBPS/Fonts/geb.ttf) holds the book's coined characters (U+AA9E–AAAF)
    and, at 'G', the upside-down G.  Saved as the family "GebRare" with that glyph moved to U+E047, where the text has it
    (bk_fixes), so that the font can stand first in every font list (style.STYLE_CSS) without touching a Latin G."""
    font = TTFont(src)
    for t in font['cmap'].tables:
        if t.isUnicode() and 0x47 in t.cmap:
            t.cmap[0xE047] = t.cmap.pop(0x47)
    for n in font['name'].names:
        if n.nameID in (1, 4, 6, 16):
            n.string = 'GebRare'
    out = os.path.join(FONT_DIR, 'GebRare.ttf')
    font.save(out)
    return out


if __name__ == '__main__' and sys.argv[1:2] != ['--shared']:
    os.makedirs(FONT_DIR, exist_ok=True)
    if sys.argv[1:2] == ['GebRare']:                # python -m tools.fonts GebRare <unpacked epub>/OEBPS/Fonts/geb.ttf
        print(geb_rare(sys.argv[2]))
        sys.exit()
    for n in (sys.argv[1:] or FACES):
        print(n, build(n), os.path.getsize(os.path.join(FONT_DIR, n + '.ttf')) // 1024, 'KB', flush=True)


def embolden(src_name, dst_name, amount=0.022):
    """Real bold for a family that only ships a regular face: every outline is thickened by `amount` em on each side
    (stroke + union), so Chromium embeds true TrueType outlines instead of a synthetic-bold Type3 font."""
    import pathops
    from fontTools.pens.cu2quPen import Cu2QuPen
    out = os.path.join(FONT_DIR, dst_name + '.ttf')
    if os.path.exists(out):
        return out
    font = TTFont(os.path.join(FONT_DIR, src_name + '.ttf'))
    gs = font.getGlyphSet()
    upm = font['head'].unitsPerEm
    d = upm * amount
    glyf = font['glyf']
    hmtx = font['hmtx']
    failed = []
    for name in font.getGlyphOrder():
        g = gs[name]
        path = pathops.Path()
        g.draw(path.getPen(glyphSet=gs))
        if not len(list(path.contours)):
            continue
        thick = pathops.Path(path)
        thick.stroke(2 * d, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4)
        thick.convertConicsToQuads()
        try:
            merged = pathops.op(path, thick, pathops.PathOp.UNION, fix_winding=True)
        except Exception:
            try:
                path.simplify(fix_winding=True)
                thick.simplify(fix_winding=True)
                merged = pathops.op(path, thick, pathops.PathOp.UNION, fix_winding=True)
            except Exception:
                failed.append(name)
                continue
        pen = TTGlyphPen(gs)
        merged.draw(Cu2QuPen(pen, 1.0, reverse_direction=False))
        glyph = pen.glyph()
        glyf[name] = glyph
        glyph.recalcBounds(glyf)
        hmtx[name] = (hmtx[name][0], glyph.xMin if hasattr(glyph, 'xMin') else hmtx[name][1])
    if failed:
        print(dst_name, 'glyphs left unemboldened:', len(failed))
    font.save(out)
    return out


BOLD_FROM = {'UKai-Bold': 'UKai-Regular', 'SungtiL-Bold': 'SungtiL-Regular', 'MicroHei-Bold': 'MicroHei-Regular',
             'UMing-Bold': 'UMing-Regular', 'KaitiM-Bold': 'KaitiM-Regular', 'Droid-Bold': 'Droid-Regular'}

SYSTEM_COPIES = {                                  # used whole (TrueType outlines already): Kai text and the Latin / Greek face
    'LXGWWenKai-Regular.ttf': '/usr/share/fonts/truetype/lxgw-wenkai/LXGWWenKai-Regular.ttf',
    'LXGWWenKai-Bold.ttf': '/usr/share/fonts/truetype/lxgw-wenkai/LXGWWenKai-Bold.ttf',
    'NotoSerif-Regular.ttf': '/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf',
    'NotoSerif-Bold.ttf': '/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf',
    'NotoSerif-Italic.ttf': '/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf',
    'NotoSansSymbols2-Regular.ttf': '/usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf',   # (❑ of book 39: .sym)
    'FreeSerif.ttf': '/usr/share/fonts/truetype/freefont/FreeSerif.ttf',   # (√ of book 59: .rad; the CJK faces set it full width)
    'FreeSerif-Italic.ttf': '/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf',   # (book 60: vectors, the arrow U+20D7: .vec)
}


def shared():
    """Every font file the style sheets name, in FONT_DIR: the subsets of all FACES (the book's corpus), the emboldened
    bold faces of the heading families that have no bold, and the fonts used whole."""
    import shutil
    os.makedirs(FONT_DIR, exist_ok=True)
    for n in FACES:
        print(n, build(n), flush=True)
    for dst, src in BOLD_FROM.items():
        print(dst, embolden(src, dst), flush=True)
    for dst, src in SYSTEM_COPIES.items():
        out = os.path.join(FONT_DIR, dst)
        if not os.path.exists(out):
            shutil.copy(src, out)
        print(dst, out, flush=True)


if __name__ == '__main__' and sys.argv[1:2] == ['--shared']:     # python -m tools.fonts --shared   (BOOK_SCRATCH, BOOK_FONT_DIR)
    shared()


