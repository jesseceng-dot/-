"""排版规范化：python3 layout_normalize.py <解包后的docx目录>
统一字体字号、行网格（15.6pt×48行）、标题层级、表格/插图/公式尺寸。"""
import re, sys, math
from lxml import etree
D=sys.argv[1]   # unpacked dir
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M='http://schemas.openxmlformats.org/officeDocument/2006/math'
WP='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
ns={'w':W,'m':M,'wp':WP,'a':A}
def q(t): p,n=t.split(':'); return '{%s}%s'%({'w':W,'m':M,'wp':WP,'a':A}[p],n)
def wv(e,a='val'): return e.get(q('w:'+a))
def sub(parent,tag,**attrs):
    e=etree.SubElement(parent,q(tag))
    for k,v in attrs.items(): e.set(q('w:'+k),v)
    return e
# ---------- spec ----------
PITCH=312            # twips = 15.6 pt grid (Word single spacing for 10.5pt)
LINES=48
MARG=(16838-PITCH*LINES)//2   # 939
BODY_SZ='21'; SMALL_SZ='18'   # 10.5pt / 9pt
SONG='宋体'; HEI='黑体'; KAI='楷体'; LAT='Times New Roman'; LAT_H='Arial'
GRAY='404040'
HEAD={'1':('36',True),'21':('30',False),'31':('24',False),'4':('21',False)}  # size, centered
# ---------- helpers ----------
PPR_ORDER=['pStyle','keepNext','keepLines','pageBreakBefore','framePr','widowControl','numPr','suppressLineNumbers','pBdr','shd','tabs','suppressAutoHyphens','kinsoku','wordWrap','overflowPunct','topLinePunct','autoSpaceDE','autoSpaceDN','bidi','adjustRightInd','snapToGrid','spacing','ind','contextualSpacing','mirrorIndents','suppressOverlap','jc','textDirection','textAlignment','textboxTightWrap','outlineLvl','divId','cnfStyle','rPr','sectPr','pPrChange']
RPR_ORDER=['rStyle','rFonts','b','bCs','i','iCs','caps','smallCaps','strike','dstrike','outline','shadow','emboss','imprint','noProof','snapToGrid','vanish','webHidden','color','spacing','w','kern','position','sz','szCs','highlight','u','effect','bdr','shd','fitText','vertAlign','rtl','cs','em','lang','eastAsianLayout','specVanish','oMath']
def set_child(parent,tag,order,attrs=None):
    """replace/insert child w:tag keeping schema order"""
    ln=tag
    for c in parent.findall(q('w:'+ln)): parent.remove(c)
    e=etree.Element(q('w:'+ln))
    for k,v in (attrs or {}).items(): e.set(q('w:'+k),v)
    idx=order.index(ln); pos=len(parent)
    for i,c in enumerate(parent):
        cl=etree.QName(c).localname
        if cl in order and order.index(cl)>idx: pos=i; break
    parent.insert(pos,e); return e
def rm(parent,*tags):
    for t in tags:
        for c in parent.findall(q('w:'+t)): parent.remove(c)
def pPr(p):
    e=p.find('w:pPr',ns)
    if e is None: e=etree.Element(q('w:pPr')); p.insert(0,e)
    return e
def rPr_of(r):
    e=r.find('w:rPr',ns)
    if e is None:
        e=etree.Element(q('w:rPr'))
        # m:r: rPr goes after m:rPr ; w:r: first
        if r.tag==q('m:r'):
            mr=r.find('m:rPr',ns); r.insert(1 if mr is not None else 0,e)
        else: r.insert(0,e)
    return e
def text_of(p): return ''.join(t.text or '' for t in p.iter(q('w:t'),q('m:t')))
def plain_text(p): return ''.join(t.text or '' for t in p.iter(q('w:t')) if not any(a.tag.startswith('{%s}'%M) for a in t.iterancestors()))
def runs(p):
    return [r for r in p.iter(q('w:r')) ]
def mruns(p): return list(p.iter(q('m:r')))
def is_math_w(r): return any(a.tag.startswith('{%s}'%M) for a in r.iterancestors())

doc=etree.parse(D+'/word/document.xml'); root=doc.getroot(); body=root.find('w:body',ns)
stats={}
def inc(k): stats[k]=stats.get(k,0)+1

# ---------- classify body-level blocks ----------
blocks=list(body)
def style(p):
    s=p.find('w:pPr/w:pStyle',ns); return wv(s) if s is not None else ''
