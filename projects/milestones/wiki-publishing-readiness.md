---
artifact_type: milestone
status: verified
title: "M3 Publishing Readiness"
owner: "agents"
start_date: 2026-05-18
target_date: 2026-05-22
linked_artifacts:
  - ../workstreams/wiki-starter-hardening.md
  - ../../README.md
  - ../../LICENSE
  - ../../knowledge/llm-wiki-pattern.md
  - ../../knowledge/karpathy-llm-wiki-pattern-summary.md
---

# M3 Publishing Readiness

## Outcome

The wiki starter is ready for public-facing handoff with a clear landing page, enforced CI checks, an MIT license, tested local tooling, source credibility boundaries, and reviewer-ready PR packaging.

## Local Acceptance State

Status is `verified` after coordinator review and local validation. GitHub issues remain open until PR #7 merges.

## Tasks

| Lane | Artifact | Owner | Status | Acceptance Focus |
| --- | --- | --- | --- | --- |
| Public landing | [README](../../README.md) | Agent A | complete | Public quickstart, workflows, validation, repository shape, and license are visible. |
| CI enforcement | [Validate workflow](../../.github/workflows/validate.yml) | Agent B | complete | CI runs structural validation, unit tests, and advisory health report. |
| License | [MIT License](../../LICENSE) | Agent A | complete | Public reuse terms are explicit. |
| Tooling tests | [Search tests](../../tests/test_search_wiki.py) | Agent B | complete | Search CLI output and limit behavior are covered. |
| Health tests | [Health report tests](../../tests/test_validate_repo_health.py) | Agent B | complete | Health report behavior and inline-code wikilink handling are covered. |
| Source credibility | [LLM Wiki Pattern](../../knowledge/llm-wiki-pattern.md) | Agent C | complete | Public-facing wording frames the note as design memory, not authoritative source reproduction. |
| Source credibility | [Karpathy LLM Wiki Pattern Source Summary](../../knowledge/karpathy-llm-wiki-pattern-summary.md) | Agent C | complete | Summary-only limits and authority limits are explicit. |
| Milestone trail | [Wiki Starter Hardening](../workstreams/wiki-starter-hardening.md) | Coordinator | complete | M3 publishing readiness is linked from the active workstream and index. |

## Coordination

- Preserve `needs-review` on source-derived artifacts until the authoritative source text is checked.
- Keep source material, summary-only interpretation, and synthesized knowledge separate.
- Track GitHub sprint work in issues [#8](https://github.com/abrapacabra/llm-wiki-starter/issues/8), [#9](https://github.com/abrapacabra/llm-wiki-starter/issues/9), [#10](https://github.com/abrapacabra/llm-wiki-starter/issues/10), [#11](https://github.com/abrapacabra/llm-wiki-starter/issues/11), [#12](https://github.com/abrapacabra/llm-wiki-starter/issues/12), and [#13](https://github.com/abrapacabra/llm-wiki-starter/issues/13).

## Validation

- `python3 -m unittest discover -s tests -v`
- `python3 tools/validate_repo.py`
- `python3 tools/validate_repo.py --health-report`
- `python3 tools/search_wiki.py wiki health --limit 5`
- `git diff --check`
