"""Which characters of the book are not covered by the fonts that will render them?"""
import sys, collections
from fontTools.ttLib import TTFont
from . import style, books
from .model import runs_text

FONTS = {
    'SongBody': [style.FONT_DIR + '/SerifSC-Regular.ttf'],
    'HeiTi': [style.FONT_DIR + '/SansSC-Regular.ttf'],
    'KaiTi': [style.FONT_DIR + '/LXGWWenKai-Regular.ttf'],
    'Noto Serif': [style.FONT_DIR + '/NotoSerif-Regular.ttf'],
}
CL = {'SongBody': [], 'HeiTi': [], 'KaiTi': [], 'Noto Serif': []}


def cmap(path):
    return set(TTFont(path, lazy=True).getBestCmap().keys())


def check(cfg):
    cm = {k: cmap(v[0]) for k, v in FONTS.items()}
    body_stack = [cm['Noto Serif'] if False else set(), cm['SongBody'], cm['Noto Serif']]
    missing = collections.defaultdict(collections.Counter)
    from .layout import STYLES, STYLES_SMALL
    kai_styles = {k for k, v in list(STYLES.items()) + list(STYLES_SMALL.items()) if v['cls'] in ('s-quote', 's-h2', 's-h4', 's-h6')}
    hei_styles = {k for k, v in list(STYLES.items()) + list(STYLES_SMALL.items()) if v['cls'] in ('s-h1', 's-h3', 's-h5', 's-h7', 's-secnum', 's-idxhead', 's-toc0', 's-toc1')}
    for mod in cfg['modules']:
        for b in mod.blocks:
            if b['k'] not in ('p', 'h'):
                continue
            st = b['style']
            stack = [cm['SongBody'], cm['Noto Serif']]
            if st in kai_styles:
                stack = [cm['KaiTi'], cm['SongBody'], cm['Noto Serif']]
            elif st in hei_styles:
                stack = [cm['HeiTi'], cm['SongBody'], cm['Noto Serif']]
            for ch in runs_text(b['runs']):
                o = ord(ch)
                if ch in '\n⁠​' or o < 0x20:
                    continue
                if not any(o in s for s in stack):
                    missing[ch][(mod.mid, st)] += 1
                elif st in kai_styles and o not in cm['KaiTi']:
                    missing['(kai fallback) ' + ch][(mod.mid, st)] += 1
                elif st in hei_styles and o not in cm['HeiTi']:
                    missing['(hei fallback) ' + ch][(mod.mid, st)] += 1
    return missing


if __name__ == '__main__':
    for name in sys.argv[1:]:
        cfg = getattr(books, name)()
        miss = check(cfg)
        print(name, 'characters lacking a glyph:', len(miss))
        for ch, c in sorted(miss.items(), key=lambda x: -sum(x[1].values()))[:40]:
            print('  ', repr(ch), hex(ord(ch[-1])), dict(list(c.items())[:3]))
