#!/usr/bin/env python3
"""
Phase 1 — Inspect the PDF.

Determines page count, checks for embedded text, samples text from the
likely front-matter / comparison-table / main-text / apparatus zones, looks
for recurring headers/footers/page numbers/line numbers, detects chapter
headings heuristically, and — crucially — hunts for the siglum used for
MS Wuerzburg M.ch.q.50 *without assuming it is "W"*.

Output: outputs/reports/pdf_inspection.md

Usage:
    python scripts/00_inspect_pdf.py [--pdf /path/to/edition.pdf] [--sample 6]
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

import common as C


# --------------------------------------------------------------------------
# Heuristics
# --------------------------------------------------------------------------
# Chapter / book headings. Perrone Compagni follows the Latin tradition; these
# are deliberately permissive and will be refined in Phase 3.
CHAPTER_HEADING_RE = re.compile(
    r"(?im)^\s*(?:CAPUT|CAP\.?|CAPITULUM|LIBER|LIB\.?)\s+"
    r"([IVXLCDM]+|\d+|PRIMUS|SECUNDUS|TERTIUS|QUARTUS)\b"
)
# A line that is mostly a roman/arabic numeral (candidate page number).
PAGE_NUMBER_LINE_RE = re.compile(r"^\s*(?:[IVXLCDMivxlcdm]+|\d{1,4})\s*$")
# Apparatus lines tend to carry line-number lemmas like "12 word] W om." or
# dense sigla + brackets. We look for the lemma bracket "]" and sigla clusters.
APPARATUS_CUE_RE = re.compile(r"\]\s|\bom\.\b|\badd\.\b|\bcorr\.\b|\bcodd?\.\b")
# Line-number gutter (small integers at line starts in the apparatus block).
LINE_NUMBER_RE = re.compile(r"(?m)^\s*\d{1,3}\b")

# Thematic cue words that, if dense on a page, hint at editorial introduction.
INTRO_CUE_RE = C.compile_any([
    r"introduzione", r"introduction", r"premessa", r"nota al testo",
    r"nota editoriale", r"editorial note", r"redaz", r"datazione",
    r"Tritem", r"Trithem", r"dedica", r"manoscritt", r"redazione",
])
COMPARISON_TABLE_RE = C.compile_any([
    r"tav(?:ola)?\s+di\s+(?:raffronto|corrisponden)",  # tavola di raffronto/corrispondenza
    r"table\s+of\s+(?:comparison|concordance)",
    r"concordanz", r"corrisponden", r"raffronto", r"prospetto",
    r"1510", r"redazione\s+manoscritta",
])


def text_quality(text: str) -> tuple[str, list[str]]:
    """Classify embedded-text quality on a page; return (label, warnings)."""
    warnings: list[str] = []
    n = len(text.strip())
    if n == 0:
        return "empty", ["no embedded text — page may be scanned image"]
    # Replacement chars / control noise indicate bad extraction.
    repl = text.count("�")
    if repl:
        warnings.append(f"{repl} U+FFFD replacement chars")
    # Ratio of alphabetic content.
    alpha = sum(ch.isalpha() for ch in text)
    ratio = alpha / max(n, 1)
    if n < 80:
        label = "poor"
        warnings.append(f"very little text ({n} chars)")
    elif ratio < 0.45 or repl > 5:
        label = "partial"
        warnings.append(f"low alpha ratio {ratio:.2f}")
    else:
        label = "good"
    return label, warnings


def detect_printed_number(text: str) -> str | None:
    """Look at first/last few lines for a standalone page number."""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    for ln in lines[:2] + lines[-2:]:
        if PAGE_NUMBER_LINE_RE.match(ln) and len(ln) <= 6:
            return ln
    return None


def find_sigla_pages(pages: list[tuple[int, str]]) -> list[int]:
    """Pages that look like a sigla / conspectus siglorum list."""
    hits = []
    for idx, txt in pages:
        if C.SIGLA_LIST_RE.search(txt):
            hits.append(idx)
    return hits


def hunt_wuerzburg_siglum(pages: list[tuple[int, str]]) -> dict:
    """Find shelfmark / place-name anchors and try to read off the siglum.

    Strategy: on any page where the Wuerzburg anchor appears (shelfmark or
    Latin place name), inspect the surrounding line for a leading single
    letter or short token that the edition assigns as the siglum, e.g.
        "W = Wirceburgensis M.ch.q.50, saec. XVI ..."
    We report ALL candidate assignments with their evidence line so the human
    can confirm. We never silently commit to "W".
    """
    anchors = []
    candidate_sigla: Counter = Counter()
    # Parenthetical / prose assignment, e.g. (henceforth called "W"),
    # "siglum W", "designated W", "= W". This is the form Perrone Compagni
    # actually uses.
    assign_re = re.compile(
        r"(?:called|siglum|designat\w*|henceforth|indicat\w*|=)\s*"
        r"[\"'«»“”]?\s*([A-Z])\b", re.IGNORECASE)
    for idx, txt in pages:
        for m in C.WUERZBURG_ANCHOR_RE.finditer(txt):
            # Grab the line containing the match.
            start = txt.rfind("\n", 0, m.start()) + 1
            end = txt.find("\n", m.end())
            line = txt[start: end if end != -1 else len(txt)].strip()
            anchors.append({"page": idx, "match": m.group(0), "line": line[:300]})
            # (a) head-of-line assignment: "W = Wirceburgensis ..." / "W) ..."
            sig = re.match(r"^([A-Z][A-Za-z]?)\s*[=\):.–-]", line)
            if sig:
                candidate_sigla[sig.group(1)] += 1
            # (b) prose/parenthetical assignment in a window around the anchor,
            #     e.g. '... M.ch.q.50 ... (henceforth called "W").'
            window = txt[m.start(): min(len(txt), m.end() + 220)]
            for am in assign_re.finditer(window):
                candidate_sigla[am.group(1)] += 1
    return {
        "anchor_count": len(anchors),
        "anchors": anchors[:40],
        "candidate_sigla": candidate_sigla.most_common(),
    }


def recurring_marginalia(pages: list[tuple[int, str]]) -> dict:
    """Detect recurring first/last lines = running headers/footers."""
    first_lines: Counter = Counter()
    last_lines: Counter = Counter()
    for _, txt in pages:
        lines = [ln.strip() for ln in txt.split("\n") if ln.strip()]
        if lines:
            first_lines[re.sub(r"\d+", "#", lines[0])[:60]] += 1
            last_lines[re.sub(r"\d+", "#", lines[-1])[:60]] += 1
    return {
        "common_headers": [h for h in first_lines.most_common(8) if h[1] > 2],
        "common_footers": [f for f in last_lines.most_common(8) if f[1] > 2],
    }


def classify_zone(text: str) -> list[str]:
    """Cheap multi-label zone guess for a single page."""
    labels = []
    if INTRO_CUE_RE.search(text):
        labels.append("intro?")
    if COMPARISON_TABLE_RE.search(text) and ("1510" in text or "raffronto" in text.lower()):
        labels.append("comparison?")
    if CHAPTER_HEADING_RE.search(text):
        labels.append("chapter-heading")
    app_cues = len(APPARATUS_CUE_RE.findall(text))
    if app_cues >= 3:
        labels.append(f"apparatus?({app_cues})")
    return labels


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", help="Path to the edition PDF")
    ap.add_argument("--sample", type=int, default=6,
                    help="Sample pages per zone for excerpting")
    args = ap.parse_args()

    C.ensure_dirs()
    fitz = C.require_fitz()

    pdf_path = C.resolve_pdf(args.pdf)
    report = C.REPORTS / "pdf_inspection.md"

    if pdf_path is None:
        report.write_text(
            "# PDF Inspection Report\n\n"
            "**Status: NO PDF FOUND.**\n\n"
            "No PDF was supplied via `--pdf` and none was found in "
            "`data/raw/`.\n\n"
            "The target is Perrone Compagni's Brill critical edition of "
            "*De occulta philosophia libri tres* (on the user's local E: "
            "drive, not present in this environment).\n\n"
            "To run inspection, copy the edition PDF into `data/raw/` or pass "
            "`--pdf /path/to/edition.pdf`, then re-run:\n\n"
            "```\npython scripts/00_inspect_pdf.py --pdf /path/to/edition.pdf\n```\n",
            encoding="utf-8",
        )
        C.log(f"No PDF found. Wrote placeholder report to {report}")
        return

    C.log(f"Inspecting {pdf_path.name}")
    doc = fitz.open(pdf_path)
    n_pages = doc.page_count

    # Extract text once for all pages (cheap relative to OCR).
    pages: list[tuple[int, str]] = []
    qualities: Counter = Counter()
    has_text_pages = 0
    for i in range(n_pages):
        raw = doc.load_page(i).get_text("text")
        txt = C.normalize_text(raw)
        pages.append((i + 1, txt))
        q, _ = text_quality(txt)
        qualities[q] += 1
        if q != "empty":
            has_text_pages += 1

    embedded_ratio = has_text_pages / max(n_pages, 1)
    metadata = doc.metadata or {}

    # Zone scan.
    zone_hits: dict[str, list[int]] = {}
    for idx, txt in pages:
        for label in classify_zone(txt):
            base = label.split("(")[0].split("?")[0]
            zone_hits.setdefault(base, []).append(idx)

    sigla_pages = find_sigla_pages(pages)
    wuerzburg = hunt_wuerzburg_siglum(pages)
    marginalia = recurring_marginalia(pages)

    has_line_numbers = sum(
        1 for _, t in pages if len(LINE_NUMBER_RE.findall(t)) >= 5
    )

    # Build report.
    out = []
    out.append("# PDF Inspection Report — Phase 1\n")
    out.append(f"- **File:** `{pdf_path.name}`")
    out.append(f"- **Pages:** {n_pages}")
    out.append(f"- **Embedded-text pages:** {has_text_pages} "
               f"({embedded_ratio:.0%})")
    out.append(f"- **Quality breakdown:** " +
               ", ".join(f"{k}={v}" for k, v in qualities.most_common()))
    out.append(f"- **Pages with line-number gutters (>=5 small ints):** "
               f"{has_line_numbers}")
    out.append("")
    out.append("## PDF metadata")
    for k in ("title", "author", "subject", "producer", "creationDate"):
        if metadata.get(k):
            out.append(f"- **{k}:** {metadata[k]}")
    out.append("")

    out.append("## Embedded text vs. OCR")
    if embedded_ratio >= 0.9:
        out.append("Embedded text appears **present and usable** on nearly all "
                   "pages. OCR fallback likely unnecessary except on scanned "
                   "plates. Proceed to Phase 2 with embedded extraction.")
    elif embedded_ratio >= 0.5:
        out.append("Embedded text is **partial**. Phase 2 should OCR only the "
                   "`empty`/`poor` pages (selective fallback).")
    else:
        out.append("Embedded text is **largely absent** — this is likely a "
                   "scanned edition. Phase 2 will need OCR for most pages "
                   "(Latin + Greek + Hebrew language packs recommended).")
    out.append("")

    out.append("## Candidate zones (heuristic — refine in Phase 3)")
    for zone, idxs in sorted(zone_hits.items()):
        preview = ", ".join(map(str, idxs[:15]))
        more = "" if len(idxs) <= 15 else f" … (+{len(idxs)-15} more)"
        out.append(f"- **{zone}** — {len(idxs)} pages: {preview}{more}")
    out.append("")

    out.append("## Sigla list candidates")
    if sigla_pages:
        out.append(f"Pages mentioning sigla/manuscript-list cues: "
                   f"{', '.join(map(str, sigla_pages[:20]))}")
    else:
        out.append("No obvious sigla-list cue words found. The conspectus "
                   "siglorum may use different wording or be image-only.")
    out.append("")

    out.append("## Wuerzburg MS (M.ch.q.50) — siglum hunt")
    out.append(f"- Anchor matches (shelfmark / place name): "
               f"**{wuerzburg['anchor_count']}**")
    if wuerzburg["candidate_sigla"]:
        out.append("- **Candidate siglum assignments found** "
                   "(confirm against sigla list):")
        for sig, count in wuerzburg["candidate_sigla"]:
            out.append(f"  - `{sig}` ×{count}")
    else:
        out.append("- No `X = Wirceburgensis …` style assignment auto-parsed. "
                   "Inspect the anchor lines below manually.")
    if wuerzburg["anchors"]:
        out.append("\n  Evidence lines (first matches):")
        for a in wuerzburg["anchors"][:12]:
            out.append(f"  - p.{a['page']}: `{a['line']}`")
    out.append("")

    out.append("## Recurring headers / footers")
    if marginalia["common_headers"]:
        out.append("**Headers (normalised, # = digit):**")
        for h, c in marginalia["common_headers"]:
            out.append(f"- ×{c}: `{h}`")
    if marginalia["common_footers"]:
        out.append("\n**Footers:**")
        for f, c in marginalia["common_footers"]:
            out.append(f"- ×{c}: `{f}`")
    out.append("")

    # Sample excerpts (short, fair-use) from each detected zone.
    out.append("## Short sample excerpts (verification only)")
    out.append("_Excerpts are truncated to ~280 chars for verification; the "
               "pipeline never stores continuous edition text._\n")

    def sample_pages(label_idxs: list[int], k: int) -> list[int]:
        return label_idxs[:k]

    sample_targets = {
        "front matter / intro": zone_hits.get("intro", [1, 2, 3])[:args.sample],
        "comparison table": zone_hits.get("comparison", [])[:args.sample],
        "chapter headings": zone_hits.get("chapter-heading", [])[:2],
        "apparatus": zone_hits.get("apparatus", [])[:2],
    }
    page_text = {idx: t for idx, t in pages}
    for label, idxs in sample_targets.items():
        out.append(f"### {label}")
        if not idxs:
            out.append("_(no candidate pages detected)_\n")
            continue
        for idx in idxs:
            snippet = " ".join(page_text.get(idx, "").split())[:280]
            out.append(f"- **p.{idx}:** {snippet}…\n")

    out.append("## Next steps")
    out.append("1. Confirm the Wuerzburg siglum from the candidate(s) above "
               "(or by reading the listed anchor lines / sigla pages).")
    out.append("2. Set the confirmed siglum in `scripts/04_extract_apparatus.py` "
               "(`WUERZBURG_SIGLUM`).")
    out.append("3. Run Phase 2 (`01_extract_text.py`) then Phase 3 "
               "(`02_detect_structure.py`).")
    out.append("4. Tune the comparison-table page range from the zone list "
               "before running Phase 4.")

    report.write_text("\n".join(out) + "\n", encoding="utf-8")
    C.log(f"Wrote inspection report: {report}")
    doc.close()


if __name__ == "__main__":
    main()
