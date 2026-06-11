#!/usr/bin/env python3
"""
Phase 10 — Parse the Table of Comparison into clean structured JSON.

The comparison table spans PDF pages 62-69 (effectively 64-69 for content).
Two OCR artefact modes exist:
  - Row-by-row (page 64): chapter ref then description, alternating.
    BUT mid-page the OCR fragments "1: 16" into separate lines "1" + "16"
    and "W, 1:9" into "W, 1" + "9".  We reconstruct those before parsing.
  - Column-by-column (pages 65-69): all left-column refs first, then all
    right-column descriptions.

Output: outputs/tables/comparison_table.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
PAGES_JSONL = ROOT / "data" / "ocr" / "pages.jsonl"
STRUCT_JSON = ROOT / "data" / "indices" / "edition_structure.json"
OUT = ROOT / "outputs" / "tables" / "comparison_table.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Patterns                                                                     #
# --------------------------------------------------------------------------- #

CHAPTER_REF_RE = re.compile(r"^([123]):\s*(\d+)\s*$")           # "1: 37"
EPIST_REF_RE   = re.compile(r"^Epist\.?\s*(.*)", re.I)
DESC_START_RE  = re.compile(r"^[Ww][,\.]|^new\b|^Hermanno\b|^same\b|^omitted\b", re.I)

# Lines that are purely structural noise
NOISE_LINE_RE = re.compile(
    r"^(TABLE\s+OF\s+COMPARISON|Edition\s*\(|Manuscript\s*\(|"
    r"sent\s+from|LIBER|DE\s+OCCULTA|INTRODUCTION)\b",
    re.I,
)


def load_pages(page_numbers: list[int]) -> dict[int, str]:
    pages: dict[int, str] = {}
    for raw in PAGES_JSONL.read_text(encoding="utf-8").splitlines():
        obj = json.loads(raw)
        pn = obj["page_number"]
        if pn in page_numbers:
            pages[pn] = obj["text"]
    return pages


# --------------------------------------------------------------------------- #
# Fragment reconstruction                                                      #
# --------------------------------------------------------------------------- #

def reconstruct(lines: list[str]) -> list[str]:
    """
    Merge OCR line-split artefacts:
      ["1", "16"]          → ["1:16"]
      ["2", "34"]          → ["2:34"]
      ["W, 1", "9"]        → ["W, 1:9"]
      ["W, 2", "15 + ..."] → ["W, 2:15 + ..."]
      ["w, 1", "10"]       → ["W, 1:10"]
    """
    result: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Book-number fragment (bare "1", "2", or "3")
        if re.match(r"^[123]$", line) and i + 1 < len(lines):
            nxt = lines[i + 1]
            if re.match(r"^\d+", nxt):                # next is chapter num or "37 + ..."
                chap_part = nxt.split()[0]             # take just the leading digits
                rest = nxt[len(chap_part):].strip()
                reconstructed = f"{line}:{chap_part}" + (" " + rest if rest else "")
                result.append(reconstructed)
                i += 2
                continue
        # W-reference fragment: "W, 1"  or "w, 2" etc.
        if re.match(r"^[Ww][,\.]\s*[123]$", line) and i + 1 < len(lines):
            nxt = lines[i + 1]
            if re.match(r"^\d+", nxt) or re.match(r"^[Ee]pi", nxt):
                book = re.search(r"[123]", line).group()
                result.append(f"W, {book}:{nxt}")
                i += 2
                continue
        result.append(line)
        i += 1
    return result


def clean(text: str) -> list[str]:
    """Strip noise lines, bare page numbers, then reconstruct fragments."""
    raw: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if NOISE_LINE_RE.match(line):
            continue
        if re.match(r"^\d{1,3}$", line):          # bare page numbers ("55", "58" …)
            raw.append(line)                       # keep for fragment detection first
            continue
        raw.append(line)
    # Second pass: filter bare page-only lines that don't serve as book frags
    # We keep "1","2","3" (possible book frags); drop 2-3 digit page numbers
    filtered: list[str] = []
    for line in raw:
        if re.match(r"^\d{2,3}$", line):           # two- or three-digit bare numbers
            continue
        filtered.append(line)
    return reconstruct(filtered)


def classify(line: str) -> str:
    if CHAPTER_REF_RE.match(line):
        return "ref"
    if EPIST_REF_RE.match(line):
        return "ref"
    if DESC_START_RE.match(line):
        return "desc"
    return "cont"


def ref_parts(line: str) -> tuple[int, int, str]:
    m = CHAPTER_REF_RE.match(line)
    if m:
        b, c = int(m.group(1)), int(m.group(2))
        return b, c, f"{b}:{c}"
    em = EPIST_REF_RE.match(line)
    if em:
        recipient = em.group(1).strip()
        return 0, 0, f"Epist. {recipient}" if recipient else "Epist."
    return 0, 0, line


# --------------------------------------------------------------------------- #
# Two layout parsers                                                           #
# --------------------------------------------------------------------------- #

def parse_row_by_row(lines: list[str]) -> list[dict]:
    """Interleaved format: ref, desc-line(s), ref, desc-line(s), …"""
    entries: list[dict] = []
    i = 0
    while i < len(lines):
        if classify(lines[i]) == "ref":
            book, chap, label = ref_parts(lines[i])
            i += 1
            desc_parts: list[str] = []
            while i < len(lines) and classify(lines[i]) != "ref":
                if classify(lines[i]) in ("desc", "cont"):
                    desc_parts.append(lines[i])
                i += 1
            entries.append({
                "book_1533": book,
                "chapter_1533": chap,
                "label_1533": label,
                "ms_description": " ".join(desc_parts).strip(),
            })
        else:
            i += 1
    return entries


def parse_column_by_column(lines: list[str]) -> list[dict]:
    """Column-separated: all refs first, then all descriptions."""
    # Find where refs end and descs begin
    split_idx: int | None = None
    for i, line in enumerate(lines):
        if classify(line) == "desc":
            split_idx = i
            break
        # A continuation line after refs means we've entered descriptions
        if i > 0 and classify(lines[i - 1]) == "ref" and classify(line) == "cont":
            split_idx = i
            break

    if split_idx is None:
        # Only refs, no descriptions found on this page
        return [
            {"book_1533": b, "chapter_1533": c, "label_1533": lbl,
             "ms_description": ""}
            for b, c, lbl in (ref_parts(l) for l in lines if classify(l) == "ref")
        ]

    ref_lines  = [l for l in lines[:split_idx] if classify(l) == "ref"]
    desc_lines = lines[split_idx:]

    # Rebuild descriptions: new entry whenever a DESC_START_RE line appears
    descs: list[str] = []
    current: list[str] = []
    for line in desc_lines:
        if classify(line) == "desc" and current:
            descs.append(" ".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        descs.append(" ".join(current).strip())

    if len(descs) != len(ref_lines):
        print(
            f"  [col] {len(ref_lines)} refs vs {len(descs)} descs — "
            f"padding shorter side",
            file=sys.stderr,
        )

    entries: list[dict] = []
    for idx, ref in enumerate(ref_lines):
        b, c, lbl = ref_parts(ref)
        entries.append({
            "book_1533": b,
            "chapter_1533": c,
            "label_1533": lbl,
            "ms_description": descs[idx] if idx < len(descs) else "",
        })
    return entries


# --------------------------------------------------------------------------- #
# Page-64 fragment recovery                                                    #
# --------------------------------------------------------------------------- #

# Pattern: line "1", then chapter number (possibly with continuation),
# then description starting with W/ or "new".
# Groups: (1) 1533 chapter num, (2) first desc token, (3) desc remainder
_P64_ENTRY_RE = re.compile(
    r"^1\n"                                         # book number line
    r"(\d+)\n"                                      # 1533 chapter number
    r"([Ww][,\.][^\n]*|new[^\n]*)",                 # start of description
    re.MULTILINE,
)

# Captures "W, 1\n9" → "W, 1:9" style fragments in the desc
_W_FRAG_RE = re.compile(r"([Ww][,\.]\s*[123])\n(\d[^\n]*)")


def recover_fragmented_p64(text: str) -> list[dict]:
    """
    Extract the OCR-fragmented chapters 1:16–1:36 from the raw page 64 text
    by applying multi-line patterns directly on the raw string.
    """
    # First, repair "W, 1\n9" → "W, 1:9" style splits in raw text
    repaired = _W_FRAG_RE.sub(lambda m: f"{m.group(1)}:{m.group(2)}", text)
    # Also fix "w,\n1\n13" (W comma, newline, book, newline, chap+desc)
    repaired = re.sub(
        r"([Ww],)\n([123])\n(\d[^\n]*)",
        lambda m: f"W, {m.group(2)}:{m.group(3)}",
        repaired,
    )

    entries = []
    for m in _P64_ENTRY_RE.finditer(repaired):
        chap = int(m.group(1))
        if chap <= 15:          # already captured by row-by-row pass
            continue
        desc = m.group(2).strip()
        # Normalise "w," → "W,"
        desc = re.sub(r"^w[,\.]", "W,", desc)
        entries.append({
            "book_1533": 1,
            "chapter_1533": chap,
            "label_1533": f"1:{chap}",
            "ms_description": desc,
        })
    return entries


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #

def main() -> None:
    struct = json.loads(STRUCT_JSON.read_text(encoding="utf-8"))
    hint_pages: list[int] = struct["navigation_hints"].get("comparison_table_pages", [])
    # Drop the ToC page (7) — not the actual table
    comp_pages = sorted(p for p in hint_pages if p >= 60)
    print(f"[parse_comparison] Using pages: {comp_pages}")

    raw_pages = load_pages(comp_pages)
    all_entries: list[dict] = []

    for pn in comp_pages:
        text = raw_pages.get(pn, "")
        lines = clean(text)
        if not lines:
            print(f"  p{pn}: empty after cleaning — skipping")
            continue

        # Decide layout: if the first several substantive lines are ALL refs
        # with no descs, it is column-by-column.
        first_n = lines[:min(8, len(lines))]
        ref_cnt  = sum(1 for l in first_n if classify(l) == "ref")
        desc_cnt = sum(1 for l in first_n if classify(l) in ("desc", "cont"))

        if ref_cnt >= 4 and desc_cnt == 0:
            mode = "col"
        else:
            mode = "row"

        entries = (parse_row_by_row(lines) if mode == "row"
                   else parse_column_by_column(lines))
        print(f"  p{pn} [{mode}]: {len(entries)} entries")
        all_entries.extend(entries)

    # --- Recovery: page 64 OCR-fragmented chapters 1:16–1:36 ---------------
    # ABBYY split "1\n16\nW, 1\n9" (book / chap / desc) across lines.
    # The chapter numbers (2-digit) were filtered as page numbers.
    # We recover them with a multi-line regex on the raw page 64 text.
    p64_text = raw_pages.get(64, "")
    recovery_entries = recover_fragmented_p64(p64_text)
    print(f"  p64 [recovery]: {len(recovery_entries)} additional entries")
    all_entries.extend(recovery_entries)

    # Deduplicate by label (keep first occurrence — earlier pages are higher
    # quality due to less ABBYY fragmentation)
    seen: set[str] = set()
    deduped: list[dict] = []
    for e in all_entries:
        lbl = e["label_1533"]
        if lbl not in seen:
            seen.add(lbl)
            deduped.append(e)

    # Sort: Epistles first (book=0), then by book + chapter number
    deduped.sort(key=lambda e: (e["book_1533"], e["chapter_1533"],
                                e["label_1533"]))

    OUT.write_text(json.dumps(deduped, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"[parse_comparison] Wrote {len(deduped)} entries -> {OUT}")

    # Quick summary
    by_book: dict[int, int] = {}
    for e in deduped:
        by_book[e["book_1533"]] = by_book.get(e["book_1533"], 0) + 1
    for b in sorted(by_book):
        label = {0: "Epistles", 1: "Book I", 2: "Book II", 3: "Book III"}.get(b, f"Book {b}")
        print(f"    {label}: {by_book[b]} entries")


if __name__ == "__main__":
    main()
