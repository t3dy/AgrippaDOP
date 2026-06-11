#!/usr/bin/env python3
"""
Phase 3 — Detect edition structure.

Reads data/ocr/pages.jsonl and segments the edition into labelled units:
  - introduction
  - table_of_comparison
  - sigla_list
  - book_chapter_heading
  - edited_text
  - critical_apparatus
  - source_apparatus  (if the edition separates source from variant apparatus)
  - index_or_bibliography
  - front_matter / unknown

Output: data/indices/edition_structure.json

Each unit records page number, section type, heading, char offsets (relative
to that page's text), a confidence score, and notes on ambiguity.

These are HEURISTICS designed to be tuned after the real PDF is inspected.
They prefer to label conservatively and mark low confidence rather than assert.

Usage:
    python scripts/02_detect_structure.py
"""

from __future__ import annotations

import re

import common as C


# --------------------------------------------------------------------------
# Patterns (shared spirit with Phase 1, kept local for standalone use)
# --------------------------------------------------------------------------
BOOK_RE = re.compile(
    r"(?im)^\s*(LIBER|LIB\.)\s+(PRIMUS|SECUNDUS|TERTIUS|[IVX]+)\b.*$")
CHAPTER_RE = re.compile(
    r"(?im)^\s*(CAPUT|CAP\.|CAPITULUM)\s+([IVXLCDM]+|\d+)\b.*$")
APPARATUS_CUE_RE = re.compile(
    r"\]\s|\bom\.|\badd\.|\bcorr\.|\bcodd?\.|\bscr\.|\bdel\.|\bsuppl\.|\bmarg\.")
SOURCE_APP_CUE_RE = re.compile(
    r"\bcf\.\b|\bvid\.\b|\bPL\b|\bPG\b|\bMigne\b|\bCorp\.|\bcfr\.\b")
INDEX_CUE_RE = C.compile_any([
    r"index nominum", r"index rerum", r"indice dei nomi", r"bibliografia",
    r"bibliography", r"indice", r"index locorum",
])
INTRO_CUE_RE = C.compile_any([
    r"introduzione", r"introduction", r"nota al testo", r"nota editoriale",
    r"datazione", r"redazione", r"Tritem", r"Trithem", r"dedica",
    r"premessa", r"editorial",
])
COMPARISON_CUE_RE = C.compile_any([
    r"tav(?:ola)?\s+di\s+(?:raffronto|corrisponden|concordan)",
    r"table\s+of\s+(?:comparison|concordance)",
    r"prospetto", r"concordanz", r"raffronto",
])


def page_apparatus_density(text: str) -> float:
    cues = len(APPARATUS_CUE_RE.findall(text))
    lines = max(text.count("\n"), 1)
    return cues / lines


def first_heading(text: str) -> str | None:
    m = BOOK_RE.search(text) or CHAPTER_RE.search(text)
    if m:
        return " ".join(m.group(0).split())[:120]
    return None


