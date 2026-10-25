"""Verify coverage, schema, embedded data, CSV, and manifest hashes."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"
JSON_PATH = ROOT / "data" / "claude_articles_deep_summaries.json"
CSV_PATH = ROOT / "data" / "claude_articles_deep_index.csv"
MANIFEST = ROOT / "manifest.json"
BOOT_RE = re.compile(r"const BOOK_DATA=(.*?);const BOOK_META=(.*?);</script><script>", re.S)
REQUIRED = {
    "id", "title", "url", "date", "category", "chapter", "source_tags", "products",
    "overview", "section_digest", "core_concepts", "evidence_and_examples",
    "practical_playbook", "limitations_and_cautions", "glossary", "bottom_line",
    "year", "deep_word_count", "canonical_key",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    records = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    assert len(records) == 293
    assert [r["id"] for r in records] == list(range(1, 294))
    assert len({r["id"] for r in records}) == 293
    assert len({r["canonical_key"] for r in records}) == 292
    assert sum(r["deep_word_count"] for r in records) == 318_567
    for r in records:
        assert REQUIRED <= r.keys(), (r.get("id"), REQUIRED - r.keys())
        assert r["url"].startswith("https://")
        assert 4 <= len(r["section_digest"]) <= 10
        assert 4 <= len(r["core_concepts"]) <= 8
        assert 2 <= len(r["evidence_and_examples"]) <= 6
        assert 3 <= len(r["practical_playbook"]) <= 8
        assert 2 <= len(r["limitations_and_cautions"]) <= 5
        assert 2 <= len(r["glossary"]) <= 8

    html = HTML.read_text(encoding="utf-8")
    assert "C:\\Users\\" not in html
    match = BOOT_RE.search(html)
    assert match, "Embedded dataset not found"
    embedded = json.loads(match.group(1))
    meta = json.loads(match.group(2))
    assert embedded == records
    assert sum(c["count"] for c in meta["chapters"]) == 293
    assert meta["total_words"] == 318_567
    assert len(meta["starter"]) == 8

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == 293
    assert [int(r["id"]) for r in csv_rows] == list(range(1, 294))

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["catalog_listings"] == 293
    assert manifest["unique_source_urls"] == 292
    assert manifest["total_summary_words"] == 318_567
    for rel, info in manifest["files"].items():
        path = ROOT / rel
        assert path.exists(), rel
        assert path.stat().st_size == info["bytes"], rel
        assert sha256(path) == info["sha256"], rel

    print("PASS: 293 listings, 292 unique URLs, 318,567 words, embedded data and hashes verified")


if __name__ == "__main__":
    main()
