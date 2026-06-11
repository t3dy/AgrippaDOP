#!/usr/bin/env python3
"""
Phase 6 — Build the passage database.

Creates db/agrippa_1510.sqlite with the full schema and loads whatever
deterministic artefacts already exist (edition pages, comparison map,
apparatus entries). The passage_assessments / themes tables are seeded with the
controlled vocabularies; rows are populated during Phases 7-8 review.

This script is idempotent: it creates tables IF NOT EXISTS and upserts.

Usage:
    python scripts/06_build_passage_database.py
"""

from __future__ import annotations

import json
import sqlite3

import common as C


SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    source_name TEXT,
    bibliographic_info TEXT,
    notes TEXT
);
CREATE TABLE IF NOT EXISTS edition_pages (
    id INTEGER PRIMARY KEY,
    page_number INTEGER UNIQUE,
    section_type TEXT,
    text_path TEXT,
    extraction_quality TEXT
);
CREATE TABLE IF NOT EXISTS comparison_map (
    id INTEGER PRIMARY KEY,
    ms_1510_locus TEXT,
    book_1533 TEXT,
    chapter_1533 TEXT,
    title_or_incipit TEXT,
    perrone_page TEXT,
    notes TEXT,
    confidence REAL
);
CREATE TABLE IF NOT EXISTS apparatus_entries (
    id INTEGER PRIMARY KEY,
    page_number INTEGER,
    book_1533 TEXT,
    chapter_1533 TEXT,
    line_or_lemma TEXT,
    sigla TEXT,
    variant_type TEXT,
    variant_summary TEXT,
    raw_excerpt TEXT,
    confidence REAL
);
CREATE TABLE IF NOT EXISTS passage_assessments (
    id INTEGER PRIMARY KEY,
    book_1533 TEXT,
    chapter_1533 TEXT,
    status_1510 TEXT CHECK (status_1510 IN (
        'present_in_1510','absent_from_1510','partly_present',
        'substantially_revised','uncertain')),
    evidence_type TEXT CHECK (evidence_type IN (
        'table_of_comparison','apparatus','introduction',
        'direct_textual_comparison','inferred')),
    evidence_refs TEXT,
    summary TEXT,
    confidence REAL
);
CREATE TABLE IF NOT EXISTS themes (
    id INTEGER PRIMARY KEY,
    theme_name TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS passage_themes (
    passage_assessment_id INTEGER,
    theme_id INTEGER,
    evidence_note TEXT,
    FOREIGN KEY (passage_assessment_id) REFERENCES passage_assessments(id),
    FOREIGN KEY (theme_id) REFERENCES themes(id)
);
"""

# Controlled theme vocabulary (Phase 8).
THEMES = [
    "natural_magic", "celestial_magic", "ceremonial_magic", "angelology",
    "demonology", "cabala", "hebrew_material", "divine_names",
    "images_and_talismans", "astrology", "alchemy", "medicine",
    "number_symbolism", "music", "optics", "virtues_of_things",
    "spiritus_mundi", "neoplatonism", "hermeticism", "ficino", "pico",
    "pseudo_dionysius", "trithemius_context", "lullism", "scholastic_sources",
    "patristic_sources", "biblical_exegesis", "uncertain",
]


def load_edition_pages(con: sqlite3.Connection) -> int:
    if not C.PAGES_JSONL.exists():
        return 0
    structure = {}
    if C.EDITION_STRUCTURE.exists():
        data = json.loads(C.EDITION_STRUCTURE.read_text(encoding="utf-8"))
        for u in data.get("units", []):
            structure[u["page_number"]] = u.get("section_type")
    n = 0
    for rec in C.read_jsonl(C.PAGES_JSONL):
        con.execute(
            "INSERT OR REPLACE INTO edition_pages "
            "(page_number, section_type, text_path, extraction_quality) "
            "VALUES (?,?,?,?)",
            (rec["page_number"],
             structure.get(rec["page_number"]),
             str(C.PAGES_JSONL.relative_to(C.PROJECT_ROOT)),
             rec.get("extraction_quality")))
        n += 1
    return n


def load_comparison_map(con: sqlite3.Connection) -> int:
    path = C.TABLES / "table_of_comparison.json"
    if not path.exists():
        return 0
    rows = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for r in rows:
        con.execute(
            "INSERT INTO comparison_map "
            "(ms_1510_locus, book_1533, chapter_1533, title_or_incipit, "
            " perrone_page, notes, confidence) VALUES (?,?,?,?,?,?,?)",
            (r.get("ms_1510_locus"), r.get("book_1533"), r.get("chapter_1533"),
             r.get("title_or_incipit"), r.get("perrone_page"),
             r.get("notes"), r.get("confidence")))
        n += 1
    return n


def load_apparatus(con: sqlite3.Connection) -> int:
    path = C.TABLES / "wurzburg_apparatus_entries.json"
    if not path.exists():
        return 0
    rows = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for r in rows:
        con.execute(
            "INSERT INTO apparatus_entries "
            "(page_number, book_1533, chapter_1533, line_or_lemma, sigla, "
            " variant_type, variant_summary, raw_excerpt, confidence) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (r.get("page_number"), r.get("book_1533"), r.get("chapter_1533"),
             r.get("line_or_lemma"), r.get("sigla"), r.get("variant_type"),
             r.get("variant_summary"), r.get("raw_excerpt"),
             r.get("confidence")))
        n += 1
    return n


def main() -> None:
    C.ensure_dirs()
    con = sqlite3.connect(C.DB_PATH)
    con.executescript(SCHEMA)

    for t in THEMES:
        con.execute("INSERT OR IGNORE INTO themes (theme_name) VALUES (?)", (t,))

    # Reload deterministic tables fresh (clear then load) so reruns are clean.
    con.execute("DELETE FROM edition_pages")
    con.execute("DELETE FROM comparison_map")
    con.execute("DELETE FROM apparatus_entries")
    p = load_edition_pages(con)
    c = load_comparison_map(con)
    a = load_apparatus(con)

    con.execute(
        "INSERT OR IGNORE INTO sources (source_name, bibliographic_info, notes) "
        "VALUES (?,?,?)",
        ("Perrone Compagni edition",
         "V. Perrone Compagni (ed.), Cornelius Agrippa, De occulta philosophia "
         "libri tres (Brill, Studies in the History of Christian Thought).",
         "Primary edition under analysis; local copyrighted source."))
    con.commit()
    con.close()
    C.log(f"DB built at {C.DB_PATH}: pages={p}, comparison={c}, apparatus={a}, "
          f"themes={len(THEMES)}")


if __name__ == "__main__":
    main()
