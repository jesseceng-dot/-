"""Mechanical proof-reading scan of one unpacked book: prints suspicious spots by category (doubled characters and words,
common wrong characters, punctuation runs, unbalanced brackets, spaces inside Chinese, half-width punctuation,
digit look-alikes, private-use characters, Cyrillic look-alikes, single dashes and ellipses, traditional characters in a
simplified book and the reverse, paragraphs broken in mid-sentence).  Every hit is a candidate only: read it in context.

    BOOK_SCRATCH=<dir> [BOOK_TC=1] [SCAN_MAX=40] python -m tools.proof_scan
"""
import os, re, sys, glob, collections
from . import bk_extract as BE
try:
    import opencc
    t2s = opencc.OpenCC('t2s'); s2t = opencc.OpenCC('s2t')
except ImportError:                       # (pip install opencc-python-reimplemented) -- without it the script/variant check is skipped
    t2s = s2t = None
TC = os.environ.get('BOOK_TC') == '1'
OE = os.environ['BOOK_SCRATCH'] + '/unpack/x/mobi8/OEBPS/Text'
parts = sorted(os.path.basename(f)[:-6] for f in glob.glob(OE + '/part*.xhtml'))
CJK = r'一-鿿㐀-䶿'
AA_OK = set('常往渐刚仅稍慢一人天年处事个种层重纷匆频默悄偷轻静久每时步隐微深紧牢白多好大小早远高足整恰统家户区草星爸妈哥姐弟妹奶爷宝谢看想说试谈等'
            '粼淙熙皑斑涓娓侃喋孜栩奄凛惴耿悻戚铮翩冉蒸欣蹒熊巍赫芸莘泱洋浩茫苍沉津楚翼彬济累滚荡晃颤哗咚哒嗡嗒呱哈嘻呵咯嘿啦喃嘀嘟咕呜'
            '历勃蓬郁葱窃凄惶惶腾汩潺漫冥昭隆夭蔼姗袅亭婷嫣灼迢悠攘熙碌庸碌孑萋兢喁憧懵昏混朦胧浑噩惺忪匆')
rep = collections.defaultdict(list)
def add(cat, loc, text, i, j=None):
    j = j if j is not None else i + 2
    rep[cat].append(f'{loc}  …{text[max(0, i - 14):j + 14]}…')
TYPOS = ['己经', '自已', '巳经', '末来', '未尾', '既使', '即然', '竟争', '必竞', '竞然', '毕竞', '一但', '不径而走', '迫不急待', '再接再励', '一愁莫展', '默守成规',
         '谈笑风声', '甘败下风', '既往不究', '貌和神离', '按装', '部署'[:0] or '布署', '渡过难关'[:0] or '度过难关', '暴燥', '烦燥', '急燥', '干躁', '枯躁', '松驰',
         '针贬', '幅射', '辐员', '重迭', '迭加'[:0] or '迭起'[:0] or '叠起'[:0] or '箫条', '萧洒'[:0] or '潇条', '寒喧', '宣泻', '发韧', '震憾', '撼动'[:0] or '憾动',
         '泄密'[:0] or '泻密', '编篡', '篡写', '赝品'[:0] or '膺品', '惦量', '掂记', '粗旷', '磬竹难书', '入场卷', '优惠卷', '国藉', '书藉', '狼籍', '一张一驰',
         '出奇不意', '名门旺族', '黄梁', '金榜提名', '世外桃园', '走头无路', '直接了当', '一股作气', '鬼鬼崇崇', '作祟'[:0] or '做祟', '的确'[:0] or '的却',
         '即使'[:0] or '既便', '既将', '即往不咎', '其它'[:0] or '起它', '在接再', '想像'[:0] or '象像', '是否'[:0] or '事否', '不径', '截止'[:0] or '截至目'[:0] or '戳止',
         '凑和', '掺和'[:0] or '搀合', '蛰伏'[:0] or '蜇伏', '肆无忌殚', '天翻地复', '提纲携领', '一诺千斤', '坐阵', '座阵', '坐落'[:0] or '座落', '决窍', '诀别'[:0] or '决别',
         '侯选', '等侯', '气侯', '时侯', '问侯', '侯车', '拨苗', '选拔'[:0] or '选拨', '提拨', '海拨', '拨河', '分折', '剖折', '折衷'[:0] or '析衷', '辩别', '分辩'[:0] or '辨论',
         '辨护', '争辨', '辩证'[:0] or '辨证法', '赢弱', '赢利'[:0] or '嬴利', '赔尝', '偿识'[:0] or '尝识', '崇祟', '鬼祟'[:0] or '鬼崇', '流览', '浏览'[:0] or '留览',
         '那怕', '那里'[:0] or '那儿'[:0] or '哪末', '那末'[:0] or '那么'[:0] or '甚么'[:0] or '什么'[:0] or '一付', '一幅'[:0] or '一副画', '幅度'[:0] or '副度',
         '材料'[:0] or '才料', '人材'[:0] or '人才'[:0] or '既然'[:0] or '记然', '已然'[:0] or '己然', '自己'[:0] or '自巳', '巳经', '巳然', '已已',
         '的的确确'[:0] or '的的', '了了'[:0] or '了了', '在在', '是是', '和和', '与与', '为为', '对对', '这这', '那那', '把把', '被被', '将将', '从从', '向向', '也也', '都都', '就就', '还还', '又又', '不不', '要要', '会会', '能能', '有有', '没没', '而而', '但但', '则则', '并并', '因因', '所所', '其其', '之之', '以以', '于于',
         '國家國家'[:0] or '這這', '們們', '個個'[:0] or '個人個人'[:0] or '的的']