def is_spacer(p):
    sp=p.find('w:pPr/w:spacing',ns)
    return p.tag==q('w:p') and sp is not None and wv(sp,'line')=='96' and not text_of(p).strip()
def is_pagebreak_para(p):
    return p.tag==q('w:p') and any(wv(b,'type')=='page' for b in p.iter(q('w:br'))) and not text_of(p).strip()
def gray_runs(p):
    rs=[r for r in p.iter(q('w:r')) if not is_math_w(r) and (r.find('w:t',ns) is not None)]
    if not rs: return False
    g=[r for r in rs if r.find('w:rPr/w:color',ns) is not None and wv(r.find('w:rPr/w:color',ns)) in ('555555','666666','777777')]
    return len(g)>=max(1,len([r for r in rs if (r.find('w:t',ns).text or '').strip()]))
def centered(p):
    j=p.find('w:pPr/w:jc',ns); return j is not None and wv(j)=='center'

# chapter page breaks: remove page-break-only paragraphs, set pageBreakBefore on chapter headings
first_h1=True
for p in list(body):
    if is_pagebreak_para(p): body.remove(p); inc('pagebreak_para_removed')
for p in body.iter(q('w:p')):
    pp=p.find('w:pPr',ns)
    if pp is not None and pp.find('w:pageBreakBefore',ns) is not None and style(p)=='21':
        pp.remove(pp.find('w:pageBreakBefore',ns)); inc('h2_pagebreak_removed')

blocks=list(body)
for i,b in enumerate(blocks):
    if b.tag!=q('w:p'): continue
    st=style(b)
    if st=='1':
        if first_h1: first_h1=False
        else: set_child(pPr(b),'pageBreakBefore',PPR_ORDER); inc('h1_pbb')

# spacer handling
blocks=list(body)
for i,b in enumerate(blocks):
    if b.tag==q('w:p') and is_spacer(b):
        nxt=blocks[i+1] if i+1<len(blocks) else None
        prv=blocks[i-1] if i>0 else None
        if nxt is None or (nxt.tag==q('w:p') and style(nxt) in HEAD) or nxt.tag==q('w:sectPr'):
            body.remove(b); inc('spacer_removed')
        else:
            pp=b.find('w:pPr',ns); rm(pp,'spacing'); inc('spacer_kept')
            set_child(pp,'rPr',PPR_ORDER)   # empty rPr fine

# ---------- paragraphs ----------
def clean_run_fmt(r,keep_color=False):
    rp=r.find('w:rPr',ns)
    if rp is None: return
    rm(rp,'sz','szCs','rFonts' if not is_math_w(r) and r.tag==q('w:r') else '__none__')
    if not keep_color: rm(rp,'color')
def set_run(r,sz=None,east=None,ascii=None,color=None,bold=None):
    rp=rPr_of(r)
    if east or ascii:
        a={}
        if ascii: a.update({'ascii':ascii,'hAnsi':ascii})
        if east: a.update({'eastAsia':east})
        set_child(rp,'rFonts',RPR_ORDER,a)
    if color: set_child(rp,'color',RPR_ORDER,{'val':color})
    if sz: set_child(rp,'sz',RPR_ORDER,{'val':sz}); set_child(rp,'szCs',RPR_ORDER,{'val':sz})
    if bold is False: rm(rp,'b','bCs')

def all_runs(p):  # w:r (text, incl. inside m) and m:r
    out=[]
    for r in p.iter(q('w:r'),q('m:r')):
        if r.tag==q('w:r') and is_math_w(r): continue
        out.append(r)
    return out

