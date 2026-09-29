"""Page geometry, grid and font settings for the print edition (大32开, 五号/17pt grid)."""
import os

# ---- page (pt) -------------------------------------------------------------
PAGE_W = 397.0          # ≈140 mm
PAGE_H = 575.0          # ≈203 mm
TEXT_W = 294.0          # 28 characters of 10.5 pt
LEFT = (PAGE_W - TEXT_W) / 2   # left == right margin (51.5 pt = 18.2 mm)
FONT = 10.5             # body size (五号)
LINE = 17.0             # grid pitch: every vertical dimension is a multiple of this
NLINES = 27             # lines per page
TOP = 62.0              # top of first grid line, from page top
TEXT_H = NLINES * LINE  # 459 pt
BOTTOM_MARGIN = PAGE_H - TOP - TEXT_H  # 54 pt

# ---- build directories -------------------------------------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRATCH = os.environ.get('BOOK_SCRATCH',
                         '/tmp/claude-0/-home-user--/243b6d09-d8f0-55ab-9830-1d98f5b584ee/scratchpad')
FONT_DIR = os.environ.get('BOOK_FONT_DIR', os.path.join(SCRATCH, 'fonts'))
CHROME = os.environ.get('BOOK_CHROME', '/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
LINK_BASE = 'https://book.local/#'     # every internal link is emitted as this URI, rewritten to GoTo later

# ---- letter-spacing variants (em) used by the paginator to absorb line-count differences --
VARIANTS = [0.0, -0.012, 0.012, -0.024, 0.024]

FONTS_CSS = """
@font-face{font-family:"SongBody";src:url("%(f)s/SerifSC-Regular.ttf");font-weight:400}
@font-face{font-family:"SongBody";src:url("%(f)s/SerifSC-Bold.ttf");font-weight:700}
@font-face{font-family:"HeiTi";src:url("%(f)s/SansSC-Regular.ttf");font-weight:400}
@font-face{font-family:"HeiTi";src:url("%(f)s/SansSC-Medium.ttf");font-weight:500}
@font-face{font-family:"HeiTi";src:url("%(f)s/SansSC-Bold.ttf");font-weight:700}
@font-face{font-family:"HeiTi";src:url("%(f)s/SansSC-Black.ttf");font-weight:900}
@font-face{font-family:"KaiTi";src:url("%(f)s/LXGWWenKai-Regular.ttf");font-weight:400}
@font-face{font-family:"KaiTi";src:url("%(f)s/LXGWWenKai-Bold.ttf");font-weight:700}
@font-face{font-family:"GrkSerif";src:url("%(f)s/NotoSerif-Regular.ttf");font-weight:400;unicode-range:U+0370-03FF,U+1F00-1FFF}
@font-face{font-family:"GrkSerif";src:url("%(f)s/NotoSerif-Bold.ttf");font-weight:700;unicode-range:U+0370-03FF,U+1F00-1FFF}
""" % {'f': 'file://' + FONT_DIR}

# Paragraph / line styles.  size in pt, family stack, weight; used for BOTH measuring and rendering.
BODY_FAMILY = '"GrkSerif","SongBody","Noto Serif",serif'
STYLE_CSS = f"""
html{{-webkit-text-size-adjust:none}}
body{{margin:0;padding:0;font-family:{BODY_FAMILY};font-size:{FONT}pt;color:#000;
  line-break:strict;word-break:normal;overflow-wrap:normal;font-kerning:normal;
  font-variant-ligatures:none;text-rendering:geometricPrecision}}
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
.s-h3{{font-family:"HeiTi",sans-serif;font-size:12pt;font-weight:500}}
.s-h4{{font-family:"KaiTi",serif;font-size:11pt;font-weight:700}}
.s-h5{{font-family:"HeiTi",sans-serif;font-size:10.5pt;font-weight:400}}
.s-h6{{font-family:"KaiTi",serif;font-size:10.5pt;font-weight:700}}
.s-h7{{font-family:"HeiTi",sans-serif;font-size:10pt;font-weight:400}}
.s-toc1{{font-family:"HeiTi",sans-serif;font-size:10.5pt;font-weight:500}}
.s-toc2{{font-size:10.5pt}}
.s-toc3{{font-size:10pt}}
.s-note{{font-size:8.5pt}}
.s-index{{font-size:8.5pt}}
.s-idxhead{{font-family:"HeiTi",sans-serif;font-size:10pt;font-weight:700}}
.nn{{display:inline-block;width:3em;text-align:left}}
.fig{{color:#1a44c8;border:.7pt solid #e2b400;padding:0 .35em;background:#fffbe6;border-radius:1pt;font-family:"HeiTi",sans-serif;font-size:9.5pt}}
"""
