"""Assemble one book: modules -> pages -> HTML -> PDF (+ links, bookmarks, page labels)."""
import os
import re
import json
import html as _html
from dataclasses import dataclass, field
from . import style, layout, typeset, render
from .layout import GRIDS
from .model import runs_text, run, BR

ROMAN = [(1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'), (100, 'c'), (90, 'xc'), (50, 'l'), (40, 'xl'),
         (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')]


def roman(n):
    out = ''
    for v, s in ROMAN:
        while n >= v:
            out += s
            n -= v
    return out


@dataclass
class Mod:
    mid: str
    zone: str                     # cover | front | body | back
    title: str = ''
    blocks: list = field(default_factory=list)
    grid: str = 'body'
    kind: str = 'text'            # text | page
    html: str = ''                # for kind == 'page' (a full static page)
    toc: bool = True              # listed in the table of contents
    toc_title: str = ''
    head: bool = True             # running head on non-opening pages
    folio: bool = True
    volume: str = ''              # volume label for multi-volume books
    toc_level: int = 1            # level of the module entry in the TOC
    anchor: str = ''              # extra anchor id resolving to the first page
    single: bool = False          # must fit on one page
    # filled in by the builder
    lbs: list = None
    plan: dict = None
    npages: int = 1


def title_text(runs):
    """Plain title: no forced breaks, no superscript note markers."""
    t = ''.join(r['t'] for r in runs if not r.get('s')).replace(BR, '')
    return t


@dataclass
class Page:
    mod: Mod
    inner: str = ''
    first: bool = False
    label: str = ''
    index: int = 0


class BookBuilder:
    def __init__(self, cfg, measurer):
        self.cfg = cfg
        self.m = measurer
        self.mods = cfg['modules']
        self.pages = []
        self.anchors = {}
        self.block_pages = {}      # (mid, block idx) -> physical page index

    # ---------------------------------------------------------------- typeset
    def typeset_all(self, cache_dir=None):
        for mod in self.mods:
            if mod.kind != 'text':
                mod.npages = 1
                continue
            if mod.blocks and mod.blocks[0]['k'] in ('h', 'p') and mod.blocks[0].get('brk') is None:
                pass
            lbs, plan = typeset.typeset(mod.blocks, self.m, mod.grid)
            mod.lbs, mod.plan = lbs, plan
            g = GRIDS[mod.grid]
            mod.npages = (len(plan['pages']) + g['cols'] - 1) // g['cols']
        return self

    # ---------------------------------------------------------------- page sequence and labels
    def sequence(self):
        self.pages = []
        for mod in self.mods:
            for k in range(mod.npages):
                self.pages.append(Page(mod=mod, first=(k == 0), index=len(self.pages)))
        # block -> physical page
        for mod in self.mods:
            if mod.kind != 'text':
                continue
            base = next(p.index for p in self.pages if p.mod is mod)
            g = GRIDS[mod.grid]
            for lpi, lp in enumerate(mod.plan['pages']):
                for (bi, lo, hi, slot0) in lp['items']:
                    self.block_pages.setdefault((mod.mid, bi), base + lpi // g['cols'])
        # folio labels: front matter roman (cover excluded), body/back arabic from 1
        n_front = 0
        n_body = 0
        for p in self.pages:
            z = p.mod.zone
            if z == 'cover':
                p.label = ''
            elif z == 'front':
                n_front += 1
                p.label = roman(n_front)
            else:
                n_body += 1
                p.label = str(n_body)
        return self

    def pages_of(self, mod):
        return [p for p in self.pages if p.mod is mod]

    def page_label(self, mid, bi):
        return self.pages[self.block_pages[(mid, bi)]].label

    # ---------------------------------------------------------------- html
    def render_pages(self):
        htmls = []
        for p in self.pages:
            mod = p.mod
            if mod.kind == 'page':
                inner = mod.html(self, p) if callable(mod.html) else mod.html
                if p.first:
                    self.anchors.setdefault(mod.mid, (p.index, style.TOP))
                    if mod.anchor:
                        self.anchors.setdefault(mod.anchor, (p.index, style.TOP))
            else:
                g = GRIDS[mod.grid]
                base = next(q.index for q in self.pages if q.mod is mod)
                k = p.index - base
                inner = ''
                for c in range(g['cols']):
                    lpi = k * g['cols'] + c
                    if lpi < len(mod.plan['pages']):
                        inner += render.logical_page_html(mod.plan['pages'][lpi], mod.lbs, mod.plan['variants'],
                                                          mod.grid, c, self.anchors, p.index)
                if k == 0:
                    self.anchors.setdefault(mod.mid, (p.index, style.TOP))
                    if mod.anchor:
                        self.anchors.setdefault(mod.anchor, (p.index, style.TOP))
                inner += self.furniture(p, k == 0)
            htmls.append(f'<section class="page">{inner}</section>')
        return htmls

    def furniture(self, p, opener):
        mod = p.mod
        out = ''
        if mod.folio and p.label:
            out += (f'<div class="hd c" style="width:{style.PAGE_W}pt;text-align:center;'
                    f'transform:translate(0pt,{style.PAGE_H - 36}pt);font-size:9pt">{p.label}</div>')
        if mod.head and not opener and p.label:
            recto = (p.index % 2 == 0) == (self.pages[0].mod.zone != 'cover') if False else None
            verso = self._is_verso(p)
            text = self.cfg['title'] if verso else (mod.toc_title or mod.title)
            out += (f'<div class="hd" style="width:{style.TEXT_W}pt;left:{style.LEFT}pt;text-align:{"left" if verso else "right"};'
                    f'transform:translate(0pt,34pt)">{_html.escape(text)}</div>'
                    f'<div class="rule" style="left:{style.LEFT}pt;width:{style.TEXT_W}pt;top:46pt"></div>')
        return out

    def _is_verso(self, p):
        # verso = even printed page; front matter counted with roman numerals
        try:
            n = int(p.label)
        except ValueError:
            n = self._roman_value(p.label)
        return n % 2 == 0

    @staticmethod
    def _roman_value(s):
        vals = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100, 'd': 500, 'm': 1000}
        tot = 0
        for i, ch in enumerate(s):
            v = vals[ch]
            if i + 1 < len(s) and vals[s[i + 1]] > v:
                tot -= v
            else:
                tot += v
        return tot

    # ---------------------------------------------------------------- output
    def build_html(self):
        self.sequence()
        htmls = self.render_pages()
        return render.document_html(htmls)


# ------------------------------------------------------------------------------------------ table of contents
def make_toc(mods, title='目　录', levels=(1, 2, 3)):
    blocks = [dict(k='h', style='tochead', rank=1, runs=[run(title)], id='toc')]
    refs = []
    last_vol = None
    for mod in mods:
        if mod.volume and mod.volume != last_vol:
            last_vol = mod.volume
            blocks.append(dict(k='p', style='toc0', runs=[run(mod.volume, h=mod.mid)], h=mod.mid, toc_ref=(mod.mid, None)))
        if not mod.toc or mod.kind != 'text' and not mod.title:
            continue
        if mod.kind == 'page' and not mod.toc_title:
            continue
        label = mod.toc_title or mod.title
        entry = dict(k='p', style=f'toc{mod.toc_level}', runs=[run(label, h=mod.mid)], h=mod.mid, toc_ref=(mod.mid, None))
        blocks.append(entry)
        if mod.kind == 'text':
            for bi, b in enumerate(mod.blocks):
                if b['k'] == 'h' and b.get('rank', 9) in (2, 3) and b.get('rank', 9) in levels and not b.get('notoc'):
                    if not b.get('id'):
                        b['id'] = f'{mod.mid}#h{bi}'
                    txt = title_text(b['runs']).replace('\u3000', '\u3000')
                    blocks.append(dict(k='p', style=f'toc{b["rank"] + 0}' if b['rank'] > 1 else 'toc2',
                                       runs=[run(re.sub(r'\s+', ' ', txt) if False else txt, h=b['id'])],
                                       h=b['id'], toc_ref=(mod.mid, bi)))
    return blocks


def fill_toc_labels(builder, toc_mod):
    for b in toc_mod.blocks:
        ref = b.get('toc_ref')
        if not ref:
            continue
        mid, bi = ref
        if bi is None:
            pg = next(p for p in builder.pages if p.mod.mid == mid)
            b['pg'] = pg.label
        else:
            b['pg'] = builder.page_label(mid, bi)
