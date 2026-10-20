"""Note marks against note entries of a book (after the bk_fixes corrections): marks that point nowhere, entries no mark
points to, duplicate anchors, and marks whose number differs from their entry's.

    BOOK_SCRATCH=<dir> python -m tools.qa_marks N
"""
import re
import sys
from . import bk, bk_extract as BE, bk_text as BT


def _num(t):
    """The number of a note entry: its leading digits (an entry that is all one back-link carries its whole text)."""
    m = re.match(r'\s*[\[［(（〔]?(\d+)', t)
    return m.group(1) if m else re.sub(r'\D', '', t)


def check(b):
    C = bk.CFG[b]
    BT.SYM_MARKS = C.get('sym_marks', '')                # (book 62) marks that are symbols: '*', '†'
    parts = [x for n, _ in C['front'] for x in bk._parts(n)]
    for x in C['body']:
        parts += bk._parts(x)
    for x in C['back']:
        if isinstance(x, tuple) and x[1] in ('pagelinks', 'index'):
            continue                                      # (links to printed pages, page numbers: not note marks)
        parts += bk._parts(x[0] if isinstance(x, tuple) else x)
    parts += list(C.get('endnotes', ()))
    marks, notes, dup = {}, {}, []
    noteish = set(C.get('note_cls', ()))
    lab = C.get('mark_label')                             # (book 59) marks with a label before the number: '[原注3]'
    is_mark = lambda t: BT.marker_text(t, 'sq') or (lab and re.fullmatch(r'\[(?:%s)[\dA-Z]+\]' % lab, t.strip()))
    sections = {p for x in C['back'] if isinstance(x, tuple) and x[1] == 'notes' for p in bk._parts(x[0])}   # (the ebook's notes in place)
    for n in parts:
        for i, it in enumerate(BE.items(bk.P(n))):
            is_note = it['k'] == 'note' or set(it['cls'].split()) & noteish or n in C.get('endnotes', ()) or n in sections and it['k'] == 'p'
            runs = it.get('runs', [])
            if runs and runs[0].get('i') in C.get('img_mark', {}):
                mt, href = C['img_mark'][runs[0]['i']]   # (book 59) a picture that is a note's mark: bk sets the mark above it
                marks[it['id']] = (n, i, mt, href)
                continue
            if C.get('note_by_marker') and it['k'] == 'p' and len(runs) > 1 and runs[0].get('h') and is_mark(runs[0]['t']):
                is_note = True                            # (as bk.elements: a paragraph that starts with a linked number is a note)
            if C.get('note_li') and it['k'] == 'li' and runs and (runs[0].get('h') or runs[0].get('a')) and BT.marker_text(runs[0]['t'], 'sq'):
                is_note = True                            # (as bk.elements: a list item that starts with a linked number)
            if is_note:
                key = runs[0].get('a') or (it.get('id') if runs[0].get('h') and is_mark(runs[0]['t']) else None) if runs else None
                if key:                                   # (book 59: the anchor of a source note is its paragraph's id)
                    notes[key] = (n, i, runs[0]['t'], runs[0].get('h'))
                runs = [r for r in runs[1:] if re.fullmatch(r'\[[^\]\s]{1,6}\]', r['t'].strip())
                        or r.get('s') and r.get('h') and r.get('a')]   # (marks inside a note: '[n]', or a raised linked mark '（n）')
            for r in runs:
                if r.get('h') and (r.get('s') or is_mark(r['t'])):
                    if r.get('a') in marks:
                        dup.append((n, i, r['t'], r.get('a')))
                    marks[r.get('a') or f'?{n}:{i}:{r["t"]}'] = (n, i, r['t'], r.get('h'))
    bad = []
    for a, (n, i, t, h) in marks.items():
        if h not in notes:
            bad.append(('角标指向不存在的注释', n, i, t, h))
        elif _num(notes[h][2]) != re.sub(r'\D', '', t) or not re.sub(r'\D', '', t) and notes[h][2].strip() != t.strip():
            bad.append(('角标与注释编号不同', n, i, t, notes[h][2]))
    orphan = []
    for a, (n, i, t, h) in notes.items():
        if h is None:
            orphan.append((n, i, t))                      # (books 53, 57) a note whose mark the ebook's text lacks: no back-link
        elif h not in marks:
            bad.append(('注释的回链没有对应角标', n, i, t, h))
    check.orphan = orphan
    return marks, notes, dup, bad


if __name__ == '__main__':
    b = int(sys.argv[1])
    marks, notes, dup, bad = check(b)
    print(f'book {b}: 角标 {len(marks)}  注释 {len(notes)}  重复锚点 {len(dup)}  问题 {len(bad)}')
    if check.orphan:
        print(f'  电子书正文里没有注码的注释（不设回链）{len(check.orphan)} 条：', check.orphan[:20])
    for x in dup[:20]:
        print('  重复', x)
    for x in bad[:60]:
        print(' ', x)
