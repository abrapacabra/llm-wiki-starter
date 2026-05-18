# LLM Wiki Starter

A public starter for an agent-maintained Markdown wiki. It gives humans and LLM agents a shared, inspectable workspace for source intake, source decomposition, durable knowledge notes, reviews, decisions, and project coordination.

The starter is intentionally generic: bring your own domain, keep source material separate from synthesis, and leave a trace that future agents can validate.

## Quickstart

1. Read the [agent entry point](AGENTS.md), then the [agent runbook](docs/agent-runbook.md).
2. Check the current navigation surfaces: [wiki index](meta/index.md), [source registry](meta/source-registry.md), and any active [workstreams](projects/workstreams/README.md).
3. Add sources only through the documented [source ingest policy](docs/source-ingest-policy.md).
4. Write durable notes, reviews, decisions, and workstream updates from the matching [templates](docs/templates/).
5. Run validation before handoff:

```bash
python3 tools/validate_repo.py
```

## What This Starter Gives You

- A small Markdown knowledge base layout with clear boundaries between `raw/`, `knowledge/`, `reviews/`, `projects/`, `docs/`, and `meta/`.
- An agent workflow that starts from a visible workstream or issue and ends with traceable validation.
- A source registry, source tiers, and ingest rules for keeping evidence explicit.
- Templates for knowledge notes, source summaries, reviews, decisions, query synthesis, workstreams, and agent tasks.
- Local validation for required frontmatter, registered source references, and relative Markdown links.
- Optional search and wiki health review lanes for when the wiki grows beyond index-first navigation.

## Common Workflows

- Agent handoff: follow the [agent runbook](docs/agent-runbook.md) and [workflow](docs/workflow.md), then report changed files, verification, uncertainty, and next action.
- Source intake: use the [source ingest policy](docs/source-ingest-policy.md), register reusable sources in [source registry](meta/source-registry.md), and keep heavyweight originals out of normal Git.
- Query promotion: use the [query workflow](docs/query-workflow.md) to decide whether a useful answer should stay ephemeral or become a durable artifact.
- Local search: start with [wiki index](meta/index.md), then use the [search workflow](docs/search.md) and `tools/search_wiki.py` when navigation is not enough.
- Wiki health review: run structural validation first, then use [wiki health lint](docs/wiki-health-lint.md) for advisory review signals.

## Validation

Run the repository validator and tests before handing off changes:

```bash
python3 tools/validate_repo.py
python3 -m unittest discover -s tests -v
```

For advisory wiki health signals:

```bash
python3 tools/validate_repo.py --health-report
```

For a quick search smoke test:

```bash
python3 tools/search_wiki.py wiki health --limit 5
```

The validator checks structural rules only. Factual claims, source disagreement, stale notes, and review quality still require human or agent inspection.

## Repository Shape

```text
AGENTS.md                  Agent entry point and cold-start rules
README.md                  Public landing page
LICENSE                    Project license
docs/                      Runbooks, workflows, policies, and templates
meta/                      Index, source registry, and maintenance log
raw/                       Source pointers, external originals, and derivatives
knowledge/                 Durable source-supported notes
reviews/                   Validation and critique artifacts
projects/                  Workstreams, milestones, and project coordination
tools/                     Validation, search, and source-ingest utilities
tests/                     Test coverage for local tooling
```

## License

This project is licensed under the [MIT License](LICENSE).
