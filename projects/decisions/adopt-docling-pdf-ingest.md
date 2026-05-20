---
artifact_type: decision
status: active
title: "Adopt Docling for PDF ingest"
owner: agents
linked_artifacts:
  - ../../tools/source-ingest/pdf/README.md
  - ../../docs/source-ingest-policy.md
sources: []
updated: 2026-05-20
---

# Adopt Docling for PDF Ingest

## Context

The starter had a handwritten PyMuPDF-based PDF lane for text extraction, page maps, chunks, figure metadata, and placeholder table output. That kept dependencies small but duplicated document parsing work that a maintained document toolkit already handles better.

## Decision

Use Docling as the PDF ingest parser backbone while preserving the existing CLI and `raw/derived/<source-id>/` output contract.

## Rationale

- Docling provides structured document conversion, Markdown/JSON export, table extraction, images, OCR controls, and native chunking.
- Keeping Docling in the uv `pdf` dependency group avoids making ordinary validation and wiki search install the document stack.
- Preserving the output contract lets existing wiki workflows keep using `manifest.yaml`, source maps, page files, chunks, tables, and figures.

## Consequences

- PDF ingest is heavier than the previous PyMuPDF-only lane, especially with rich defaults.
- Users can opt out of OCR, page rendering, or figure extraction for faster scoped runs.
- Broader document formats remain deferred until a future source lane defines routing and registry rules.
