"""Page geometry, grid and font settings for the print edition (大32开, 五号/17pt grid)."""
import os

# ---- page (pt) -------------------------------------------------------------
# BOOK_GEOM selects the page: 'd32' = 大32开 (140 × 203 mm; Hegel, Kant, Dewey), 'k16' = 16开 (170 × 240 mm, 481.89 × 680.31 pt).
GEOM = os.environ.get('BOOK_GEOM', 'd32')
_PROFILES = {
    'd32': dict(PAGE_W=397.0, PAGE_H=575.0, CHARS=28, NLINES=27, TOP=62.0, SMALL_N=40),
    'k16': dict(PAGE_W=481.89, PAGE_H=680.31, CHARS=34, NLINES=32, TOP=76.0, SMALL_N=47),
}
_P = _PROFILES[GEOM]
PAGE_W = _P['PAGE_W']
PAGE_H = _P['PAGE_H']
FONT = 10.5             # body size (五号)
TEXT_W = _P['CHARS'] * FONT    # 28 (d32) / 34 (k16) characters of 10.5 pt
LEFT = (PAGE_W - TEXT_W) / 2   # left == right margin (51.5 pt = 18.2 mm on d32)
LINE = 17.0             # grid pitch: every vertical dimension is a multiple of this
NLINES = _P['NLINES']   # lines per page
TOP = _P['TOP']         # top of first grid line, from page top
TEXT_H = NLINES * LINE  # 459 pt (d32) / 544 pt (k16)
BOTTOM_MARGIN = PAGE_H - TOP - TEXT_H  # 54 pt (d32)
SMALL_N = _P['SMALL_N'] # lines of the small-print grid (notes, copyright, index) per page
SY = PAGE_H / 575.0     # vertical scale of the fixed positions of title/divider pages, designed on the d32 page

# ---- build directories -------------------------------------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRATCH = os.environ.get('BOOK_SCRATCH',
                         '/tmp/claude-0/-home-user--/243b6d09-d8f0-55ab-9830-1d98f5b584ee/scratchpad')
