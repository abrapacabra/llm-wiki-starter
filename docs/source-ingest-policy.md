---
title: Source Ingest Policy
artifact_type: source-ingest-policy
status: active
last_reviewed: 2026-05-20
---

# Source Ingest Policy

This policy controls how sources enter the wiki. Its goal is to keep source use useful, traceable, and scoped without turning the repository into a bulk copy of source material.

This is an operational policy, not legal advice. When uncertain, use the stricter ingest mode, mark the artifact `needs-review`, and ask the integration owner before expanding extraction.

## Governing Rules

- Keep heavyweight originals outside normal Git unless a separate control decision says otherwise.
- Keep raw capture, parser output, summaries, knowledge notes, decisions, and reviews separate.
- Cite source support with source ID plus page or chunk ID when derivatives exist.
- Commit only the smallest derivative set needed for the workflow.
- Do not bulk reproduce restricted or access-controlled material.

## Ingest Modes

| Mode | Use when | Commit behavior | Controls |
| --- | --- | --- | --- |
| `full-local-index` | Broad local search is useful and the source is allowed for broad derivation. | May create page files, chunks, tables, figure metadata, manifests, and quality reports under `raw/derived/<source-id>/`. | Requires explicit source choice, stable source ID, registry review, and `--large-source` for heavyweight PDFs. |
| `selective-page-range` | A large source is needed for a focused note, source map, review, or decision. | Commit only derivatives for selected pages or sections, plus manifest and quality report. | Use `--page-range`; avoid `--overwrite` unless replacing that derivative intentionally. |
| `summary-only` | The repo needs high-level takeaways but broad derivatives should not be committed. | Commit a concise source summary or source-linked note, not page/chunk dumps. | Use paraphrase, selected references, source ID, and uncertainty markers. |
| `restricted-pointer-only` | A source must be known to the system but should not have committed derivatives. | Commit only source identity, location pointer, and control metadata. | Use for sensitive, access-controlled, uncertain-license, or not-yet-reviewed material. |

## Source Tiers

| Tier | Meaning |
| --- | --- |
| `primary` | Direct authority for the domain or project. |
| `secondary` | Strong supporting source. |
| `reference` | Useful lookup source. |
| `background` | Context only. |
| `restricted` | Known to the repo but not copied or broadly derived. |

## Source Lanes

The first implemented lane is Docling-backed PDF decomposition:

```bash
uv run --group pdf python tools/source-ingest/pdf/ingest_pdf.py \
  --pdf "/path/to/source.pdf" \
  --source-id "source-slug" \
  --source-tier reference \
  --title "Source Title" \
  --page-range 1-20 \
  --max-chars 2200
```

The PDF lane enables Docling OCR, table structure extraction, page previews, and picture extraction by default. Use `--no-ocr`, `--no-render-pages`, and `--no-extract-figures` for faster scoped runs when those outputs are unnecessary.

Roadmap lanes may later cover web pages, document files, transcripts, and structured datasets. Add those lanes only when they have clear source identity, derivative output, and registry rules.

## Agent Decision Checklist

Before ingesting or using a source, answer:

1. What source type is this?
2. Which ingest mode applies?
3. What exact note, review, decision, issue, or workstream requires it?
4. What is the smallest page range, summary, or pointer that satisfies the task?
5. Are registry, index, runbook, tool README, and log updates required?

If the answer is unclear, choose `restricted-pointer-only` or `summary-only` until the owner approves broader ingest.