for p in body.iter(q('w:p')):
    in_tc=any(a.tag==q('w:tc') for a in p.iterancestors())
    in_hdr_row=False
    if in_tc:
        tr=next(a for a in p.iterancestors() if a.tag==q('w:tr'))
        in_hdr_row=tr.find('w:trPr/w:tblHeader',ns) is not None
    st=style(p); pp=pPr(p)
    has_img=p.find('.//w:drawing',ns) is not None
    has_disp=p.find('m:oMathPara',ns) is not None
    txt=plain_text(p).strip()
    if st in HEAD:
        rm(pp,'spacing','jc','ind')
        prp=pp.find('w:rPr',ns)
        if prp is not None: pp.remove(prp)
        for r in all_runs(p):
            rp=r.find('w:rPr',ns)
            if rp is None: continue
            if r.tag==q('w:r'): rm(rp,'rFonts','sz','szCs','b','bCs','color')
            else: rm(rp,'sz','szCs')
        inc('heading')
        continue
    if in_tc:
        rm(pp,'spacing','ind')
        if pp.find('w:jc',ns) is None: set_child(pp,'jc',PPR_ORDER,{'val':'left'})
        for r in all_runs(p):
            if r.tag==q('m:r'):
                set_run(r,sz=SMALL_SZ)
            else:
                rp=r.find('w:rPr',ns)
                if rp is not None: rm(rp,'color')
                if in_hdr_row: set_run(r,sz=SMALL_SZ,east=HEI,ascii=LAT_H,bold=False)
                else:
                    if rp is not None: rm(rp,'rFonts')
                    set_run(r,sz=SMALL_SZ)
        inc('cell_para'); continue
    # body level
    if has_img:
        rm(pp,'spacing','ind'); set_child(pp,'jc',PPR_ORDER,{'val':'center'})
        inc('img_para'); continue
    if gray_runs(p) and plain_text(p).strip().startswith('类别：'):
        for r in p.iter(q('w:r')):
            rp=r.find('w:rPr',ns)
            if rp is not None: rm(rp,'color','sz','szCs','rFonts')
    if gray_runs(p):
        cap=centered(p)
        rm(pp,'spacing','ind')
        if not cap: set_child(pp,'ind',PPR_ORDER,{'firstLineChars':'200','firstLine':'360'})
        for r in all_runs(p):
            if r.tag==q('m:r'): set_run(r,sz=SMALL_SZ,color=GRAY)
            else:
                rp=r.find('w:rPr',ns)
                if rp is not None: rm(rp,'rFonts')
                set_run(r,sz=SMALL_SZ,color=GRAY,east=(None if cap else KAI))
        inc('caption' if cap else 'note'); continue
    # normal body / display math
    rm(pp,'spacing')
    for r in all_runs(p):
        rp=r.find('w:rPr',ns)
        if rp is None: continue
        if r.tag==q('m:r'): rm(rp,'sz','szCs')
        else: rm(rp,'sz','szCs','rFonts')
    prp=pp.find('w:rPr',ns)
    if prp is not None: rm(prp,'sz','szCs','rFonts')
    if has_disp and not txt:
        rm(pp,'ind'); inc('display')
    elif not txt and not has_disp and p.find('.//m:oMath',ns) is None:
        inc('empty')
    else:
        if not centered(p):
            set_child(pp,'ind',PPR_ORDER,{'firstLineChars':'200','firstLine':'420'})
            if any(wv(b,'type') in (None,'textWrapping') for b in p.iter(q('w:br'))): set_child(pp,'jc',PPR_ORDER,{'val':'left'})
        inc('body')
    # keep image with its caption
blocks=list(body)
for i,b in enumerate(blocks[:-1]):
    if b.tag==q('w:p') and b.find('.//w:drawing',ns) is not None:
        n=blocks[i+1]
        if n.tag==q('w:p') and gray_runs(n) and centered(n):
            set_child(pPr(b),'keepNext',PPR_ORDER); inc('img_keep_caption')

# CJK characters inside math zones use the East Asian body font
import unicodedata
for mr in body.iter(q('m:r')):
    t=''.join(x.text or '' for x in mr.iter(q('m:t')))
    if any(0x2E80<=ord(c)<=0x9FFF or 0xFF00<=ord(c)<=0xFFEF for c in t):
        rp=rPr_of(mr); f=rp.find('w:rFonts',ns)
        if f is None: f=set_child(rp,'rFonts',RPR_ORDER)
        f.set(q('w:eastAsia'),SONG); inc('math_cjk_font')
# ---------- tables ----------
def est_lines(tc):
    w=tc.find('w:tcPr/w:tcW',ns); wd=int(wv(w,'w')) if w is not None and wv(w,'type')=='dxa' else 3000
    cpl=max(4,(wd-170)/180.0)
    tot=0
    for p in tc.findall('w:p',ns):
        t=text_of(p); units=sum(1 if ord(c)>0x2E80 else 0.55 for c in t)
        # fractions / big operators make a line taller -> count 2
        tall=len(p.findall('.//m:f',ns))+len(p.findall('.//m:nary',ns))
        segs=1+len([b for b in p.iter(q('w:br'))])
        tot+=max(segs, math.ceil(units/cpl)) + (1 if tall else 0)
    return tot
