import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pymupdf, survey
doc = pymupdf.open('src/book.pdf')
for pn in range(1, len(doc) + 1):
    L = survey.paragraphs(doc, pn)
    for i in range(1, len(L)):
        y, x, t = L[i]
        if abs(x - 78.51) < 0.3 and i >= 3:
            # previous lines: display rows
            prev = L[i - 1]
            if prev[1] > 120 and L[i-2][1] > 120:
                rows = []
                j = i - 1
                while j >= 0 and L[j][1] > 120 and not L[j][2].startswith('✍'):
                    rows.append(L[j]); j -= 1
                rows = rows[::-1]
                print('p%d gap %.2f | %s || %s' % (pn, prev[0] - y, ' / '.join('%.2f@%.0f %s' % (r[0], r[1], r[2][:30]) for r in rows), t[:30]))