FONT_DIR = os.environ.get('BOOK_FONT_DIR', os.path.join(SCRATCH, 'fonts'))
CHROME = os.environ.get('BOOK_CHROME', '/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
LINK_BASE = 'https://book.local/#'     # every internal link is emitted as this URI, rewritten to GoTo later

# ---- letter-spacing variants (em) used by the paginator to absorb line-count differences --
VARIANTS = [0.0, -0.012, 0.012, -0.024, 0.024, -0.036, 0.036]
# wider variants, only tried for a module whose first solution leaves a page unfilled (still well below what the eye notices)
VARIANTS_ALL = VARIANTS + [-0.048, 0.048, -0.06, 0.06]

FONTS_CSS = """
@font-face{font-family:"SongBody";src:url("%(f)s/SerifSC-Regular.ttf");font-weight:400}
@font-face{font-family:"SongBody";src:url("%(f)s/SerifSC-Bold.ttf");font-weight:700}
@font-face{font-family:"HeiTi";src:url("%(f)s/SansSC-Regular.ttf");font-weight:400}
@font-face{font-family:"HeiTi";src:url("%(f)s/SansSC-Medium.ttf");font-weight:500}
@font-face{font-family:"HeiTi";src:url("%(f)s/SansSC-Bold.ttf");font-weight:700}
@font-face{font-family:"HeiTi";src:url("%(f)s/SansSC-Black.ttf");font-weight:900}
@font-face{font-family:"KaiTi";src:url("%(f)s/LXGWWenKai-Regular.ttf");font-weight:400}
@font-face{font-family:"KaiTi";src:url("%(f)s/LXGWWenKai-Bold.ttf");font-weight:700}
@font-face{font-family:"ZhengHei";src:url("%(f)s/ZenHei-Regular.ttf");font-weight:400}
@font-face{font-family:"WenKai2";src:url("%(f)s/UKai-Regular.ttf");font-weight:400}
@font-face{font-family:"WenKai2";src:url("%(f)s/UKai-Bold.ttf");font-weight:700}
@font-face{font-family:"BaoSong";src:url("%(f)s/SungtiL-Regular.ttf");font-weight:400}
@font-face{font-family:"BaoSong";src:url("%(f)s/SungtiL-Bold.ttf");font-weight:700}
@font-face{font-family:"WeiMi";src:url("%(f)s/MicroHei-Regular.ttf");font-weight:400}
@font-face{font-family:"WeiMi";src:url("%(f)s/MicroHei-Bold.ttf");font-weight:700}
@font-face{font-family:"MingTi";src:url("%(f)s/UMing-Regular.ttf");font-weight:400}
@font-face{font-family:"MingTi";src:url("%(f)s/UMing-Bold.ttf");font-weight:700}
@font-face{font-family:"KaiM";src:url("%(f)s/KaitiM-Regular.ttf");font-weight:400}
@font-face{font-family:"KaiM";src:url("%(f)s/KaitiM-Bold.ttf");font-weight:700}
@font-face{font-family:"DroidHei";src:url("%(f)s/Droid-Regular.ttf");font-weight:400}
@font-face{font-family:"DroidHei";src:url("%(f)s/Droid-Bold.ttf");font-weight:700}
@font-face{font-family:"LatIt";src:url("%(f)s/NotoSerif-Italic.ttf");font-style:italic;font-weight:400;unicode-range:U+0000-024F,U+0300-036F,U+0370-03FF,U+1F00-1FFF,U+2000-206F}
@font-face{font-family:"HanExt";src:url("%(f)s/SansSC-Regular.ttf");font-weight:400;unicode-range:U+20000-3FFFF}
@font-face{font-family:"GrkSerif";src:url("%(f)s/NotoSerif-Regular.ttf");font-weight:400;unicode-range:U+0370-03FF,U+1F00-1FFF}
@font-face{font-family:"GrkSerif";src:url("%(f)s/NotoSerif-Bold.ttf");font-weight:700;unicode-range:U+0370-03FF,U+1F00-1FFF}
@font-face{font-family:"AposSerif";src:url("%(f)s/NotoSerif-Regular.ttf");font-weight:400;unicode-range:U+2019}
@font-face{font-family:"AposSerif";src:url("%(f)s/NotoSerif-Bold.ttf");font-weight:700;unicode-range:U+2019}
@font-face{font-family:"GebRare";src:url("%(f)s/GebRare.ttf");unicode-range:U+AA9E-AAAF,U+E047}
@font-face{font-family:"SymFont";src:url("%(f)s/NotoSansSymbols2-Regular.ttf");font-weight:400;unicode-range:U+2751}
@font-face{font-family:"RadSerif";src:url("%(f)s/FreeSerif.ttf");font-weight:400;unicode-range:U+221A}
@font-face{font-family:"MathOps";src:url("%(f)s/FreeSerif.ttf");font-weight:400;unicode-range:U+00B1,U+00D7,U+00F7,U+2026,U+2190-21FF,U+2200-22FF}
@font-face{font-family:"VecIt";src:url("%(f)s/FreeSerif-Italic.ttf");font-style:italic;font-weight:400}
@font-face{font-family:"MathFont";src:url("%(f)s/STIXTwoMath-Regular.ttf");font-weight:400}
@font-face{font-family:"GuaSym";src:url("%(f)s/LXGWWenKai-Regular.ttf");font-weight:400;unicode-range:U+2630-2637,U+268A-268F,U+4DC0-4DFF}
@font-face{font-family:"LatSerif";src:url("%(f)s/NotoSerif-Regular.ttf");font-weight:400;unicode-range:U+0000-024F,U+1E00-1EFF,U+2000-206F,U+20A0-20CF,U+2100-214F}
@font-face{font-family:"LatSerif";src:url("%(f)s/NotoSerif-Bold.ttf");font-weight:700;unicode-range:U+0000-024F,U+1E00-1EFF,U+2000-206F,U+20A0-20CF,U+2100-214F}
""" % {'f': 'file://' + FONT_DIR}

# Paragraph / line styles.  size in pt, family stack, weight; used for BOTH measuring and rendering.
BODY_FAMILY = '"GrkSerif","GebRare","SongBody","HanExt","Noto Serif",serif'
STYLE_CSS = f"""
html{{-webkit-text-size-adjust:none}}
body{{margin:0;padding:0;font-family:{BODY_FAMILY};font-size:{FONT}pt;color:#000;
  line-break:normal;word-break:normal;overflow-wrap:normal;font-kerning:normal;
  font-variant-ligatures:none;text-rendering:geometricPrecision;font-synthesis:none}}
.ln{{position:absolute;left:0;top:0;height:{LINE}pt;line-height:{LINE}pt;white-space:nowrap;
  transform-origin:0 0}}
.meas{{position:absolute;left:0;top:0;line-height:{LINE}pt;text-align:left;visibility:hidden}}
b,.b{{font-weight:700}}
.sup{{font-size:7pt;line-height:0;position:relative;top:-3.4pt;color:#1f3a93}}
.sup a,a.mk{{color:#1f3a93}}
a{{color:inherit;text-decoration:none}}
/* paragraph styles */
.s-body{{font-size:{FONT}pt}}
.s-noindent{{font-size:{FONT}pt}}
.s-quote{{font-family:"GrkSerif","KaiTi","SongBody",serif;font-size:10pt}}
.s-center{{font-size:{FONT}pt}}
.s-right{{font-size:{FONT}pt}}
.s-secnum{{font-family:"GrkSerif","HeiTi","Noto Serif",serif;font-size:9.5pt;font-weight:500}}
.s-h1{{font-family:"HeiTi",sans-serif;font-size:17pt;font-weight:700}}
.s-h2{{font-family:"KaiTi",serif;font-size:14pt;font-weight:700}}
.s-h3{{font-family:"ZhengHei","HeiTi",sans-serif;font-size:12pt;font-weight:400}}
.s-h4{{font-family:"WenKai2","KaiTi",serif;font-size:11pt;font-weight:700}}
.s-h5{{font-family:"BaoSong","SongBody",serif;font-size:10.5pt;font-weight:700}}
.s-h6{{font-family:"WeiMi","HeiTi",sans-serif;font-size:10.5pt;font-weight:700}}
.s-h7{{font-family:"MingTi","SongBody",serif;font-size:10pt;font-weight:700}}
.s-h8{{font-family:"KaiM","KaiTi",serif;font-size:10pt;font-weight:700}}
.s-h9{{font-family:"DroidHei","HeiTi",sans-serif;font-size:9.5pt;font-weight:700}}
.emp{{-webkit-text-emphasis:filled dot;text-emphasis:filled dot;-webkit-text-emphasis-position:under right;text-emphasis-position:under right}}
.msup{{font-size:.7em;position:relative;top:-.4em;line-height:0}}
.msub{{font-size:.7em;position:relative;top:.28em;line-height:0}}
.msub2{{font-size:.5em;position:relative;top:.5em;line-height:0}}
.msup2{{font-size:.5em;position:relative;top:-1.25em;line-height:0}}
.msupsub{{font-size:.5em;position:relative;top:-.35em;line-height:0}}
.msubsup{{font-size:.5em;position:relative;top:-.1em;line-height:0}}
.ov{{border-top:.5pt solid;padding:0 .06em 0 .1em}}
.pgno{{font-size:.62em;color:#8a8a8a;letter-spacing:0;line-height:0;font-family:"Noto Serif",serif}}
.it{{font-family:"LatIt","GrkSerif","SongBody","HanExt","Noto Serif",serif;font-style:italic;line-height:0}}
.mth{{font-family:"MathOps","GrkSerif","SongBody","Noto Serif",serif;line-height:0}}
.vec{{font-family:"VecIt","LatIt",serif;font-style:italic;line-height:0}}
math{{font-family:"MathFont",math;font-weight:400;font-style:normal;letter-spacing:0;word-spacing:0}}
math .it{{text-transform:none}}
/* table cells: inline boxes of fixed width (em of the line font) */
.tw{{display:inline-block;vertical-align:baseline;white-space:nowrap}}
.w2{{width:2em}} .w3{{width:3em}} .w4{{width:4em}} .w5{{width:5em}} .w6{{width:6em}} .w7{{width:7em}} .w8{{width:8em}} .w9{{width:9em}} .w10{{width:10em}} .w11{{width:11em}} .w12{{width:12em}} .w13{{width:13em}} .w14{{width:14em}} .w15{{width:15em}} .w16{{width:16em}} .w17{{width:17em}} .w18{{width:18em}} .w19{{width:19em}} .w20{{width:20em}} .w21{{width:21em}} .w22{{width:22em}} .w23{{width:23em}} .w24{{width:24em}} .w25{{width:25em}} .w26{{width:26em}} .w27{{width:27em}} .w28{{width:28em}} .w29{{width:29em}} .w30{{width:30em}} .w31{{width:31em}} .w32{{width:32em}} .w33{{width:33em}} .w34{{width:34em}}
.s-kaibody{{font-family:"KaiTi","GrkSerif","SongBody",serif}}
.kai{{font-family:"KaiTi","GrkSerif","SongBody",serif;line-height:0}}
.s-refhead{{font-family:"HeiTi",sans-serif;font-size:10pt;font-weight:700}}
.fx{{white-space:nowrap;font-family:"GrkSerif","SongBody","Noto Serif",serif}}
.s-toc0{{font-family:"KaiTi",serif;font-size:11pt;font-weight:700}}
.s-toc0s{{font-family:"KaiTi",serif;font-size:10.5pt;font-weight:700}}
.s-toc1{{font-family:"HeiTi",sans-serif;font-size:10.5pt;font-weight:500}}
.s-mbook{{font-family:"HeiTi",sans-serif;font-size:12pt;font-weight:700}}
.s-mvol{{font-family:"KaiTi",serif;font-size:11pt;font-weight:700}}
.s-mtocnote{{font-family:"KaiTi",serif;font-size:9pt;color:#555}}
.s-mnote{{font-family:"KaiTi",serif;font-size:9pt;color:#444}}
.s-toc2{{font-size:10.5pt}}
.s-toc3{{font-size:10pt}}
.s-note{{font-size:8.5pt}}
.s-index{{font-size:8.5pt}}
.s-cip{{font-size:9pt}}
.s-idxhead{{font-family:"HeiTi",sans-serif;font-size:10pt;font-weight:700}}
.nn{{display:inline-block;width:3em;text-align:left;text-align-last:left}}
.nb{{display:inline-block;width:2em;text-align:left;text-align-last:left}}
.pn{{color:#1f3a93}}
.spk{{font-family:"GebRare","HeiTi",sans-serif;font-weight:400}}
.hei{{font-family:"GrkSerif","GebRare","HeiTi",sans-serif;font-weight:500}}
.hei.nohei,.nohei{{font-family:inherit;font-weight:inherit}}
.sm{{font-size:.86em}}
.ul{{text-decoration:underline;text-underline-offset:.15em}}
/* the grey box grows by shadows: vertical padding would move its glyphs 0.08 pt off the baseline */
.gbox{{background:#e4e4e4;border-radius:1.5pt;box-shadow:0 .08em 0 #e4e4e4,0 -.08em 0 #e4e4e4}}
.lat{{font-family:"LatSerif","GrkSerif","SongBody","HanExt",serif}}
.it.lat{{font-family:"LatIt","GrkSerif","SongBody","HanExt",serif;font-style:italic}}
.lnk{{color:#1f3a93}}
.url{{word-break:break-all;overflow-wrap:anywhere}}
.gua{{font-family:"GuaSym","SongBody",serif}}
.sym{{font-family:"SymFont","SongBody",serif}}
.rad{{font-family:"RadSerif","SongBody",serif}}
.spk,.hei,.sm,.lat,.gbox,.ul,.nohei,.gua,.sym,.rad{{line-height:0}}
.s-small{{font-size:9pt}}
.s-smallkai{{font-family:"KaiTi","GebRare","GrkSerif","SongBody",serif;font-size:9.5pt}}
.s-figcap{{font-family:"GrkSerif","GebRare","HeiTi",sans-serif;font-size:9pt;font-weight:500}}
.s-figsub{{font-family:"KaiTi","GebRare","GrkSerif","SongBody",serif;font-size:9pt;color:#222}}
.fig{{color:#1a44c8;border:.7pt solid #e2b400;padding:0 .35em;background:#fffbe6;border-radius:1pt;font-family:"HeiTi",sans-serif;font-size:9.5pt}}
"""

import re as _re
# The coined characters of 《哥德尔、艾舍尔、巴赫》 (U+AA9E–AAAF, the inverted G at U+E047) come from the ebook's own font in every face.
STYLE_CSS = _re.sub(r'font-family:(?!"GebRare"|inherit)', 'font-family:"GebRare",', STYLE_CSS)


# The face of an apostrophe inside a Latin word (model._APOS_HTML), set beside every font-family as --apos-ff: the CJK
# faces set ’ full width ('Nature’ s'), so it comes from AposSerif; faces with a proportional ’ of their own keep it.
_APOS_SKIP = {'GrkSerif', 'GebRare', 'HanExt', 'GuaSym', 'SymFont', 'RadSerif', 'DroidHei'}       # (no ’ in these: the next face sets it)
_APOS_OWN = {'KaiTi', 'ZhengHei', 'LatSerif', 'LatIt', 'Noto Serif', 'AposSerif'}


def _apos_ff(m):
    fams = m.group(1)
    first = next((f for f in (x.strip().strip('"\'') for x in fams.split(',')) if f not in _APOS_SKIP), '')
    return f'{m.group(0)};--apos-ff:{fams if first in _APOS_OWN else chr(34) + "AposSerif" + chr(34) + "," + fams}'


import re as _re_apos
STYLE_CSS = _re_apos.sub(r'font-family:(?!inherit)([^;}]+)', _apos_ff, STYLE_CSS)
