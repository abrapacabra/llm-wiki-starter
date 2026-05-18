---
artifact_type: workstream
status: active
title: "Wiki Starter Hardening"
owner: "agents"
start_date: 2026-05-18
target_date: 2026-05-29
linked_artifacts:
  - ../milestones/wiki-foundation.md
  - ../milestones/wiki-scale-readiness.md
  - ../milestones/wiki-publishing-readiness.md
---

# Wiki Starter Hardening

## Outcome

The starter repo has a visible sprint structure for the open hardening work, with foundation, search, health-lint, and publishing-readiness workflows in place.

## Scope

- In: GitHub labels, GitHub milestones, issue milestone assignment, issue labels, local milestone pages, this workstream, M1 foundation implementation, M2 scale-readiness implementation, and M3 publishing-readiness trail maintenance.
- Out: follow-up issue execution beyond the starter hardening milestone set.

## Active Tasks

| Wave | Agent | Issue | Milestone | Status | Coordination Notes |
| --- | --- | --- | --- | --- | --- |
| Sprint 0 | Coordinator | [Sprint setup](https://github.com/abrapacabra/llm-wiki-starter/issues) | M1 / M2 | complete | Labels, milestones, assignments, and local planning trail are in place. |
| Wave A | Agent A | [#6 Wire validate_repo.py into GitHub Actions](https://github.com/abrapacabra/llm-wiki-starter/issues/6) | [M1 Wiki Foundation](../milestones/wiki-foundation.md) | complete | CI validation workflow added. |
| Wave A | Agent B | [#1 Add Obsidian-native wiki conventions](https://github.com/abrapacabra/llm-wiki-starter/issues/1) | [M1 Wiki Foundation](../milestones/wiki-foundation.md) | complete | Obsidian conventions and template metadata added. |
| Wave B | Agent C | [#2 Define query-to-durable-artifact workflow](https://github.com/abrapacabra/llm-wiki-starter/issues/2) | [M1 Wiki Foundation](../milestones/wiki-foundation.md) | complete | Query workflow and synthesis template added. |
| Wave B | Agent D | [#5 Register Karpathy LLM Wiki pattern](https://github.com/abrapacabra/llm-wiki-starter/issues/5) | [M1 Wiki Foundation](../milestones/wiki-foundation.md) | complete | Source registry entry, source summary, and knowledge note added. |
| Sprint 2 | Agent E | [#4 Add local wiki search lane for scale](https://github.com/abrapacabra/llm-wiki-starter/issues/4) | [M2 Scale Readiness](../milestones/wiki-scale-readiness.md) | complete | Search workflow and stdlib CLI added. |
| Sprint 2 | Agent F | [#3 Add wiki health lint workflow](https://github.com/abrapacabra/llm-wiki-starter/issues/3) | [M2 Scale Readiness](../milestones/wiki-scale-readiness.md) | complete | Health lint workflow, issue template, review format, and non-blocking validator report added. |
| Sprint 3 | Agents A-F | [#8-#13 M3 Publishing Readiness](https://github.com/abrapacabra/llm-wiki-starter/milestone/3) | [M3 Publishing Readiness](../milestones/wiki-publishing-readiness.md) | complete | Public landing page, CI test enforcement, MIT license, tooling tests, source credibility wording, and PR packaging are in place. |

## Source Inputs

- GitHub issue queue for `abrapacabra/llm-wiki-starter`.
- Local workflow rules in [agent runbook](../../docs/agent-runbook.md) and [workflow](../../docs/workflow.md).

## Reviews

- Each issue PR should include the validation command output.
- Coordinator should check `meta/index.md` and `meta/log.md` conflicts between parallel agents before merge.
- Coordinator reconciles navigation and maintenance-log updates before PR handoff.

## Closeout

- Result:
- Follow-up:
