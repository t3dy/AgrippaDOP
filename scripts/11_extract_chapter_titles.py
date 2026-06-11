#!/usr/bin/env python3
"""
Phase 11 — Extract Latin chapter titles from the De occulta philosophia text.

Chapter headings appear as Latin text followed by "Cap. [roman]" on the same
or following line.  We find every "Cap." token, then look back up to 3 lines
for the title text.  Book assignment uses the 'heading' field in edition_structure.json.

Output: outputs/tables/chapter_titles.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
PAGES_JSONL = ROOT / "data" / "ocr" / "pages.jsonl"
STRUCT_JSON = ROOT / "data" / "indices" / "edition_structure.json"
OUT = ROOT / "outputs" / "tables" / "chapter_titles.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

CAP_RE = re.compile(r"\bCap(?:ut)?\.\s*([ivxlcdmIVXLCDM]+)\b", re.I)
# Lines that are clearly NOT title text
SKIP_TITLE_RE = re.compile(
    r"^\d+$|^LIBER|^DE OCCULTA|^INTRODUCTION|^TABLE|^INDEX|^PRIVILEGIUM",
    re.I,
)


def roman_to_int(s: str) -> int:
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    s = s.upper().replace("ς", "S").replace("π", "")  # handle OCR Greek
    total, prev = 0, 0
    for ch in reversed(s):
        v = vals.get(ch, 0)
        total += v if v >= prev else -v
        prev = v
    return total


def build_page_book_map() -> dict[int, int]:
    """Return {page_number: book (1/2/3)} using the 'heading' field."""
    struct = json.loads(STRUCT_JSON.read_text(encoding="utf-8"))
    result: dict[int, int] = {}
    cur_book = 1
    for u in sorted(struct["units"], key=lambda x: x["page_number"]):
        h = u.get("heading") or ""
        if "SECUNDUS" in h or "LIBER II" in h:
            cur_book = 2
        elif "TERTIUS" in h or "LIBER III" in h:
            cur_book = 3
        elif "PRIMUS" in h or "LIBER I" in h:
            cur_book = 1
        result[u["page_number"]] = cur_book
    return result


def load_edited_pages(page_book: dict[int, int]) -> list[tuple[int, int, str]]:
    """Return [(page_number, book, text)] for edited-text pages only."""
    struct = json.loads(STRUCT_JSON.read_text(encoding="utf-8"))
    valid = {
        u["page_number"]
        for u in struct["units"]
        if u.get("section_type") in (
            "edited_text", "edited_text+apparatus",
            "book_chapter_heading", "critical_apparatus",
        )
    }
    pages = []
    for raw in PAGES_JSONL.read_text(encoding="utf-8").splitlines():
        obj = json.loads(raw)
        pn = obj["page_number"]
        if pn in valid:
            pages.append((pn, page_book.get(pn, 1), obj["text"]))
    return sorted(pages)


def extract_titles(pages: list[tuple[int, int, str]]) -> dict[tuple[int, int], str]:
    """
    Slide a window over all lines; when we hit "Cap. N", scan back up to 3
    lines for the last non-trivial title fragment.
    """
    # Build a flat list of (book, line_text)
    all_lines: list[tuple[int, str]] = []
    for _pn, book, text in pages:
        for line in text.split("\n"):
            all_lines.append((book, line.strip()))

    titles: dict[tuple[int, int], str] = {}

    for i, (book, line) in enumerate(all_lines):
        m = CAP_RE.search(line)
        if not m:
            continue
        chap = roman_to_int(m.group(1))
        if chap == 0 or chap > 120:
            continue

        # Collect title: text before "Cap." on the same line, or scan back
        before_cap = line[: m.start()].strip().rstrip(".").strip().lstrip("{").strip()
        if len(before_cap) > 8:
            title = before_cap
        else:
            # Scan backwards for title fragments
            frags = []
            for j in range(i - 1, max(i - 4, -1), -1):
                prev_line = all_lines[j][1]
                if not prev_line or SKIP_TITLE_RE.match(prev_line):
                    break
                # Stop if we hit another chapter or a section break
                if CAP_RE.search(prev_line):
                    break
                if len(prev_line) > 3:
                    frags.insert(0, prev_line.lstrip("{").strip())
            title = " ".join(frags).rstrip(".").strip() if frags else before_cap

        if len(title) > 5 and (book, chap) not in titles:
            titles[(book, chap)] = title

    return titles


def main() -> None:
    page_book = build_page_book_map()
    pages = load_edited_pages(page_book)
    print(f"[chapter_titles] Scanning {len(pages)} edited-text pages ...")

    titles = extract_titles(pages)

    result = [
        {"book": b, "chapter": c, "title_latin": t}
        for (b, c), t in sorted(titles.items())
    ]
    by_book: dict[int, int] = {}
    for e in result:
        by_book[e["book"]] = by_book.get(e["book"], 0) + 1
    print(f"[chapter_titles] Found {len(result)} titles — by book: {by_book}")
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[chapter_titles] Wrote {OUT}")


if __name__ == "__main__":
    main()