TYPOS = sorted(set(t for t in TYPOS if t))
prev = None
for part in parts:
    try:
        its = BE.items(part)
    except Exception as e:
        print('ERR', part, e); continue
    for k, it in enumerate(its):
        runs = it.get('runs') or []
        t = ''.join(r['t'] for r in runs if not r.get('i'))
        loc = f'{part}:{k}:{it["k"]}'
        if not t:
            prev = None; continue
        for m in re.finditer(rf'([{CJK}])\1', t):
            ch = m.group(1)
            if ch not in AA_OK:
                add('dup-char', loc, t, m.start())
        for m in re.finditer(rf'([{CJK}]{{2,4}})\1', t):
            add('dup-word', loc, t, m.start(), m.end())
        for w in TYPOS:
            i = t.find(w)
            while i >= 0:
                add('typo:' + w, loc, t, i, i + len(w)); i = t.find(w, i + 1)
        for m in re.finditer(r'[，。、；：！？]{2,}|，」|，”(?=[，。])|。，|，。|、、|；；|：：', t):
            if m.group() not in ('？！', '！？', '？？', '！！', '。」'):
                add('punct-run', loc, t, m.start(), m.end())
        for a, b in (('（', '）'), ('《', '》'), ('“', '”'), ('‘', '’'), ('「', '」'), ('『', '』'), ('〈', '〉'), ('(', ')'), ('[', ']'), ('【', '】')):
            if t.count(a) != t.count(b):
                add(f'unbalanced {a}{b}', loc, t, 0, min(len(t), 60))
        for m in re.finditer(rf'[{CJK}][  ]+[{CJK}]', t):
            add('space-in-cjk', loc, t, m.start(), m.end())
        for m in re.finditer(rf'[{CJK}][,;:!?](?=[{CJK}“”「」]|$)|[{CJK}]\.(?=[{CJK}])|[{CJK}]\((?=[{CJK}])|(?<=[{CJK}])\)', t):
            add('ascii-punct', loc, t, m.start(), m.end())
        for m in re.finditer(r'\d[lIO]\d|[lIO]\d{3}|\d{3}[lIO](?![A-Za-z])', t):
            add('digit-lookalike', loc, t, m.start(), m.end())
        for m in re.finditer(r'[-�□]', t):
            add('pua/replacement/□', loc, t, m.start())
        for m in re.finditer(r'[Ѐ-ӿ]', t):
            add('cyrillic', loc, t, m.start())
        for m in re.finditer(r'(?<!—)—(?!—)', t):
            if re.search(rf'[{CJK}]—[{CJK}]', t[max(0, m.start()-1):m.end()+1]):
                add('single-dash', loc, t, m.start())
        for m in re.finditer(r'(?<!…)…(?!…)', t):
            add('single-ellipsis', loc, t, m.start())
        cs = set(t) if t2s else set()
        for ch in cs:
            if not re.match(rf'[{CJK}]', ch):
                continue
            if TC:
                if t2s.convert(ch) == ch and s2t.convert(ch) != ch:
                    add('simplified-in-TC:' + ch, loc, t, t.index(ch))
            else:
                if t2s.convert(ch) != ch and s2t.convert(t2s.convert(ch)) == ch and ch not in '著乾後於餘麽闆夥嚮瞭隻鍾':
                    add('traditional-in-SC:' + ch, loc, t, t.index(ch))
        # broken paragraph: a body paragraph that stops mid-sentence and the next body paragraph continues it
        if prev and it['k'] == 'p' and prev[2] == 'p':
            pt = prev[1]
            if pt and not re.search(r'[。！？…”」』）)：；:.!?\]】—―─·]$|^\S{0,14}$', pt) and not re.match(r'^[　\s]*[（(]?[一二三四五六七八九十\d]', t):
                add('broken-para?', prev[0], pt[-30:] + ' ¶ ' + t[:30], len(pt[-30:]))
        prev = (loc, t, it['k'])
for cat in sorted(rep, key=lambda c: (-len(rep[c]), c)):
    xs = rep[cat]
    print(f'## {cat}  ({len(xs)})')
    for x in xs[:int(os.environ.get('SCAN_MAX', '40'))]:
        print('   ', x)
