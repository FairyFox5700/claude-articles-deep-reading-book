"""Refresh index.html's embedded dataset from the structured JSON."""
from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "claude_articles_deep_summaries.json"
HTML_PATH = ROOT / "index.html"

CHAPTERS = [
    "Foundations & prompting",
    "Agents & tool use",
    "Claude Code & software engineering",
    "Platform, APIs & infrastructure",
    "Enterprise adoption & operations",
    "Security, safety & governance",
    "Product updates & models",
    "Customer stories & domain use cases",
    "Productivity, education & creative work",
    "Partnerships & ecosystem",
]
DESCRIPTIONS = {
    "Foundations & prompting": "Intent, context, prompting, and the basic mental models for productive work with Claude.",
    "Agents & tool use": "Planning, tool use, memory, context management, automation, and recovery in agentic systems.",
    "Claude Code & software engineering": "Coding, review, testing, migrations, source control, and agent-assisted engineering workflows.",
    "Platform, APIs & infrastructure": "APIs, SDKs, deployment, performance, cost, observability, and production architecture.",
    "Enterprise adoption & operations": "Organizational rollout, workflow redesign, change management, measurement, and scaled operations.",
    "Security, safety & governance": "Permissions, safeguards, evaluations, monitoring, and accountable human oversight.",
    "Product updates & models": "Model and product changes, capability boundaries, availability, and intended uses.",
    "Customer stories & domain use cases": "Implementations across industries and the operating decisions behind reported outcomes.",
    "Productivity, education & creative work": "Research, writing, analysis, learning, design, and creative production workflows.",
    "Partnerships & ecosystem": "Cloud, technology, consulting, and distribution partnerships that extend Claude.",
}
BOOT_RE = re.compile(
    r"const BOOK_DATA=(.*?);const BOOK_META=(.*?);</script><script>", re.S
)


def main() -> None:
    records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if [r["id"] for r in records] != list(range(1, len(records) + 1)):
        raise ValueError("IDs must be contiguous and ordered")
    counts = Counter(r["chapter"] for r in records)
    meta = {
        "chapters": [
            {"name": c, "description": DESCRIPTIONS[c], "count": counts[c]}
            for c in CHAPTERS
        ],
        "years": sorted({r["year"] for r in records}, reverse=True),
        "total_words": sum(r["deep_word_count"] for r in records),
        "median_words": int(statistics.median(r["deep_word_count"] for r in records)),
        "starter": [next(r["id"] for r in records if r["chapter"] == c) for c in CHAPTERS[:8]],
    }
    html = HTML_PATH.read_text(encoding="utf-8")
    replacement = (
        "const BOOK_DATA="
        + json.dumps(records, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        + ";const BOOK_META="
        + json.dumps(meta, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        + ";</script><script>"
    )
    updated, count = BOOT_RE.subn(lambda _: replacement, html, count=1)
    if count != 1:
        raise RuntimeError("Could not locate the embedded BOOK_DATA/BOOK_META block")
    HTML_PATH.write_text(updated, encoding="utf-8")
    print(f"Embedded {len(records)} records ({meta['total_words']:,} words) into {HTML_PATH.name}")


if __name__ == "__main__":
    main()
