import sys, json, pymupdf
sys.path.insert(0,'tools')
import vis
doc=pymupdf.open('src/book.pdf')
out={}
for pn in range(1,len(doc)+1):
    vg,rules,dr=vis.visible_glyphs(doc[pn-1])
    out[pn]=[(g['c'],g['font'],round(g['size'],2),round(g['x0'],2),round(g['x1'],2),round(g['oy'],2),round(g['y0'],2),round(g['y1'],2),g.get('name')) for g in vg]
json.dump(out,open('glyphs.json','w'),ensure_ascii=False)
