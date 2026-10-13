"""overfull.py pdf page... : report text lines whose glyph advance extends past the right margin"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, engine as E
pdf = pikepdf.open(sys.argv[1]); bf = E.BookFonts(pdf)
for pn in map(int, sys.argv[2:]):
    pe = E.PageEdit(pdf, pn, bf)
    rows = {}
    for g in pe.glyphs:
        if g.size > 7 and 60 < g.y < 780:
            rows.setdefault(round(g.y), []).append(g)
    for y, r in sorted(rows.items(), reverse=True):
        m = max(r, key=lambda g: g.x + g.adv)
        ext = m.x + m.adv - E.RM
        if ext > 0.6 and not (m.font.name.startswith('STSong') and m.uni in '，。、；：？！）”' and ext < 6):
            print('p%d y=%d right=%.2f (+%.2f) %r' % (pn, y, m.x + m.adv, ext, m.uni))
