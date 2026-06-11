#!/usr/bin/env python3
"""
Phase 5 — Apparatus extraction (Wuerzburg witness)  [SCAFFOLD].

Isolates the critical apparatus from the edited text and extracts entries that
cite the Wuerzburg manuscript (MS Wuerzburg M.ch.q.50).

IMPORTANT: do NOT assume the siglum is "W". Set WUERZBURG_SIGLUM below only
after confirming it from the edition's conspectus siglorum (Phase 1 reports
candidates). Until confirmed, the parser runs in "discovery" mode and reports
all apparatus entries near a Wuerzburg anchor instead.

Per-entry fields: page_number, book/chapter/section (if detectable),
line_or_lemma, sigla, variant_type, short_lemma (legally minimal), paraphrase,
confidence, raw_excerpt (minimal, verification only).

Outputs:
  outputs/tables/wurzburg_apparatus_entries.csv
  outputs/tables/wurzburg_apparatus_entries.json
  outputs/reports/apparatus_extraction_method.md
"""

from __future__ import annotations

import argparse
import csv
import json
import re

import common as C


# Set this ONLY after confirming from the sigla list. None => discovery mode.
WUERZBURG_SIGLUM: str | None = None

VARIANT_TYPE_CUES = {
    "omission": [r"\bom\.", r"\bdeest\b", r"omit"],
    "addition": [r"\badd\.", r"\bsuppl\.", r"\bin marg\."],
    "substitution": [r"\bcorr\.", r"\bscr\.", r"\bpro\b"],
    "transposition": [r"\btransp\.", r"\binv\.", r"\bord\. inv\."],
    "orthographic": [r"\bsic\b", r"\borthogr"],
}


def classify_variant(excerpt: str) -> str:
    for vtype, cues in VARIANT_TYPE_CUES.items():
        if any(re.search(c, excerpt, re.IGNORECASE) for c in cues):
            return vtype
    return "uncertain"


def apparatus_lines(text: str):
    """Yield candidate apparatus lines (those containing a lemma bracket or
    standard sigla abbreviations)."""
    for ln in text.split("\n"):
        if "]" in ln or re.search(r"\b(om|add|corr|scr|del|suppl)\.", ln):
            yield ln.strip()


def entry_mentions_wuerzburg(line: str, siglum: str | None) -> bool:
    if siglum:
        # Word-boundary match on the confirmed siglum token.
        return re.search(rf"(?<![A-Za-z]){re.escape(siglum)}(?![A-Za-z])", line) is not None
    # Discovery mode: match shelfmark/place anchors.
    return C.WUERZBURG_ANCHOR_RE.search(line) is not None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--siglum", help="Confirmed Wuerzburg siglum "
                                     "(overrides module default)")
    args = ap.parse_args()
    C.ensure_dirs()

    siglum = args.siglum or WUERZBURG_SIGLUM
    mode = f"siglum='{siglum}'" if siglum else "DISCOVERY (anchors)"
    C.log(f"Apparatus extraction mode: {mode}")

    if not C.PAGES_JSONL.exists():
        C.log("pages.jsonl missing — run Phase 2 first.")
        return

    entries = []
    for rec in C.read_jsonl(C.PAGES_JSONL):
        page_no = rec["page_number"]
        text = rec.get("text", "")
        for line in apparatus_lines(text):
            if not entry_mentions_wuerzburg(line, siglum):
                continue
            lemma = line.split("]", 1)[0].strip() if "]" in line else None
            entries.append({
                "page_number": page_no,
                "book_1533": None,
                "chapter_1533": None,
                "line_or_lemma": (lemma or "")[:60],
                "sigla": siglum or "(anchor)",
                "variant_type": classify_variant(line),
                "variant_summary": "",        # paraphrase added in review
                "raw_excerpt": " ".join(line.split())[:160],
                "confidence": 0.4 if siglum else 0.25,
            })

    out_json = C.TABLES / "wurzburg_apparatus_entries.json"
    out_csv = C.TABLES / "wurzburg_apparatus_entries.csv"
    out_json.write_text(json.dumps(entries, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    if entries:
        with out_csv.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(entries[0].keys()))
            w.writeheader()
            w.writerows(entries)

    (C.REPORTS / "apparatus_extraction_method.md").write_text(
        "# Apparatus extraction method\n\n"
        f"- Mode: **{mode}**\n"
        f"- Candidate Wuerzburg apparatus entries: **{len(entries)}**\n\n"
        "## Method\n"
        "1. Lines containing a lemma bracket `]` or standard sigla "
        "abbreviations (`om.`, `add.`, `corr.`, …) are treated as apparatus.\n"
        "2. Entries are kept when they mention the confirmed Wuerzburg siglum "
        "(or, in discovery mode, a shelfmark/place anchor).\n"
        "3. Variant type is guessed from abbreviation cues; `uncertain` "
        "otherwise.\n\n"
        "**Confirm the siglum** (Phase 1 report) and re-run with "
        "`--siglum <X>` to leave discovery mode. Raw excerpts are truncated to "
        "~160 chars for verification only.\n",
        encoding="utf-8")
    C.log(f"Wrote {len(entries)} apparatus entries ({mode})")


if __name__ == "__main__":
    main()
