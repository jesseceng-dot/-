"""《康德文集（注释版）》文字层面的修复：私用区字符、多余空格、行末连字符、希腊文、内联小图（公式/着重号文字）。

原则与黑格尔各书相同：只改“电子书转换时产生的明显错误”，并在 docs/kant/dispositions.md 里逐类列出；有疑问的保持原样。
"""
import re
from .model import run, merge_runs, BR, OBJ

# ------------------------------------------------------------------------------------------ characters
# Kindle 私用区字符（用不同册里同一段文字的正常写法对照确认）
PUA = {
    '': 'ä', '': 'â', '': 'ô', '': 'ß', '': 'Ä', '': 'ç',
    '': '-', '': '.', '': '’', '': '*',
    '': 'ⅩⅢ', '': 'ⅩⅣ',      # 罗马数字 13、14（第 4/5 册同一处正文写作 ⅩⅢ、ⅩⅣ）
}
CHARS = {
    '﹒': '.',            # 小写句点 ﹒ 用作缩写点（G﹒Chr﹒Recard）
    '＜': '《',            # 书名号写成了全角小于号（源里的 ＜ 只有这一种用法）；大于号见 _RE_GT
    '‐': '-',            # U+2010 连字符 -> ASCII（下面再处理断行连字符）
    '\xa0': ' ',
}
DASH3 = re.compile('—{3,}')          # 第 1 册用 ——— 表示破折号，其余各册均为 ——

# 印刷版在行末拆开的外文词（连字符是排版遗留），以及少数缺空格/错字的外文词
WORDS = {
    'comple-xa': 'complexa', 'appa-rentia': 'apparentia', 'ex-hibitio': 'exhibitio', 'memo-ria': 'memoria',
    'exa-cta': 'exacta', 'cau-salitatis': 'causalitatis', 'transcen-dentalis': 'transcendentalis',
    'indef-initum': 'indefinitum', 'decom-positio': 'decompositio', 'Prototy-pon': 'Prototypon',
    'omni-tudo': 'omnitudo', 'Gold-schmidt': 'Goldschmidt', 'lan-guidum': 'languidum', 'Se-niores': 'Seniores',
    'commi-ssionis': 'commissionis', 'tempe-ries': 'temperies', 'parti-culariter': 'particulariter',
    'pro-positio': 'propositio', 'conver-sionem': 'conversionem', 'catho-licismus': 'catholicismus',
    'accesso-rium': 'accessorium', 'Sinn-spruch': 'Sinnspruch', 'pah-cio': 'pahcio',
    'entrçe': 'entrée', 'Franξois': 'François', 'Francois': 'François',
    'Dreβkammer': 'Dreßkammer', 'Hiβmann': 'Hißmann',
    'φιλsó': 'φιλόσο',
}
ROMAN_FIX = {'XⅢ': 'ⅩⅢ', 'XⅣ': 'ⅩⅣ', 'ⅩⅩXⅣ': 'ⅩⅩⅩⅣ', 'XⅡ': 'ⅩⅡ', 'XⅠ': 'ⅩⅠ'}

# ------------------------------------------------------------------------------------------ Greek
# 电子书里的希腊文：无重音、词末 ς 写成 s/c/ζ、个别字母错成拉丁字母或相近字母。逐词按上下文（见 docs/kant/greek.md）还原。
GREEK = {
    'αιδθητα και νοητα': 'αἰσθητὰ καὶ νοητά',
    'αλη，αλυω': 'ἀλή，ἀλύω',
    'ανθρωποπαθωζ': 'ἀνθρωποπαθῶς', 'θεοπρεπωζ': 'θεοπρεπῶς',
    'αυτοδιδακτοι': 'αὐτοδίδακτοι',
    'Aα｀χουσμαθιχοι': 'Ἀκουσματικοί', 'Aα｀χροαμαθιχοι': 'Ἀκροαματικοί',
    'φιλóδοξοV': 'φιλόδοξος', 'φιλσóοφοV': 'φιλόσοφος',
    'ζητειν': 'ζητεῖν', 'κακου，malum': 'κακοῦ，malum',
    'μεταβαδιs ειs αλλο γενοs': 'μετάβασις εἰς ἄλλο γένος', 'μεταβασιζ ειζαλλο γευοζ': 'μετάβασις εἰς ἄλλο γένος',
    'μυνδα': 'μυϊνδα',
    'Mens，νου': 'Mens，νοῦ',
    "χατ'ε,ξοχην": 'κατ’ ἐξοχήν',
    'προληφιc': 'πρόληψις', 'προληφισ': 'πρόληψις',
    'προτερον，而应是πρωτερον': 'πρότερον，而应是πρώτερον',
    'πρωτον ψενδοs': 'πρῶτον ψεῦδος', 'πρωτον ψευδοs': 'πρῶτον ψεῦδος', 'πρωτονψευδο': 'πρῶτον ψεῦδος',
    'στοα': 'στοά', 'παππα': 'πάππα',
    'υστεπον προτεπον': 'ὕστερον πρότερον', 'υ＇στερονπροτερου': 'ὕστερον πρότερον',
    "χατ' αληθειαυ": 'κατ’ ἀλήθειαν', "χατ'αληθειαυ": 'κατ’ ἀλήθειαν', "χατ' αληθειαν": 'κατ’ ἀλήθειαν',
    "χατ’ αληθειαν": 'κατ’ ἀλήθειαν', "χατ' αληθεια": 'κατ’ ἀλήθειαν', "χατ’ αληθεια": 'κατ’ ἀλήθειαν',
    "χαταληθεια": 'κατ’ ἀλήθειαν', 'χαταληθεια': 'κατ’ ἀλήθειαν',
    "χατ' ανθρωπου": 'κατ’ ἄνθρωπον', "χατ’ ανθρωπου": 'κατ’ ἄνθρωπον', "χατ' αυθρωπον": 'κατ’ ἄνθρωπον',
    "χατ’ αυθρωπον": 'κατ’ ἄνθρωπον', "χατανθρωπου": 'κατ’ ἄνθρωπον',
}
# 拉丁字母写的希腊词头（Kουξ'Oμπαξ 里的 K 和 O）保持原样