def classify_page(text: str) -> tuple[str, float, str]:
    """Return (section_type, confidence, notes) for a page's full text."""
    notes = []
    t = text.strip()
    if not t:
        return "blank", 0.9, "empty page"

    low = t.lower()
    app_density = page_apparatus_density(t)
    has_book = bool(BOOK_RE.search(t))
    has_chapter = bool(CHAPTER_RE.search(t))
    src_cues = len(SOURCE_APP_CUE_RE.findall(t))

    # Strong structural cues first.
    if COMPARISON_CUE_RE.search(t) and ("1510" in t or app_density < 0.2):
        return "table_of_comparison", 0.7, "comparison cue words present"
    if C.SIGLA_LIST_RE.search(t) and len(t) < 4000:
        return "sigla_list", 0.6, "sigla/manuscript-list cues"
    if INDEX_CUE_RE.search(t):
        return "index_or_bibliography", 0.7, "index/bibliography cue"

    # Apparatus-heavy page (variant readings).
    if app_density >= 0.25:
        if src_cues >= 4 and src_cues > len(APPARATUS_CUE_RE.findall(t)) / 2:
            return "source_apparatus", 0.45, "many cf./PL/PG citation cues"
        return "critical_apparatus", 0.55, f"apparatus density {app_density:.2f}"

    # Edited text with a heading.
    if has_book or has_chapter:
        notes.append("heading present")
        # Mixed: text on top, apparatus at foot.
        if app_density >= 0.08:
            return "edited_text+apparatus", 0.5, "heading + footer apparatus"
        return "book_chapter_heading", 0.6, "; ".join(notes)

    # Introduction prose.
    intro_hits = len(INTRO_CUE_RE.findall(t))
    if intro_hits >= 2:
        return "introduction", 0.5, f"{intro_hits} intro cue words"

    # Default: plain edited text vs unknown front matter.
    if len(t) > 600:
        return "edited_text", 0.35, "prose, no heading detected"
    return "front_matter_or_unknown", 0.3, "short page, no strong cue"


def heading_offsets(text: str):
    """Yield (heading_text, start, end) for each book/chapter heading."""
    for m in list(BOOK_RE.finditer(text)) + list(CHAPTER_RE.finditer(text)):
        yield " ".join(m.group(0).split())[:120], m.start(), m.end()


def main() -> None:
    C.ensure_dirs()
    if not C.PAGES_JSONL.exists():
        C.log(f"{C.PAGES_JSONL} not found — run Phase 2 first.")
        C.write_json(C.EDITION_STRUCTURE, {
            "status": "no_input",
            "message": "Run 01_extract_text.py first to produce pages.jsonl",
            "units": [],
        })
        return

    units = []
    type_counts: dict[str, int] = {}
    for rec in C.read_jsonl(C.PAGES_JSONL):
        page_no = rec["page_number"]
        text = rec.get("text", "")
        section_type, confidence, notes = classify_page(text)
        type_counts[section_type] = type_counts.get(section_type, 0) + 1

        unit = {
            "page_number": page_no,
            "printed_number": rec.get("printed_number"),
            "section_type": section_type,
            "heading": first_heading(text),
            "char_start": 0,
            "char_end": len(text),
            "confidence": confidence,
            "extraction_quality": rec.get("extraction_quality"),
            "notes": notes,
            "headings_on_page": [
                {"heading": h, "char_start": s, "char_end": e}
                for (h, s, e) in heading_offsets(text)
            ],
        }
        units.append(unit)

    # Light post-processing: smooth obvious apparatus runs and find the
    # contiguous comparison-table block (helps Phase 4).
    comparison_pages = [u["page_number"] for u in units
                        if u["section_type"] == "table_of_comparison"]
    sigla_pages = [u["page_number"] for u in units
                   if u["section_type"] == "sigla_list"]
    intro_pages = [u["page_number"] for u in units
                   if u["section_type"] == "introduction"]

    structure = {
        "status": "ok",
        "source_pages": len(units),
        "section_type_counts": type_counts,
        "navigation_hints": {
            "introduction_pages": intro_pages,
            "sigla_list_pages": sigla_pages,
            "comparison_table_pages": comparison_pages,
            "apparatus_pages": [u["page_number"] for u in units
                                if "apparatus" in u["section_type"]][:200],
        },
        "caveat": ("Section types are heuristic (confidence < 0.7 for most). "
                   "Confirm comparison-table and sigla-list ranges manually "
                   "against outputs/reports/pdf_inspection.md before Phase 4/5."),
        "units": units,
    }
    C.write_json(C.EDITION_STRUCTURE, structure)
    C.log(f"Wrote structure for {len(units)} pages to {C.EDITION_STRUCTURE}")
    C.log("Section type counts: " +
          ", ".join(f"{k}={v}" for k, v in sorted(type_counts.items())))


if __name__ == "__main__":
    main()
