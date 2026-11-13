# Claude Articles Deep-Reading Book

A self-contained, interactive study guide for the complete [Claude articles catalog](https://claude.com/resources/articles).

## What is included

- **293 catalog listings** representing **292 unique source URLs**
- **318,567 words** of source-grounded summaries
- A median depth of **1,192 words per article**
- Comprehensive overviews
- Section-by-section digests following each source article's structure
- Core concepts and why they matter
- Specific evidence, examples, implementation playbooks, cautions, and glossaries
- Search, chapter/year/progress filters, full-detail and overview-only modes
- Built-in browser voice narration for every lesson, with pause, stop, and speed controls
- Browser-local reading progress, responsive layouts, dark mode, and print support

## Read online

After GitHub Pages deployment, the book is available at:

**https://fairyfox5700.github.io/claude-articles-deep-reading-book/**

The site has no backend, analytics, account requirement, or external runtime dependency. Open `index.html` directly to use it offline.

## Repository contents

- `index.html` — complete standalone interactive book with embedded dataset
- `data/claude_articles_deep_summaries.json` — lossless structured summaries
- `data/claude_articles_deep_index.csv` — auditable article index
- `manifest.json` — counts, file sizes, and SHA-256 checksums
- `scripts/build_index.py` — refreshes the embedded dataset from the structured JSON
- `scripts/validate.py` — verifies schema, coverage, embedded data, and checksums

## Method and scope

The collection was enumerated from Claude's public resources API. Every unique source page was retrieved successfully. Summaries were produced from extracted full article bodies—not landing-page previews—and preserve the source title, date, category, and canonical link.

The repository intentionally excludes fetched article bodies, intermediate batches, browser profiles, and processing logs. It publishes only derived summaries, source links, the interactive reader, and audit metadata.

Two catalog records point to the same canonical article, so the book preserves 293 catalog entries while reporting 292 unique source URLs.

## Validate locally

Requires Python 3.10+ and no third-party packages:

```bash
python scripts/validate.py
```

To regenerate the HTML's embedded dataset after editing the JSON:

```bash
python scripts/build_index.py
python scripts/update_manifest.py
python scripts/validate.py
```

## Limitations

This is a derived educational guide, not current product documentation. Product availability, pricing, model behavior, and recommended deployment practices may change after an article is published. Follow each lesson's **Open original** link and consult current Anthropic documentation before making implementation decisions.

## Attribution

Original articles, product names, and trademarks belong to Anthropic or their respective owners. Each lesson links to its source. This repository is not affiliated with or endorsed by Anthropic.

## License

The reader application and repository scripts are available under the MIT License. The license does not grant rights to the linked original articles, Anthropic trademarks, or third-party material.