# ------------------------------------------------------------------------------------------ inline images
# 内联小图：着重号文字（成图）与公式。用一个小标记语法写成文字：  ^{..} 上标  _{..} 下标  ⟦..⟧ 根号横线（vinculum）
# 每一张的读法见 docs/kant/inline-images.md。
EMPH = {'image04122.jpeg': '先验', 'image04123.jpeg': '经常', 'image04124.jpeg': '经验的运用', 'image04125.jpeg': '知性',
        'image04126.jpeg': '感性只有在它们联合运用的时候'}
FORMULA = {
    'image04172.jpeg': '½',
    'image04200.jpeg': '√⟦Y21000Y^{3}⟧',
    'image04201.jpeg': 'x=^{3}√⟦1/3 m⟧',
    'image04202.jpeg': 'x=^{3}√⟦1/(3·355499)⟧',
    'image04203.jpeg': 'x=^{3}√⟦1/(3·1048)⟧',
    'image04205.jpeg': '√13=3.61，3.61/216=0.01672',
    'image04206.jpeg': 'X/R=G/C',
    'image04207.jpeg': 'G·R^{2}/X^{2}',
    'image04208.jpeg': 'C·R/X',
    'image04209.jpeg': '—d C_{ester}/dt=k_{2}C_{ester}C_{base} 和 —d C_{ester}/dt=k_{2}C_{ester}C_{säure}',
    'image04216.jpeg': '(1/62)·(r^{2}π/R^{2}π)',
    'image04217.jpeg': '600·b·(1/62)·(r^{2}π/R^{2}π)',
    'image04218.jpeg': '(1/62)·(r^{2}π/R^{2}π)=R·600b·(r/R)·(1/62)·(r^{2}π/R^{2}π)',
    'image04219.jpeg': 'r/R',
    'image04220.jpeg': 'R·(600·地球)/(62·r^{2}π)',
    'image04221.jpeg': '600/(62R^{2}π)',
    'image04222.jpeg': 'Mc=(5/2)mgT',
    'image04223.jpeg': '5/2',
    'image04224.jpeg': '(c/g)·(M/m)=1500/31',
    'image04234.jpeg': '(1/125)·(1/1048)=1/130000',
    'image04240.jpeg': 'ϊ',
}
_FX = re.compile(r'\^\{([^}]*)\}|_\{([^}]*)\}')
_BAR = re.compile(r'⟦([^⟧]*)⟧')


def fx_runs(s, base):
    """Markup string -> runs.  `base` carries the attributes of the surrounding run (bold, ...).  ⟦x⟧ (the radicand under a
    root sign) is set in parentheses, unless it is a plain number."""
    s = _BAR.sub(lambda m: m.group(1) if re.fullmatch(r'[\d.]+', m.group(1)) else '(' + m.group(1) + ')', s)
    out, pos = [], 0

    def add(t, c=''):
        if t:
            r = dict(base)
            r['t'] = t
            r.pop('i', None)
            r['c'] = ' '.join(x for x in (base.get('c', ''), 'fx', c) if x)
            out.append(r)
    for m in _FX.finditer(s):
        add(s[pos:m.start()])
        add(m.group(1) if m.group(1) is not None else m.group(2), 'msup' if m.group(1) is not None else 'msub')
        pos = m.end()
    add(s[pos:])
    return out


def expand_images(runs):
    """Inline images that stand for text (emphasised words, formulas) become text runs."""
    out = []
    for r in runs:
        name = r.get('i')
        if name in EMPH:
            out.append(dict({k: v for k, v in r.items() if k not in ('i', 't', 'c')}, t=EMPH[name], c='emp'))
        elif name in FORMULA:
            out += fx_runs(FORMULA[name], {k: v for k, v in r.items() if k not in ('t',)})
        else:
            out.append(r)
    return out


