---
artifact_type: log
status: active
owner: agents
updated: 2026-05-20
---

# Maintenance Log

## 2026-05-20

- Replaced the PDF ingest parser internals with Docling while preserving the derived-source output contract; added mocked ingest tests and recorded the Docling adoption decision.
- Added uv project metadata, moved PDF ingest dependency management into a uv dependency group, and updated validation/source-ingest commands plus CI to run through uv.

## 2026-05-18

- Hardened the publishing-readiness GitHub Actions workflow with explicit read permissions, manual dispatch, and `python`/`python3` fallback commands after startup-only check failures.
- Completed M3 publishing-readiness polish for PR #7: public README, MIT license, CI test enforcement, CLI and health-report tests, source credibility wording, and local milestone trail.
- Completed M2 scale-readiness artifacts: local wiki search workflow and CLI, wiki health lint workflow, health-check issue/review templates, and non-blocking validator health report.
- Completed M1 foundation artifacts: CI validation workflow, Obsidian conventions, query-to-artifact workflow, and Karpathy LLM Wiki pattern source summary and knowledge note.
- Added wiki starter hardening workstream and milestone artifacts for the open GitHub issue sprint plan; updated validator artifact types for milestone pages.
- Created the blank LLM wiki starter scaffold with generic source intake, control files, and agent runbooks.
