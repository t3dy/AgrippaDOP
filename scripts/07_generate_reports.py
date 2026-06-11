#!/usr/bin/env python3
"""
Phase 9 — Generate reports  [SCAFFOLD].

Renders the deliverable markdown reports + the chapter status matrix CSV from
the SQLite database. Reports are scholarly summaries/paraphrases with page
references — never continuous transcription.

Reports produced:
  outputs/reports/1510_draft_reconstruction.md
  outputs/reports/1533_additions_after_1510.md
  outputs/reports/revision_patterns.md
  outputs/reports/theme_matrix.md
  outputs/reports/source_and_authority_changes.md
  outputs/reports/uncertainties_and_manual_review.md
  outputs/tables/chapter_status_matrix.csv

STATUS: scaffold. Renders headers + whatever rows already exist in the DB so
the pipeline is end-to-end runnable; full narrative synthesis depends on
Phases 4-8 having been populated.

Usage:
    python scripts/07_generate_reports.py
"""

from __future__ import annotations

import csv
import sqlite3

import common as C


def q(con, sql, params=()):
    return con.execute(sql, params).fetchall()


def main() -> None:
    C.ensure_dirs()
    if not C.DB_PATH.exists():
        C.log("Database missing — run Phase 6 first.")
        return
    con = sqlite3.connect(C.DB_PATH)
    con.row_factory = sqlite3.Row

    n_pages = q(con, "SELECT COUNT(*) FROM edition_pages")[0][0]
    n_cmp = q(con, "SELECT COUNT(*) FROM comparison_map")[0][0]
    n_app = q(con, "SELECT COUNT(*) FROM apparatus_entries")[0][0]
    n_assess = q(con, "SELECT COUNT(*) FROM passage_assessments")[0][0]

    header = (f"_Generated from {C.DB_PATH.name}. Pages={n_pages}, "
              f"comparison_rows={n_cmp}, apparatus_entries={n_app}, "
              f"assessments={n_assess}._\n\n")

    reports = {
        "1510_draft_reconstruction.md":
            "# Reconstruction of the 1510 Wuerzburg Draft\n\n" + header +
            "Scholarly summary of what the 1510 draft appears to have "
            "contained, by book/chapter, from comparison-table + apparatus + "
            "introduction evidence. (Populated after Phases 4-8.)\n",
        "1533_additions_after_1510.md":
            "# Material Added After 1510 (1533 vs draft)\n\n" + header +
            "Chapter-by-chapter list of passages absent from / added after the "
            "1510 draft, with evidence references.\n",
        "revision_patterns.md":
            "# Revision Patterns 1510 -> 1533\n\n" + header +
            "Analytical account of expansion, rearrangement, intensification "
            "of Cabala, added authorities, doctrinal change.\n",
        "theme_matrix.md":
            "# Theme Matrix\n\n" + header +
            "Themes x chapter with 1510 status (present/added/expanded/"
            "revised/uncertain).\n",
        "source_and_authority_changes.md":
            "# Source & Authority Changes\n\n" + header +
            "Changes in cited/implied authorities (Ficino, Hermetica, "
            "pseudo-Dionysius, scholastic, patristic) between versions.\n",
        "uncertainties_and_manual_review.md":
            "# Uncertainties & Manual Review Queue\n\n" + header +
            "Unresolved extraction problems, ambiguous apparatus, uncertain "
            "chapter mappings, pages needing human review.\n",
    }
    for name, body in reports.items():
        (C.REPORTS / name).write_text(body, encoding="utf-8")

    # chapter_status_matrix.csv
    cols = ["book_1533", "chapter_1533", "title_or_incision", "status_1510",
            "evidence_source", "main_themes", "revision_summary", "confidence",
            "page_refs"]
    rows = q(con, "SELECT book_1533, chapter_1533, status_1510, evidence_type, "
                  "summary, confidence, evidence_refs FROM passage_assessments")
    with (C.TABLES / "chapter_status_matrix.csv").open(
            "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([r["book_1533"], r["chapter_1533"], "", r["status_1510"],
                        r["evidence_type"], "", r["summary"], r["confidence"],
                        r["evidence_refs"]])
    con.close()
    C.log(f"Wrote {len(reports)} reports + chapter_status_matrix.csv "
          f"({len(rows)} assessment rows)")


if __name__ == "__main__":
    main()