for tbl in body.iter(q('w:tbl')):
    for tr in tbl.findall('w:tr',ns):
        trp=tr.find('w:trPr',ns)
        if trp is None: continue
        for h in trp.findall('w:trHeight',ns): trp.remove(h); inc('trHeight_removed')
        cs=trp.find('w:cantSplit',ns)
        if cs is not None and trp.find('w:tblHeader',ns) is None:
            mx=max([est_lines(tc) for tc in tr.findall('w:tc',ns)] or [1])
            if mx>3: trp.remove(cs); inc('cantSplit_removed')
    for mar in tbl.iter(q('w:tcMar')):
        for side in ('top','bottom'):
            e=mar.find('w:'+side,ns)
            if e is not None: e.set(q('w:w'),'0')

# ---------- images ----------
EMU_PT=12700
glyph={'image3.png':32,'image4.png':30,'image5.png':31,'image6.png':31,'image7.png':31,'image22.png':32,
       'image23.png':31,'image24.png':32,'image25.png':29,'image26.png':35,'image27.png':30}
INK_PT=7.4
fixedw={}  # width in EMU for latin-only figures
for n in range(10,22): fixedw['image%d.png'%n]=1260000
fixedw.update({'image28.png':1512000,'image29.png':1512000,'image30.png':2520000,'image31.png':2520000})
rels=etree.parse(D+'/word/_rels/document.xml.rels').getroot()
rid2t={r.get('Id'):r.get('Target').split('/')[-1] for r in rels}
from PIL import Image
TEXTW=(11906-2*964)*635
for inl in body.iter(q('wp:inline')):
    blip=inl.find('.//a:blip',ns); t=rid2t[blip.get('{%s}embed'%R)]
    pw,ph=Image.open(D+'/word/media/'+t).size
    ext=inl.find('wp:extent',ns); cx=int(ext.get('cx')); cy=int(ext.get('cy'))
    if t in glyph: ncx=pw*INK_PT/glyph[t]*EMU_PT
    elif t in fixedw: ncx=fixedw[t]
    else: ncx=cx
    ncx=min(ncx,TEXTW)
    ncy=ncx*ph/pw
    # snap height to just under a whole number of grid lines (scale change <= 8%)
    pitch_emu=PITCH*635; slack=40*635
    n_lines=max(1,round((ncy+slack)/pitch_emu))
    target=n_lines*pitch_emu-slack
    if abs(target/ncy-1)>0.08:
        n_lines=math.ceil((ncy+slack)/pitch_emu); target=n_lines*pitch_emu-slack
        if target/ncy-1>0.08: target=ncy
    f=target/ncy; ncx*=f; ncy=target
    ncx,ncy=int(ncx),int(ncy)
    ext.set('cx',str(ncx)); ext.set('cy',str(ncy))
    for x in inl.iter(q('a:ext')): x.set('cx',str(ncx)); x.set('cy',str(ncy))
    inc('img_scaled')

# ---------- section ----------
sect=body.find('w:sectPr',ns)
pm=sect.find('w:pgMar',ns); pm.set(q('w:top'),str(MARG)); pm.set(q('w:bottom'),str(MARG))
pm.set(q('w:header'),'454'); pm.set(q('w:footer'),'454')
dg=sect.find('w:docGrid',ns); dg.set(q('w:type'),'lines'); dg.set(q('w:linePitch'),str(PITCH))
doc.write(D+'/word/document.xml',xml_declaration=True,encoding='UTF-8',standalone=True)

# ---------- styles ----------
sty=etree.parse(D+'/word/styles.xml'); sr=sty.getroot()
dd=sr.find('w:docDefaults',ns)
rpd=dd.find('w:rPrDefault/w:rPr',ns)
set_child(rpd,'rFonts',RPR_ORDER,{'ascii':LAT,'eastAsia':SONG,'hAnsi':LAT,'cs':LAT})
set_child(rpd,'sz',RPR_ORDER,{'val':BODY_SZ}); set_child(rpd,'szCs',RPR_ORDER,{'val':BODY_SZ})
set_child(rpd,'lang',RPR_ORDER,{'val':'en-US','eastAsia':'zh-CN','bidi':'ar-SA'})
ppd=dd.find('w:pPrDefault/w:pPr',ns)
set_child(ppd,'spacing',PPR_ORDER,{'after':'0','line':'240','lineRule':'auto'})
def S(sid): return sr.find('w:style[@w:styleId="%s"]'%sid,ns)
def spr(s,tag):
    e=s.find('w:'+tag,ns)
    if e is None:
        e=etree.SubElement(s,q('w:'+tag))
    return e