# ------------------------------------------------------------------------------------------ text
CJK = '一-鿿'
_CLOSE = '，。、；：！？）］】〕》」』”’…—．～／'
_OPEN = '（［【〔《「『“‘'
_RE_SP_BEFORE = re.compile(r'[ 　]*(?<=[ 　])(?=[%s])' % re.escape(_CLOSE))       # placeholder (not used)
_RE_SPACE_AROUND_FW = re.compile(r'(?<=[%s%s]) +| +(?=[%s%s])' % (re.escape(_CLOSE), re.escape(_OPEN), re.escape(_CLOSE), re.escape(_OPEN)))
_RE_DIGSP = re.compile(r'(?<=\d) +(?=\d)')
_RE_DIGCJK = re.compile(r'(?<=\d) +(?=[%s])|(?<=[%s]) +(?=\d)' % (CJK, CJK))
_RE_CAPDIG = re.compile(r'(?<![A-Za-z])([A-Z]) +(?=\d)')
_RE_DIGLET = re.compile(r'(?<=\d) +(?=[a-z](?![A-Za-z]))')
_RE_DOT = re.compile(r'(?<=[a-zäöüß]{2})\.(?=[A-Za-zÄÖÜ][a-zäöüßé])|(?<=\b[A-Z])\.(?=[A-Z][a-z]{2})')
_RE_HYPH = re.compile(r'(?<=[a-zäöüß])- +(?=[a-zäöüß])')
_RE_ROMAN = re.compile('|'.join(sorted(map(re.escape, ROMAN_FIX), key=len, reverse=True)))
_RE_BETA = re.compile(r'(?<=[A-Za-zÄÖÜäöü])[βΒ](?=[a-zäöü]|\b)')


VOLUME = 0        # set by kant_struct.elements(): the spaced-digit typesetting artefact ('1 7 8 1年') only occurs in volume 1


def set_volume(v):
    global VOLUME
    VOLUME = v


_RE_GT = re.compile('(?<=[\u4e00-\u9fff])＞')
_RE_NBSP_GAP = re.compile('(?<=[\u4e00-\u9fff，。、；：！？”）])[ \xa0]*\xa0[ \xa0]*(?=[\u4e00-\u9fff“（《])')


def fix_text(t):
    t = _RE_NBSP_GAP.sub('', t)                  # NBSP runs inside a sentence (layout residue of the source)
    for k, v in PUA.items():
        t = t.replace(k, v)
    for k, v in CHARS.items():
        t = t.replace(k, v)
    t = _RE_GT.sub('》', t)                        # ＞ closing a title; a ＞ after ')' / a letter is the math sign, kept
    t = DASH3.sub('——', t)
    t = re.sub(r' {2,}', ' ', t)                 # runs of blanks (NBSP layout hacks of the source)
    for k, v in GREEK.items():
        if k in t:
            t = t.replace(k, v)
    t = _RE_ROMAN.sub(lambda m: ROMAN_FIX[m.group(0)], t)
    t = _RE_HYPH.sub('', t)                       # 'Si- nnlichkeit' (line-break hyphen, space) -> 'Sinnlichkeit'
    for k, v in WORDS.items():
        if k in t:
            t = t.replace(k, v)
    t = _RE_SPACE_AROUND_FW.sub('', t)
    if VOLUME == 1:
        t = _RE_DIGSP.sub('', t)
        t = _RE_DIGSP.sub('', t)
        t = _RE_DIGCJK.sub('', t)
        t = _RE_CAPDIG.sub(r'\1', t)
        t = _RE_DIGLET.sub('', t)
    t = _RE_DOT.sub('. ', t)
    t = _RE_BETA.sub('ß', t)
    return t


def fix_runs(runs):
    """Text repairs for a run list (works on each run; keeps links/anchors/markup)."""
    runs = expand_images(runs)
    out = []
    for r in runs:
        if r['t'] in (BR, OBJ) or r.get('i'):
            out.append(r)
            continue
        t = fix_text(r['t'])
        if t != r['t']:
            r = dict(r, t=t)
        out.append(r)
    return merge_runs(out)


def fix_edges(runs):
    """Strip leading/trailing blanks of a paragraph (source used NBSP runs as indentation)."""
    runs = [r for r in runs if r['t'] != '']
    while runs and not runs[0].get('i') and runs[0]['t'].strip(' 　\xa0') == '' and runs[0]['t'] != BR:
        runs.pop(0)
    while runs and not runs[-1].get('i') and runs[-1]['t'].strip(' 　\xa0') == '' and runs[-1]['t'] != BR:
        runs.pop()
    if runs:
        runs[0] = dict(runs[0], t=runs[0]['t'].lstrip(' \xa0'))
        runs[-1] = dict(runs[-1], t=runs[-1]['t'].rstrip(' \xa0'))
    return [r for r in runs if r['t'] != '']
