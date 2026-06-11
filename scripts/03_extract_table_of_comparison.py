#!/usr/bin/env python3
"""
Phase 4 — Extract the Table of Comparison  [SCAFFOLD].

Locates the comparison / concordance table (1510 manuscript redaction vs the
1533 three-book structure) using the page hints from Phase 3, then parses rows
into a structured table.

Outputs (when implemented against the real layout):
  outputs/tables/table_of_comparison.csv
  outputs/tables/table_of_comparison.json
  outputs/reports/table_of_comparison_summary.md

Target row fields:
  ms_1510_locus, book_1533, chapter_1533, title_or_incipit, perrone_page,
  notes, confidence, raw_snippet (SHORT excerpt only — verification only).

STATUS: scaffold. Row parsing is deliberately not finalised because the exact
column layout (whether 1510 loci are given as folios, as chapter lists, or only
as prose cross-references) must be read off the real edition first. Phase 1's
inspection report lists the candidate comparison-table pages to target here.
"""

from __future__ import annotations

import argparse
import csv
import json
import re

import common as C


# Heuristic row pattern: a 1533 reference like "I, 12" or "II.7" possibly with
# a page and a 1510 cue. Refine after seeing the real table.
ROW_RE = re.compile(
    r"(?P<book>[IVX]+)[\.,]\s*(?P<chap>\d+)\b.*?(?P<page>\d{1,4})?")


def load_comparison_pages() -> list[int]:
    if not C.EDITION_STRUCTURE.exists():
        return []
    data = json.loads(C.EDITION_STRUCTURE.read_text(encoding="utf-8"))
    return data.get("navigation_hints", {}).get("comparison_table_pages", [])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", help="Comma-separated page range override, "
                                    "e.g. 18,19,20")
    args = ap.parse_args()
    C.ensure_dirs()

    pages = ([int(x) for x in args.pages.split(",")] if args.pages
             else load_comparison_pages())
    if not pages:
        C.log("No comparison-table pages identified. Inspect "
              "outputs/reports/pdf_inspection.md and pass --pages.")
        return

    by_page = {r["page_number"]: r.get("text", "")
               for r in C.read_jsonl(C.PAGES_JSONL)} if C.PAGES_JSONL.exists() else {}

    rows = []
    for p in pages:
        text = by_page.get(p, "")
        for line in text.split("\n"):
            m = ROW_RE.search(line)
            if not m:
                continue
            rows.append({
                "ms_1510_locus": None,           # fill once layout is known
                "book_1533": m.group("book"),
                "chapter_1533": m.group("chap"),
                "title_or_incipit": None,
                "perrone_page": m.group("page"),
                "notes": "",
                "confidence": 0.3,
                "raw_snippet": " ".join(line.split())[:120],
            })

    # Write whatever we found (likely needs manual tuning).
    out_json = C.TABLES / "table_of_comparison.json"
    out_csv = C.TABLES / "table_of_comparison.csv"
    out_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    if rows:
        with out_csv.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    (C.REPORTS / "table_of_comparison_summary.md").write_text(
        "# Table of Comparison — extraction summary (DRAFT)\n\n"
        f"- Pages scanned: {pages}\n- Candidate rows: {len(rows)}\n\n"
        "**Manual review required.** Confirm column layout against the edition "
        "and refine `ROW_RE` / field mapping before trusting these rows.\n",
        encoding="utf-8")
    C.log(f"Wrote {len(rows)} candidate rows (DRAFT) for pages {pages}")


if __name__ == "__main__":
    main()
