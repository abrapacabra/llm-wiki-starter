# PDF Source Ingest

The PDF lane uses Docling to create navigation and search artifacts from a local PDF while keeping source originals separate from durable wiki notes.

Run from the repository root:

```bash
uv run --group pdf python tools/source-ingest/pdf/ingest_pdf.py --pdf <path> --source-id <id> --source-tier reference --title <title>
```

Docling OCR, table structure extraction, page previews, and picture extraction are enabled by default. Use `--no-ocr`, `--no-render-pages`, or `--no-extract-figures` when a faster or lighter run is enough.

Outputs are written to `raw/derived/<source-id>/` by default:

- `manifest.yaml`
- `quality-report.md`
- `source-summary.md`
- `source-maps/outline.md`
- `sections.jsonl`
- `chunks.jsonl`
- `pages/`
- `tables/`
- `figures/`

For a local smoke run against a small PDF:

```bash
uv run --group pdf python tools/source-ingest/pdf/ingest_pdf.py \
  --pdf <small.pdf> \
  --source-id smoke-test \
  --source-tier reference \
  --title "Smoke Test" \
  --output-root tmp/derived \
  --overwrite
```

Use source maps and summaries for navigation. Promote source material into knowledge notes only through a scoped workstream, review, or decision.
