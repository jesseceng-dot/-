"""PDF post-processing: rewrite placeholder URI links into internal GoTo links, add bookmarks, page labels."""
import re
import urllib.parse
import pymupdf
from . import style


def finish_pdf(src, dst, anchors, outline, labels, meta):
    doc = pymupdf.open(src)
    missing = {}
    n_int = n_ext = 0
    for pno in range(len(doc)):
        page = doc[pno]
        for l in page.get_links():
            uri = l.get('uri') or ''
            if not uri.startswith(style.LINK_BASE):
                n_ext += 1
                continue
            key = urllib.parse.unquote(uri[len(style.LINK_BASE):])
            page.delete_link(l)
            tgt = anchors.get(key)
            if tgt is None:
                missing[key] = missing.get(key, 0) + 1
                continue
            tp, ty = tgt
            page.insert_link({'kind': pymupdf.LINK_GOTO, 'from': l['from'], 'page': tp,
                              'to': pymupdf.Point(0, max(0.0, ty - 12)), 'zoom': 0})
            n_int += 1
    if outline:
        doc.set_toc(outline)
    if labels:
        doc.set_page_labels(labels)
    doc.set_metadata(meta)
    doc.save(dst, garbage=4, deflate=True, clean=True)
    return dict(internal=n_int, external=n_ext, missing=missing)
