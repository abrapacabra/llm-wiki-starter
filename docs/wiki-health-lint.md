# Wiki Health Lint

Wiki health lint is a periodic review pass for problems that structural validation cannot prove automatically.

## Mechanical Checks

Run the normal validator first:

```bash
uv run python tools/validate_repo.py
```

Then run the non-blocking health report:

```bash
uv run python tools/validate_repo.py --health-report
```

The health report is advisory in v1. It reports status counts, unresolved `needs-review` and `conflicted` artifacts, orphan candidates, unresolved wikilinks, and registered source count. It does not fail the build.

Use [search workflow](search.md) when investigating duplicates, missing concept pages, or stale claims.

## Manual Review Categories

A health check review should inspect:

- contradictory claims across notes,
- stale claims superseded by newer sources,
- unresolved `needs-review` or `conflicted` items,
- orphan pages with no meaningful inbound links,
- missing concept pages for important wikilinks,
- missing source support for factual claims,
- duplicated or overlapping notes.

## Review Output

Use [wiki health check review template](../reviews/wiki-health-check-template.md) for the review artifact. A completed health review should name the time period or scope, list mechanical report findings, separate semantic findings from mechanical findings, and turn follow-up work into issues or workstream tasks.

## Limits

Do not treat health lint as automated factual verification. Agents must inspect sources before changing factual claims, and unresolved source disagreement should remain `conflicted` until a higher-tier source resolves it.
