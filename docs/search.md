# Search Workflow

The wiki is index-first while it is small. Use search only after checking the navigation surfaces that should already know about durable work.

## Search Order

1. Start with [wiki index](../meta/index.md).
2. Check the active workstream, relevant milestone, and [source registry](../meta/source-registry.md).
3. Search durable Markdown artifacts with `tools/search_wiki.py`.
4. Search `raw/derived/` only when doing source work that requires parser output.

Do not search `raw/external/` as a default workflow. Heavyweight originals and access-controlled material stay outside normal agent search unless a specific source task authorizes them.

## Local CLI

Use the stdlib search helper when the index is too small to answer a navigation question:

```bash
uv run python tools/search_wiki.py query workflow --limit 10
```

The search matches lines containing all query terms, case-insensitively by default. It searches durable Markdown and excludes `.git/`, virtual environments, caches, scratch folders, `raw/external/`, and `raw/derived/`.

For source work that needs committed parser derivatives:

```bash
uv run python tools/search_wiki.py source locator --include-derived --limit 20
```

`--include-derived` adds `raw/derived/` only. It still excludes `raw/external/`.

## Optional Upgrade Lane

External tools such as qmd, ripgrep wrappers, or vector search may be documented later. They should remain optional until a workstream proves the wiki has outgrown the stdlib helper and index-first workflow.

## Agent Rule

Search before creating a new durable artifact when there is a reasonable chance a related note, review, decision, source summary, or workstream entry already exists. If search finds overlapping material, update or link the existing artifact instead of creating a duplicate.
