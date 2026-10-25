"""Regenerate manifest.json for publishable repository files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "index.html",
    "README.md",
    "LICENSE",
    ".gitignore",
    "data/claude_articles_deep_summaries.json",
    "data/claude_articles_deep_index.csv",
    "scripts/build_index.py",
    "scripts/validate.py",
    "scripts/update_manifest.py",
]


def main() -> None:
    manifest = {
        "title": "The Claude Articles Deep-Reading Book",
        "source": "https://claude.com/resources/articles",
        "catalog_listings": 293,
        "unique_source_urls": 292,
        "total_summary_words": 318_567,
        "median_words_per_article": 1_192,
        "files": {},
    }
    for rel in FILES:
        path = ROOT / rel
        data = path.read_bytes()
        manifest["files"][rel] = {
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    (ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote manifest for {len(FILES)} files")


if __name__ == "__main__":
    main()
