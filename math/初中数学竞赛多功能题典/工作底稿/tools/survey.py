"""Print paragraphs (exercise bodies / sub-paragraphs) of a page with geometry and TeX skeleton."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pymupdf, vis, totex
H = 841.89

def paragraphs(doc, pn):
    page = doc[pn-1]
    lines, glyphs, rules, draws = vis.page_lines(page)
    # lines: (baseline (mupdf y), x0, text)
    out = []
    for b, x0, t in lines:
        out.append((round(H - b, 2), round(x0, 2), t))
    return out

if __name__ == '__main__':
    doc = pymupdf.open(sys.argv[1])
    for pn in map(int, sys.argv[2:]):
        print('=== p%d' % pn)
        for yb, x0, t in paragraphs(doc, pn):
            print('%7.2f %6.2f | %s' % (yb, x0, t[:150]))
