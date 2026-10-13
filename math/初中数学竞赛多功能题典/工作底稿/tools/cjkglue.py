import sys, os, statistics
sys.path.insert(0, os.path.dirname(__file__))
import pikepdf, engine as E
pdf = pikepdf.open('src/book.pdf'); bf = E.BookFonts(pdf)
res = []
for pn in range(int(sys.argv[1]), int(sys.argv[2]) + 1):
    pe = E.PageEdit(pdf, pn, bf)
    lines = {}
    for g in pe.glyphs:
        if g.size > 10:
            lines.setdefault(round(g.y, 1), []).append(g)
    for y, row in lines.items():
        row.sort(key=lambda g: g.x)
        cj = []; ec = []
        for a, b in zip(row, row[1:]):
            gap = b.x - (a.x + a.adv)
            ca = a.font.name.startswith('STSong'); cb = b.font.name.startswith('STSong')
            if ca and cb and a.uni not in '，。、；：？！（）“”' and b.uni not in '，。、；：？！（）“”':
                cj.append(gap)
            elif (ca and b.font.name.startswith('TeXGyreTermes') and b.uni.isdigit()) or (cb and a.font.name.startswith('TeXGyreTermes') and a.uni.isdigit()):
                ec.append(gap)
        if len(cj) > 5 and ec:
            c = statistics.median(cj); e = statistics.median(ec)
            r = (e - 2.727) / 1.364
            if r > 0.05:
                res.append((pn, y, round(c, 3), round(e, 3), round(r, 3), round(c / r, 3)))
for x in res[:40]:
    print(x)
print('median s_cjk', statistics.median([x[5] for x in res]), len(res))