n=S('a1'); p=spr(n,'pPr'); r=spr(n,'rPr')
for c in list(p): p.remove(c)
set_child(p,'widowControl',PPR_ORDER,{'val':'0'})
set_child(p,'spacing',PPR_ORDER,{'before':'0','after':'0','line':'240','lineRule':'auto'})
set_child(p,'jc',PPR_ORDER,{'val':'both'})
for c in list(r): r.remove(c)
set_child(r,'rFonts',RPR_ORDER,{'ascii':LAT,'eastAsia':SONG,'hAnsi':LAT,'cs':LAT})
set_child(r,'kern',RPR_ORDER,{'val':'2'})
set_child(r,'sz',RPR_ORDER,{'val':BODY_SZ}); set_child(r,'szCs',RPR_ORDER,{'val':BODY_SZ})
HSP={'1':('0','100'),'21':('100','50'),'31':('50','0'),'4':('0','0')}
for sid,(sz,cent) in HEAD.items():
    s=S(sid); p=spr(s,'pPr'); r=spr(s,'rPr')
    rm(p,'spacing','jc','keepNext','keepLines')
    set_child(p,'keepNext',PPR_ORDER); set_child(p,'keepLines',PPR_ORDER)
    b,a=HSP[sid]
    set_child(p,'spacing',PPR_ORDER,{'beforeLines':b,'before':str(int(b)*PITCH//100),'afterLines':a,'after':str(int(a)*PITCH//100),'line':'240','lineRule':'auto'})
    if cent: set_child(p,'jc',PPR_ORDER,{'val':'center'})
    else: set_child(p,'jc',PPR_ORDER,{'val':'left'})
    for c in list(r): r.remove(c)
    set_child(r,'rFonts',RPR_ORDER,{'ascii':LAT_H,'eastAsia':HEI,'hAnsi':LAT_H,'cs':LAT_H})
    set_child(r,'color',RPR_ORDER,{'val':'000000'})
    set_child(r,'kern',RPR_ORDER,{'val':'2'})
    set_child(r,'sz',RPR_ORDER,{'val':sz}); set_child(r,'szCs',RPR_ORDER,{'val':sz})
# linked character styles of headings
for sid,cid in [('1','10'),('21','22'),('31','32'),('4','40')]:
    c=S(cid)
    if c is not None:
        r=spr(c,'rPr')
        for x in list(r): r.remove(x)
        set_child(r,'rFonts',RPR_ORDER,{'ascii':LAT_H,'eastAsia':HEI,'hAnsi':LAT_H,'cs':LAT_H})
        set_child(r,'sz',RPR_ORDER,{'val':HEAD[sid][0]}); set_child(r,'szCs',RPR_ORDER,{'val':HEAD[sid][0]})
# header / footer styles: no grid snapping, 9pt
for sid in ('a5','a7'):
    s=S(sid)
    if s is None: continue
    p=spr(s,'pPr'); set_child(p,'snapToGrid',PPR_ORDER,{'val':'0'})
    r=spr(s,'rPr'); set_child(r,'sz',RPR_ORDER,{'val':SMALL_SZ}); set_child(r,'szCs',RPR_ORDER,{'val':SMALL_SZ})
sty.write(D+'/word/styles.xml',xml_declaration=True,encoding='UTF-8',standalone=True)

# header/footer runs: 9pt, keep gray
for f in ('header1.xml','footer1.xml'):
    t=etree.parse(D+'/word/'+f)
    for p in t.getroot().iter(q('w:p')):
        pp=pPr(p); set_child(pp,'snapToGrid',PPR_ORDER,{'val':'0'})
        if f=='header1.xml':
            set_child(pp,'pBdr',PPR_ORDER)
            bd=pp.find('w:pBdr',ns); b=etree.SubElement(bd,q('w:bottom'))
            for k,v in {'val':'single','sz':'4','space':'1','color':'808080'}.items(): b.set(q('w:'+k),v)
            set_child(pp,'jc',PPR_ORDER,{'val':'center'})
        for r in p.iter(q('w:r')):
            rp=r.find('w:rPr',ns)
            if rp is not None and rp.find('w:sz',ns) is not None:
                set_child(rp,'sz',RPR_ORDER,{'val':SMALL_SZ})
    t.write(D+'/word/'+f,xml_declaration=True,encoding='UTF-8',standalone=True)
print(stats)
