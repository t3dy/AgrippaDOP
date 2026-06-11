#!/usr/bin/env python3
"""
Phase 7 — Chunk for targeted LLM reading  [SCAFFOLD].

Builds prioritised chunk files (data/chunks/*.json) from the structured pages.
Chunks correspond to meaningful units (intro subsections, comparison-table
pages, chapter+apparatus units) and carry page + section metadata. Chunks that
touch the Wuerzburg witness, the comparison table, editorial discussion of
1510, or dense apparatus are prioritised.

Each chunk is paired with a prompt that asks the LLM for STRUCTURED JSON ONLY
(schema in PROMPT_SCHEMA below) and to paraphrase rather than reproduce text.

Usage:
    python scripts/05_chunk_for_llm.py [--max-chars 6000]
"""

from __future__ import annotations

import argparse
import json

import common as C


PROMPT_SCHEMA = {
    "chunk_id": "...",
    "pages": ["..."],
    "section_type": "...",
    "claims_about_1510": [
        {"claim": "...", "evidence": "...", "page_ref": "...",
         "confidence": "high|medium|low"}],
    "variant_observations": [
        {"book_1533": "...", "chapter_1533": "...", "variant_type": "...",
         "summary": "...", "page_ref": "...", "confidence": "high|medium|low"}],
    "themes": [
        {"theme": "...", "summary": "...", "evidence_ref": "...",
         "confidence": "high|medium|low"}],
    "uncertainties": ["..."],
}

PROMPT_INSTRUCTIONS = (
    "You are extracting structured scholarly metadata about the 1510 Wuerzburg "
    "draft of Agrippa's De occulta philosophia from Perrone Compagni's edition. "
    "Read the supplied chunk. Output ONLY valid JSON matching the schema. "
    "PARAPHRASE; do NOT reproduce continuous edition text. Keep any quoted "
    "lemma under ~10 words and only when needed for verification. Preserve "
    "page references. Prefer 'uncertain' over inventing confident claims."
)


def priority_for(section_type: str, text: str) -> int:
    score = 0
    if "comparison" in section_type:
        score += 5
    if "apparatus" in section_type:
        score += 3
    if section_type == "introduction":
        score += 3
    if "1510" in text:
        score += 4
    if C.WUERZBURG_ANCHOR_RE.search(text):
        score += 4
    return score


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-chars", type=int, default=6000)
    args = ap.parse_args()
    C.ensure_dirs()

    if not (C.PAGES_JSONL.exists() and C.EDITION_STRUCTURE.exists()):
        C.log("Need pages.jsonl and edition_structure.json (run Phases 2-3).")
        return

    structure = json.loads(C.EDITION_STRUCTURE.read_text(encoding="utf-8"))
    sec_by_page = {u["page_number"]: u["section_type"]
                   for u in structure.get("units", [])}
    pages = {r["page_number"]: r.get("text", "")
             for r in C.read_jsonl(C.PAGES_JSONL)}

    chunks = []
    for page_no in sorted(pages):
        text = pages[page_no]
        section_type = sec_by_page.get(page_no, "unknown")
        prio = priority_for(section_type, text)
        # One chunk per page for the scaffold; merge adjacent chapter+apparatus
        # pages in a later refinement.
        chunk = {
            "chunk_id": f"p{page_no:04d}",
            "pages": [page_no],
            "section_type": section_type,
            "priority": prio,
            "instructions": PROMPT_INSTRUCTIONS,
            "output_schema": PROMPT_SCHEMA,
            "text": text[:args.max_chars],
        }
        chunks.append(chunk)

    chunks.sort(key=lambda c: c["priority"], reverse=True)
    index = [{"chunk_id": c["chunk_id"], "pages": c["pages"],
              "section_type": c["section_type"], "priority": c["priority"]}
             for c in chunks]

    for c in chunks:
        (C.CHUNKS / f"{c['chunk_id']}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
    C.write_json(C.CHUNKS / "_index.json", index)
    top = [c["chunk_id"] for c in chunks[:20]]
    C.log(f"Wrote {len(chunks)} chunks. Top-priority: {top}")


if __name__ == "__main__":
    main()
