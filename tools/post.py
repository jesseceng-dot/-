"""PDF post-processing: rewrite placeholder URI links into internal GoTo links, add bookmarks, page labels."""
import re
import urllib.parse
import pymupdf
from . import style


def fit_page_box(doc, page):
    """Chromium rounds the printed page size to whole device units (16开: 481.92 x 679.92 pt instead of 481.89 x 680.31 pt).
    The MediaBox is set to the exact size: the top edge stays where it is (every baseline keeps its distance from the top),
    the difference is added at the bottom and cut at the right; the CropBox (same as the MediaBox) is dropped."""
    mb = page.rect
    if abs(mb.width - style.PAGE_W) < 0.005 and abs(mb.height - style.PAGE_H) < 0.005:
        return
    top = page.mediabox.y1                                # PDF coordinates: y grows upwards
    page.set_mediabox(pymupdf.Rect(page.mediabox.x0, top - style.PAGE_H, page.mediabox.x0 + style.PAGE_W, top))
    doc.xref_set_key(page.xref, 'CropBox', 'null')


def finish_pdf(src, dst, anchors, outline, labels, meta):
    doc = pymupdf.open(src)
    missing = {}
    n_int = n_ext = 0
    for pno in range(len(doc)):
        page = doc[pno]
        fit_page_box(doc, page)
        for l in page.get_links():
            uri = l.get('uri') or ''
            if not uri.startswith(style.LINK_BASE):
                n_ext += 1
                continue
            key = urllib.parse.unquote(uri[len(style.LINK_BASE):])
            page.delete_link(l)
            tgt = anchors.get(key) or anchors.get(key.split('#')[0])
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
