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

FACES = {
    # name: (path, ttc-index-or-None)
    'SerifSC-Regular': ('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc', 2),
    'SerifSC-Bold':    ('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc', 2),
    'SansSC-Regular':  ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 2),
    'SansSC-Medium':   ('/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc', 2),
    'SansSC-Bold':     ('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 2),
    'SansSC-Black':    ('/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc', 2),
    # further heading families (TrueType already): every heading level gets its own family
    'ZenHei-Regular':   ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 0),          # 文泉驿正黑
    'UKai-Regular':     ('/usr/share/fonts/truetype/arphic/ukai.ttc', 0),              # 文鼎楷体 (AR PL UKai CN)
    'SungtiL-Regular':  ('/usr/share/fonts/truetype/arphic-gbsn00lp/gbsn00lp.ttf', None),   # 文鼎报宋 (AR PL SungtiL GB)
    'MicroHei-Regular': ('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 0),          # 文泉驿微米黑
    'UMing-Regular':    ('/usr/share/fonts/truetype/arphic/uming.ttc', 0),              # 文鼎明体 (AR PL UMing CN)
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
    cps |= set(range(0x0370, 0x0400)) | set(range(0x2150, 0x2190))
    cps |= {0x7560}                       # 畠 (stands behind a private-use glyph of the ebook)
    for f in glob.glob('/tmp/claude-0/-home-user--/243b6d09-d8f0-55ab-9830-1d98f5b584ee/scratchpad/unpack/x/mobi8/OEBPS/Text/*.xhtml'):
        cps |= {ord(c) for c in open(f, encoding='utf8').read()}
    # GB2312 level-1/2 hanzi for safety
    for hi in range(0xb0, 0xf8):
        for lo in range(0xa1, 0xff):
            try: cps.add(ord(bytes([hi, lo]).decode('gb2312')))
            except Exception: pass
    return sorted(cps)

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
    os.makedirs(FONT_DIR, exist_ok=True)
    font.save(out); return out

if __name__ == '__main__':
    os.makedirs(FONT_DIR, exist_ok=True)
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
             'UMing-Bold': 'UMing-Regular'}

if __name__ == '__main__' and False:
    pass
