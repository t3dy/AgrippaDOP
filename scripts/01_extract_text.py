#!/usr/bin/env python3
"""
Phase 2 — Text extraction.

Robust extraction with PyMuPDF. Selective OCR fallback (Tesseract via
pytesseract) for pages whose embedded text is empty/poor — only if OCR is
available; otherwise such pages are flagged for manual handling rather than
silently dropped.

Unicode is normalised (NFC) while preserving Latin / Greek / Hebrew / sigla /
diacritics. Page boundaries are kept intact.

Outputs:
  data/ocr/pages.jsonl       one JSON record per page
  data/ocr/full_text.txt     page-delimited plain text
  logs/extraction_warnings.md aggregated quality problems

Usage:
    python scripts/01_extract_text.py [--pdf PATH] [--ocr auto|never|force]
                                      [--ocr-lang lat+grc+heb]
"""

from __future__ import annotations

import argparse
from collections import Counter

import common as C


PAGE_DELIM = "\n\n===== PAGE {n} ({printed}) [{method}/{quality}] =====\n\n"


def classify_quality(text: str) -> tuple[str, list[str]]:
    """Mirror of the inspection heuristic, kept here so Phase 2 is standalone."""
    warnings: list[str] = []
    s = text.strip()
    n = len(s)
    if n == 0:
        return "empty", ["no embedded text"]
    repl = text.count("�")
    alpha = sum(ch.isalpha() for ch in s)
    ratio = alpha / max(n, 1)
    if repl:
        warnings.append(f"{repl} replacement chars")
    if n < 80:
        return "poor", warnings + [f"only {n} chars"]
    if ratio < 0.45 or repl > 5:
        return "partial", warnings + [f"alpha ratio {ratio:.2f}"]
    return "good", warnings


def try_ocr_page(doc, page_index: int, lang: str):
    """OCR a single page if pytesseract+tesseract are available. Returns
    (text, ok). On any failure returns ("", False) so the caller can flag it."""
    try:
        import pytesseract  # noqa
        from PIL import Image  # noqa
        import io
    except ImportError:
        return "", False
    try:
        page = doc.load_page(page_index)
        # Render at 300 dpi for OCR quality.
        pix = page.get_pixmap(dpi=300)
        from PIL import Image
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, lang=lang)
        return text, True
    except Exception as exc:  # noqa: BLE001
        C.log(f"OCR failed on page {page_index + 1}: {exc}")
        return "", False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf")
    ap.add_argument("--ocr", choices=["auto", "never", "force"], default="auto",
                    help="auto: OCR only empty/poor pages; never: no OCR; "
                         "force: OCR every page")
    ap.add_argument("--ocr-lang", default="lat+grc+heb",
                    help="Tesseract language packs (e.g. lat+grc+heb+ita)")
    args = ap.parse_args()

    C.ensure_dirs()
    fitz = C.require_fitz()

    pdf_path = C.resolve_pdf(args.pdf)
    if pdf_path is None:
        C.log("No PDF found (data/raw/ empty and no --pdf). Aborting Phase 2.")
        (C.LOGS / "extraction_warnings.md").write_text(
            "# Extraction warnings\n\n**No PDF found** — nothing extracted.\n",
            encoding="utf-8")
        return

    doc = fitz.open(pdf_path)
    n_pages = doc.page_count
    C.log(f"Extracting {n_pages} pages from {pdf_path.name} (ocr={args.ocr})")

    records: list[dict] = []
    warnings_log: list[str] = []
    method_counts: Counter = Counter()
    quality_counts: Counter = Counter()
    ocr_unavailable_flagged = False

    full_parts: list[str] = []

    for i in range(n_pages):
        page = doc.load_page(i)
        raw = page.get_text("text")
        text = C.normalize_text(raw)
        quality, qwarn = classify_quality(text)
        method = "embedded" if quality != "empty" else "empty"

        need_ocr = (
            args.ocr == "force"
            or (args.ocr == "auto" and quality in ("empty", "poor"))
        )
        if need_ocr:
            ocr_text, ok = try_ocr_page(doc, i, args.ocr_lang)
            if ok and ocr_text.strip():
                ocr_text = C.normalize_text(ocr_text)
                if args.ocr == "force" and text:
                    # keep both but prefer the longer
                    text = ocr_text if len(ocr_text) > len(text) else text
                    method = "embedded+ocr"
                else:
                    text = ocr_text
                    method = "ocr"
                quality, qwarn = classify_quality(text)
            elif not ok:
                if not ocr_unavailable_flagged:
                    warnings_log.append(
                        "- **OCR unavailable** (pytesseract/Tesseract not "
                        "installed). Empty/poor pages were kept as-is and "
                        "flagged; install Tesseract with lat/grc/heb packs to "
                        "enable selective OCR.")
                    ocr_unavailable_flagged = True
                qwarn = qwarn + ["OCR wanted but unavailable"]

        printed = None
        # cheap printed-number sniff: standalone numeric line near edges
        edge_lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        for ln in edge_lines[:2] + edge_lines[-2:]:
            if ln.isdigit() and len(ln) <= 4:
                printed = ln
                break

        rec = C.PageRecord(
            page_number=i + 1,
            printed_number=printed,
            text=text,
            char_count=len(text),
            extraction_method=method,
            extraction_quality=quality,
            scripts=C.script_histogram(text),
            warnings=qwarn,
        )
        records.append(rec.__dict__)
        method_counts[method] += 1
        quality_counts[quality] += 1
        if qwarn:
            warnings_log.append(
                f"- p.{i+1} [{quality}]: " + "; ".join(qwarn))

        full_parts.append(
            PAGE_DELIM.format(n=i + 1, printed=printed or "?",
                              method=method, quality=quality) + text)

    # Write artefacts.
    n = C.write_jsonl(C.PAGES_JSONL, records)
    C.FULL_TEXT.write_text("".join(full_parts), encoding="utf-8")

    # Aggregate non-latin script presence for the warnings log.
    greek_pages = [r["page_number"] for r in records if r["scripts"].get("greek", 0) > 3]
    hebrew_pages = [r["page_number"] for r in records if r["scripts"].get("hebrew", 0) > 3]

    log_lines = ["# Extraction warnings\n"]
    log_lines.append(f"- Source: `{pdf_path.name}`")
    log_lines.append(f"- Pages: {n}")
    log_lines.append("- Method counts: " +
                     ", ".join(f"{k}={v}" for k, v in method_counts.most_common()))
    log_lines.append("- Quality counts: " +
                     ", ".join(f"{k}={v}" for k, v in quality_counts.most_common()))
    log_lines.append(f"- Pages with Greek (>3 chars): "
                     f"{greek_pages[:30]}{' …' if len(greek_pages) > 30 else ''}")
    log_lines.append(f"- Pages with Hebrew (>3 chars): "
                     f"{hebrew_pages[:30]}{' …' if len(hebrew_pages) > 30 else ''}")
    log_lines.append("\n## Per-page issues\n")
    log_lines.extend(warnings_log or ["- none"])
    (C.LOGS / "extraction_warnings.md").write_text(
        "\n".join(log_lines) + "\n", encoding="utf-8")

    C.log(f"Wrote {n} page records to {C.PAGES_JSONL}")
    C.log(f"Wrote full text to {C.FULL_TEXT}")
    C.log(f"Wrote warnings to {C.LOGS / 'extraction_warnings.md'}")
    doc.close()


if __name__ == "__main__":
    main()
