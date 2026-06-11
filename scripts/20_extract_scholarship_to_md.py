#!/usr/bin/env python3
"""
Phase 20 — Extract Agrippa scholarship PDFs to chunked markdown.

Reads every PDF in SOURCE_DIR, extracts text with PyMuPDF, cleans it,
and writes chunked .md files to SOURCE_DIR/markdown/.

Each output file:  markdown/<slug>/<slug>_chunk_NNN.md
Each chunk:        ~2 500 words (≈ 3 300 tokens), split on paragraph breaks.
Index file:        markdown/INDEX.md  listing every source with chunk count.

Usage:
    python scripts/20_extract_scholarship_to_md.py
"""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    raise SystemExit("PyMuPDF not installed. Run: pip install pymupdf")

SOURCE_DIR = Path(r"E:\pdf\renaissance magic\Agrippa")
OUT_DIR    = SOURCE_DIR / "markdown"
OUT_DIR.mkdir(exist_ok=True)

WORDS_PER_CHUNK = 2_500
MAX_CHUNK_CHARS = WORDS_PER_CHUNK * 6   # rough upper bound

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^\w\s-]", " ", s)
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"-{2,}", "-", s)
    return s[:80].rstrip("-")


def clean_text(raw: str) -> str:
    """Basic cleanup of PDF-extracted text."""
    # Remove form feeds
    text = raw.replace("\f", "\n\n")
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove hyphenation at line ends (common in academic PDFs)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Merge lines that clearly belong together (no sentence boundary)
    # — keep paragraph breaks (double newline) intact
    lines = text.split("\n")
    merged: list[str] = []
    for line in lines:
        line = line.rstrip()
        if not line:
            merged.append("")
        elif merged and merged[-1] and not merged[-1].endswith((".", "!", "?", ":", ";")):
            # continuation line — append with a space
            merged[-1] += " " + line
        else:
            merged.append(line)
    return "\n".join(merged)


def split_into_paragraphs(text: str) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\n+", text)]
    return [p for p in paras if len(p) > 20]


def chunk_paragraphs(paragraphs: list[str]) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    for para in paragraphs:
        word_count = len(para.split())
        if current_words + word_count > WORDS_PER_CHUNK and current:
            chunks.append("\n\n".join(current))
            current = [para]
            current_words = word_count
        else:
            current.append(para)
            current_words += word_count

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def extract_pdf(pdf_path: Path) -> tuple[str, list[str]]:
    """
    Returns (title_guess, list_of_page_texts).
    title_guess is the filename stem cleaned up.
    """
    doc = fitz.open(str(pdf_path))
    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return pages


def make_frontmatter(title: str, slug: str, source_file: str,
                     chunk_index: int, total_chunks: int,
                     page_range: tuple[int, int]) -> str:
    return f"""---
title: "{title}"
source_file: "{source_file}"
slug: "{slug}"
chunk: {chunk_index + 1}
total_chunks: {total_chunks}
pages: {page_range[0]}-{page_range[1]}
---

"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_pdf(pdf_path: Path) -> dict:
    stem = pdf_path.stem
    slug = slugify(stem)
    out_subdir = OUT_DIR / slug
    out_subdir.mkdir(exist_ok=True)

    print(f"  Extracting: {pdf_path.name[:70]}")

    pages = extract_pdf(pdf_path)
    if not pages:
        print(f"    [SKIP] No text extracted")
        return {"slug": slug, "title": stem, "chunks": 0, "pages": 0, "error": "no_text"}

    # Clean and join all pages, tracking page offsets
    page_texts = [clean_text(p) for p in pages]
    full_text = "\n\n".join(page_texts)

    paragraphs = split_into_paragraphs(full_text)
    if not paragraphs:
        return {"slug": slug, "title": stem, "chunks": 0, "pages": len(pages), "error": "no_paragraphs"}

    chunks = chunk_paragraphs(paragraphs)

    # Write chunks
    for i, chunk_text in enumerate(chunks):
        chunk_file = out_subdir / f"{slug}_chunk_{i+1:03d}.md"
        fm = make_frontmatter(
            title=stem[:120],
            slug=slug,
            source_file=pdf_path.name,
            chunk_index=i,
            total_chunks=len(chunks),
            page_range=(1, len(pages)),
        )
        chunk_file.write_text(fm + chunk_text, encoding="utf-8")

    print(f"    -> {len(chunks)} chunks from {len(pages)} pages")
    return {
        "slug": slug,
        "title": stem[:120],
        "source_file": pdf_path.name,
        "chunks": len(chunks),
        "pages": len(pages),
    }


def main() -> None:
    pdfs = sorted(SOURCE_DIR.glob("*.pdf"))
    print(f"Found {len(pdfs)} PDFs in {SOURCE_DIR}\n")

    index_entries: list[dict] = []
    for pdf_path in pdfs:
        entry = process_pdf(pdf_path)
        index_entries.append(entry)

    # Write INDEX.md
    index_md = "# Agrippa Scholarship — Markdown Extraction Index\n\n"
    index_md += f"Source: `{SOURCE_DIR}`  \n"
    index_md += f"Total PDFs: {len(pdfs)}\n\n"
    index_md += "| # | Title (truncated) | Chunks | Pages |\n"
    index_md += "|---|-------------------|--------|-------|\n"
    for i, e in enumerate(index_entries, 1):
        err = f" ⚠ {e.get('error','')}" if e.get("error") else ""
        index_md += f"| {i} | [{e['title'][:60]}]({e['slug']}/) | {e['chunks']} | {e.get('pages', 0)} |{err}\n"

    (OUT_DIR / "INDEX.md").write_text(index_md, encoding="utf-8")

    # Write machine-readable index
    (OUT_DIR / "index.json").write_text(
        json.dumps(index_entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    total_chunks = sum(e["chunks"] for e in index_entries)
    print(f"\nDone. {len(pdfs)} PDFs -> {total_chunks} total chunks.")
    print(f"Index: {OUT_DIR / 'INDEX.md'}")


if __name__ == "__main__":
    main()
