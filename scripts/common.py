"""
common.py — shared paths, configuration, and helpers for the Agrippa 1510
extraction pipeline.

This module centralises:
  * project paths (so every script writes to the same tree)
  * the configurable list of candidate sigla / spellings for the Wuerzburg MS
  * Unicode normalisation that preserves Latin / Greek / Hebrew / sigla
  * small logging + JSONL helpers

Nothing here is edition-specific in a way that hard-codes assumptions about
Perrone Compagni's text. Heuristic patterns live in the individual phase
scripts and are meant to be tuned *after* the real PDF has been inspected.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Iterator

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
# scripts/ -> project root is one level up.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA = PROJECT_ROOT / "data"
RAW = DATA / "raw"
OCR = DATA / "ocr"
CHUNKS = DATA / "chunks"
INDICES = DATA / "indices"

OUTPUTS = PROJECT_ROOT / "outputs"
TABLES = OUTPUTS / "tables"
REPORTS = OUTPUTS / "reports"
NOTES = OUTPUTS / "notes"

DB_DIR = PROJECT_ROOT / "db"
DB_PATH = DB_DIR / "agrippa_1510.sqlite"
LOGS = PROJECT_ROOT / "logs"

# Canonical artefacts produced by the pipeline.
PAGES_JSONL = OCR / "pages.jsonl"
FULL_TEXT = OCR / "full_text.txt"
EDITION_STRUCTURE = INDICES / "edition_structure.json"

ALL_DIRS = [RAW, OCR, CHUNKS, INDICES, TABLES, REPORTS, NOTES, DB_DIR, LOGS]


def ensure_dirs() -> None:
    for d in ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# Source PDF resolution
# --------------------------------------------------------------------------
# The real target is Perrone Compagni's Brill critical edition, which lives on
# the user's local E: drive. In this repo we keep PDFs in data/raw/. The
# resolver lets every script accept an explicit --pdf path, fall back to an
# env-style default, or auto-discover a single PDF in data/raw/.

def resolve_pdf(explicit: str | None = None) -> Path | None:
    """Return the PDF to operate on, or None if nothing usable is found."""
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.exists() else None
    candidates = sorted(RAW.glob("*.pdf"))
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        # Prefer something that looks like the De occulta edition.
        for c in candidates:
            name = c.name.lower()
            if "occulta" in name or "perrone" in name or "compagni" in name:
                return c
        return candidates[0]
    return None


# --------------------------------------------------------------------------
# Wuerzburg MS siglum candidates
# --------------------------------------------------------------------------
# IMPORTANT: we do NOT assume the siglum is "W". These are *candidate* cues
# used to discover the real siglum during inspection. The shelfmark and the
# Latinised place name are reliable anchors; the single-letter sigla are only
# weak hints to be confirmed against the edition's own sigla list.
WUERZBURG_SHELFMARK_PATTERNS = [
    r"M\.?\s*ch\.?\s*q\.?\s*50",      # M.ch.q.50 with optional dots/spaces
    r"Mch\s*q\s*50",
]
WUERZBURG_PLACE_PATTERNS = [
    r"W[üu]rzburg",
    r"Wirceburg\w*",                   # Wirceburgensis (Latin)
    r"Herbipol\w*",                    # Herbipolitanus (classical Latin name)
    r"Universit[äa]tsbibliothek",
]
# Weak single-token siglum hints; confirmed only via the sigla list.
WUERZBURG_SIGLUM_HINTS = [r"\bW\b"]

SIGLA_LIST_CUES = [
    r"sigla",
    r"conspectus siglorum",
    r"abbreviazioni",
    r"manoscritt",          # manoscritti / manoscritto (IT)
    r"manuscript",
    r"codic",               # codices / codice
    r"witness",
    r"testimoni",           # testimoni (IT)
]


def compile_any(patterns: Iterable[str], flags: int = re.IGNORECASE) -> re.Pattern:
    return re.compile("|".join(f"(?:{p})" for p in patterns), flags)


WUERZBURG_ANCHOR_RE = compile_any(
    WUERZBURG_SHELFMARK_PATTERNS + WUERZBURG_PLACE_PATTERNS
)
SIGLA_LIST_RE = compile_any(SIGLA_LIST_CUES)


# --------------------------------------------------------------------------
# Unicode normalisation
# --------------------------------------------------------------------------
def normalize_text(text: str) -> str:
    """NFC-normalise while preserving Latin/Greek/Hebrew, diacritics, sigla.

    We deliberately avoid aggressive cleaning. We only:
      * normalise to NFC (composed form) for consistent diacritics
      * collapse Windows/Mac line endings to \n
      * strip trailing spaces per line
      * drop zero-width / BOM characters that corrupt downstream regex
    Hebrew, Greek, and apparatus sigla (], †, *, etc.) are left intact.
    """
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = unicodedata.normalize("NFC", text)
    # Remove zero-width and BOM-style invisibles, keep everything else.
    text = re.sub(r"[​‌‍﻿]", "", text)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text


def script_histogram(text: str) -> dict[str, int]:
    """Count characters by writing system — useful for flagging Greek/Hebrew."""
    counts = {"latin": 0, "greek": 0, "hebrew": 0, "digit": 0, "other": 0}
    for ch in text:
        code = ord(ch)
        if ch.isdigit():
            counts["digit"] += 1
        elif 0x0590 <= code <= 0x05FF:
            counts["hebrew"] += 1
        elif (0x0370 <= code <= 0x03FF) or (0x1F00 <= code <= 0x1FFF):
            counts["greek"] += 1
        elif ch.isalpha():
            counts["latin"] += 1
        elif not ch.isspace():
            counts["other"] += 1
    return counts


# --------------------------------------------------------------------------
# Page records (the unit of data/ocr/pages.jsonl)
# --------------------------------------------------------------------------
@dataclass
class PageRecord:
    page_number: int            # 1-based PDF page index
    printed_number: str | None  # printed folio/page number if detected
    text: str
    char_count: int
    extraction_method: str      # "embedded" | "ocr" | "embedded+ocr" | "empty"
    extraction_quality: str     # "good" | "partial" | "poor" | "empty"
    scripts: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def write_jsonl(path: Path, records: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n


def read_jsonl(path: Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------
# Tiny logger
# --------------------------------------------------------------------------
def log(msg: str) -> None:
    print(f"[agrippa] {msg}", file=sys.stderr)


def require_fitz():
    try:
        import fitz  # noqa: F401  (PyMuPDF)
        return fitz
    except ImportError:
        log("PyMuPDF (pymupdf) is required. Install with: pip install pymupdf")
        raise
