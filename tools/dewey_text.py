"""《杜威著作精选11种》的文字修复：私用区字符、标点旁多余空格、直撇号、希腊文、行内小图转文字。

电子书的文字很干净，需要处理的只有下面几类（全部列在 docs/dewey/dispositions.md）。
"""
import re
from .model import run, merge_runs, BR, OBJ

# 电子书字库里没有的外文字母（Kindle 私用区）：上下文对应 Cæsar / Märkel / Höffding、Fröhlich
PUA = {'': 'æ', '': 'ä', '': 'ö'}

# 行内小图（13 张）：着重…… 见 docs/dewey/inline-images.md
#   文字 -> (文字, 类)；公式 -> 一组 run
IMG_TEXT = {
    'image01826.jpeg': [run('䳍')],                                  # 䳍（共+鸟）：海伦·凯勒所说的一种鸟的蛋
    'image01835.jpeg': [run('√'), run('−1', c='ov')],                    # 负一的平方根
    'image01843.jpeg': [run('φιλία', c='it')],
    'image01844.jpeg': [run('ὁμόνοια', c='it')],
    'image01845.jpeg': [run('μεγαλοψυχία', c='it')],
    'image01846.jpeg': [run('τέλος', c='it')],
    'image01847.jpeg': [run('ἡδονή', c='it')],
    'image01848.jpeg': [run('ἄσκησις', c='it')],
    'image01854.jpeg': [run('εἴδωλα', c='it')],
    'image01855.jpeg': [run('γνῶναι', c='it')],
    'image01856.jpeg': [run('εἰδέναι', c='it')],
    'image01857.jpeg': [run('connaître', c='it')],
    'image01858.jpeg': [run('λόγος', c='it')],
}

_RE_SPACE_BEFORE_CLOSE = re.compile(r'(?<=[A-Za-z0-9])[ 　]+(?=[）】》”’，。；：！？、])')
_RE_APOS = re.compile(r"(?<=[A-Za-z])'(?=[A-Za-z]|\s|[）”，。；：])")


def fix_text(t):
    for k, v in PUA.items():
        t = t.replace(k, v)
    t = t.replace('\xa0', ' ')
    t = t.replace('τεχνη＇', 'τέχνη')                 # 希腊字（无重音转写）+ 全角撇号当重音
    t = _RE_APOS.sub('’', t)                          # Poetry's / O'Neill / Agnes' -> typographic apostrophe
    t = _RE_SPACE_BEFORE_CLOSE.sub('', t)             # '（Genesis ）' '“eudaimonia ”'
    t = re.sub(r' {2,}', ' ', t)
    return t


def expand_images(runs):
    """Inline images -> text runs (see IMG_TEXT); an image that has no transcription is kept (and reported by the checker)."""
    out = []
    for r in runs:
        if r.get('i') and r['i'] in IMG_TEXT:
            for x in IMG_TEXT[r['i']]:
                d = dict(x)
                for k in ('h', 'a', 'b'):
                    if r.get(k):
                        d[k] = r[k]
                out.append(d)
        else:
            out.append(r)
    return out


def fix_runs(runs):
    runs = expand_images(runs)
    out = []
    for r in runs:
        if r.get('i'):
            out.append(r)
            continue
        t = fix_text(r['t'])
        if t:
            out.append(dict(r, t=t))
    close = '）】》”’，。；：！？、'
    for i in range(len(out)):                            # '<i>Genesis</i> ）' / '<i>Genesis </i>）': the space sits at the run boundary
        if i and out[i]['t'].startswith(' ') and out[i]['t'].lstrip(' ')[:1] in close and not out[i - 1].get('i'):
            out[i] = dict(out[i], t=out[i]['t'].lstrip(' '))
        if i + 1 < len(out) and out[i + 1]['t'][:1] in close and not out[i].get('i'):
            out[i] = dict(out[i], t=out[i]['t'].rstrip(' '))
    return merge_runs([r for r in out if r['t'] != ''])


def fix_edges(runs):
    """No leading/trailing plain space at the edges of a paragraph."""
    runs = [dict(r) for r in runs]
    while runs and runs[-1]['t'] == BR:
        runs.pop()
    if runs and not runs[0].get('i'):
        runs[0]['t'] = runs[0]['t'].lstrip(' ')
    if runs and not runs[-1].get('i'):
        runs[-1]['t'] = runs[-1]['t'].rstrip(' ')
    return [r for r in runs if r['t'] != '']
