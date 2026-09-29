"""Ask Chromium where it breaks lines.

Every paragraph is laid out as an ordinary block (left aligned, given width / first-line indent /
letter-spacing) and we read back, per character, which visual line it fell on.  The result is
{starts: [unit index where each line begins], nat: [natural width (pt) of each line], h: block height (pt)}.
"""
import os
import json
from playwright.sync_api import sync_playwright
from . import style

JS = r"""
async (specs) => {
  const root = document.getElementById('root');
  root.innerHTML = '';
  const divs = specs.map(s => {
    const d = document.createElement('div');
    d.className = 'meas ' + s.cls;
    d.style.width = s.width + 'pt';
    d.style.textIndent = s.indent + 'pt';
    d.style.letterSpacing = s.ls + 'em';
    d.style.lineHeight = s.lh + 'pt';
    d.innerHTML = s.html;
    root.appendChild(d);
    return d;
  });
  const PX = 96 / 72;
  const out = [];
  const range = document.createRange();
  for (let k = 0; k < divs.length; k++) {
    const d = divs[k], s = specs[k];
    const lhpx = s.lh * PX;
    const box = d.getBoundingClientRect();
    const top0 = box.top, left0 = box.left;
    const starts = [0], nat = [], lineMin = [], lineMax = [];
    let cur = 0, unit = 0, forced = false, minL = 1e9, maxR = -1e9;
    const flush = () => { nat.push(maxR > -1e8 ? (maxR - minL) / PX : 0); minL = 1e9; maxR = -1e9; };
    const walker = document.createTreeWalker(d, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    let n;
    while ((n = walker.nextNode())) {
      if (n.nodeType === 1) {
        if (n.tagName === 'BR') { unit += 1; forced = true; continue; }
        if (n.tagName === 'IMG') {
          const rc = n.getBoundingClientRect();
          const ln = Math.floor(((rc.top + rc.bottom) / 2 - top0) / lhpx);
          if (ln > cur || forced) { flush(); starts.push(unit); cur = Math.max(ln, cur + (forced ? 1 : 0)); forced = false; }
          minL = Math.min(minL, rc.left - (cur === 0 ? left0 + s.indent * PX : left0)); maxR = Math.max(maxR, rc.right - left0);
          unit += 1; continue;
        }
        continue;
      }
      const tn = n, str = tn.data;
      let i = 0;
      while (i < str.length) {
        const cp = str.codePointAt(i), w = cp > 0xffff ? 2 : 1;
        range.setStart(tn, i); range.setEnd(tn, i + w);
        const rc = range.getBoundingClientRect();
        if (rc.width > 0 || rc.height > 0) {
          const ln = Math.floor(((rc.top + rc.bottom) / 2 - top0) / lhpx);
          if (ln > cur || (forced && ln >= cur)) {
            if (ln > cur) { flush(); starts.push(unit); cur = ln; }
            forced = false;
          }
          if (str[i] !== ' ') { minL = Math.min(minL, rc.left); maxR = Math.max(maxR, rc.right); }
        }
        unit += 1; i += w;
      }
    }
    flush();
    // natural width is measured from the first ink to the last ink; convert to "used width"
    out.push({starts, nat, h: box.height / PX, units: unit});
  }
  root.innerHTML = '';
  return out;
}
"""

PAGE_HTML = """<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><style>%s%s</style></head>
<body><div id="root"></div>
<span style="font-family:SongBody">中</span><b style="font-family:SongBody">中</b>
<span style="font-family:HeiTi">中</span><b style="font-family:HeiTi">中</b>
<span style="font-family:KaiTi">中</span><b style="font-family:KaiTi">中</b>
<span style="font-family:GrkSerif">α</span><b style="font-family:GrkSerif">α</b>
</body></html>"""


class Measurer:
    def __init__(self):
        self._pw = sync_playwright().start()
        self._b = self._pw.chromium.launch(executable_path=style.CHROME, args=['--no-sandbox'])
        self._pg = self._b.new_page()
        path = os.path.join(style.SCRATCH, 'measure.html')
        with open(path, 'w', encoding='utf8') as f:
            f.write(PAGE_HTML % (style.FONTS_CSS, style.STYLE_CSS))
        self._pg.goto('file://' + path)
        self._pg.evaluate('document.fonts.ready.then(()=>true)')
        self._pg.wait_for_timeout(300)

    def measure(self, specs, batch=150):
        res = []
        for i in range(0, len(specs), batch):
            res += self._pg.evaluate(JS, specs[i:i + batch])
        return res

    def close(self):
        try:
            self._b.close()
        finally:
            self._pw.stop()
