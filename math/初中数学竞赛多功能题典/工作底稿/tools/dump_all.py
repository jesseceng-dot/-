import sys, json, pymupdf
sys.path.insert(0,'tools')
import vis
doc=pymupdf.open('src/book.pdf')
allp={}
for pn in range(1,len(doc)+1):
    try:
        lines, glyphs, rules, draws = vis.page_lines(doc[pn-1])
    except Exception as e:
        print('ERR',pn,e); continue
    with open(f'lin/p{pn:03d}.txt','w') as f:
        for b,x,t in lines:
            f.write(f'{b:6.1f} {x:5.1f} | {t}\n')
    allp[pn]=[(round(b,1),round(x,1),t) for b,x,t in lines]
json.dump(allp,open('lin/all.json','w'),ensure_ascii=False)
