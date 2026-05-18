#!/usr/bin/env python3
"""Structural checks for the LLM wiki starter repository."""

from __future__ import annotations

import re
import sys
import argparse
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ALLOWED_ARTIFACT_TYPES = {
    "knowledge-note",
    "source-summary",
    "source-map",
    "source-registry",
    "index",
    "log",
    "milestone",
    "workstream",
    "review",
    "decision",
    "agent-task",
    "source-ingest-policy",
}

ALLOWED_STATUSES = {
    "draft",
    "active",
    "needs-review",
    "verified",
    "conflicted",
    "deprecated",
}

ALLOWED_SOURCE_TIERS = {
    "primary",
    "secondary",
    "reference",
    "background",
    "restricted",
}

LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
CODE_SPAN_RE = re.compile(r"(`+).*?\1", re.DOTALL)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if ".git" not in path.parts
    )


def split_frontmatter(text: str) -> tuple[dict[str, object], int] | tuple[None, int]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, 0
    for end_index in range(1, len(lines)):
        if lines[end_index].strip() == "---":
            return parse_frontmatter(lines[1:end_index]), end_index + 1
    return {}, len(lines)


def parse_frontmatter(lines: list[str]) -> dict[str, object]:
    data: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in lines:
        if not raw_line.strip():
            continue
        if raw_line.startswith("  - ") and current_key:
            value = raw_line[4:].strip()
            current = data.setdefault(current_key, [])
            if isinstance(current, list):
                current.append(clean_scalar(value))
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "[]":
            data[key] = []
        elif value:
            data[key] = clean_scalar(value)
        else:
            data[key] = []
    return data


def clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def should_require_frontmatter(path: Path) -> bool:
    if path.name == "README.md":
        return False
    if ".github" in path.parts:
        return False
    if "templates" in path.parts:
        return False
    rel_path = rel(path)
    return (
        rel_path.startswith("meta/")
        or rel_path.startswith("knowledge/")
        or rel_path.startswith("reviews/")
        or rel_path.startswith("projects/")
        or rel_path.startswith("raw/derived/")
        or rel_path == "docs/source-ingest-policy.md"
    )


def registered_sources() -> dict[str, dict[str, str]]:
    registry_path = ROOT / "meta" / "source-registry.md"
    if not registry_path.exists():
        return {}
    sources: dict[str, dict[str, str]] = {}
    for line in registry_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or cells[0] in {"Source ID", "---"} or set(cells[0]) == {"-"}:
            continue
        if len(cells) < 6:
            continue
        source_id, title, tier, status, derived_path, notes = cells[:6]
        if source_id and source_id != "-":
            sources[source_id] = {
                "title": title,
                "tier": tier,
                "status": status,
                "derived_path": derived_path,
                "notes": notes,
            }
    return sources


def source_values(frontmatter: dict[str, object]) -> list[str]:
    raw = frontmatter.get("sources")
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item).strip()]
    value = str(raw).strip()
    return [value] if value else []


def validate_frontmatter(errors: list[str], sources: dict[str, dict[str, str]]) -> None:
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        frontmatter, _ = split_frontmatter(text)
        if frontmatter is None:
            if should_require_frontmatter(path):
                errors.append(f"{rel(path)}: missing frontmatter")
            continue
        artifact_type = frontmatter.get("artifact_type")
        status = frontmatter.get("status")
        if artifact_type is not None and artifact_type not in ALLOWED_ARTIFACT_TYPES:
            errors.append(f"{rel(path)}: unknown artifact_type {artifact_type!r}")
        if status is not None and status not in ALLOWED_STATUSES:
            errors.append(f"{rel(path)}: unknown status {status!r}")
        source_tier = frontmatter.get("source_tier")
        if source_tier is not None and source_tier not in ALLOWED_SOURCE_TIERS:
            errors.append(f"{rel(path)}: unknown source_tier {source_tier!r}")
        if should_require_frontmatter(path):
            if artifact_type is None:
                errors.append(f"{rel(path)}: missing artifact_type")
            if status is None:
                errors.append(f"{rel(path)}: missing status")
        for source_id in source_values(frontmatter):
            if source_id not in sources:
                errors.append(f"{rel(path)}: source {source_id!r} is not registered")


def validate_registry(errors: list[str], sources: dict[str, dict[str, str]]) -> None:
    for source_id, row in sources.items():
        tier = row["tier"]
        status = row["status"]
        derived_path = row["derived_path"]
        if tier not in ALLOWED_SOURCE_TIERS:
            errors.append(f"meta/source-registry.md: source {source_id!r} has unknown tier {tier!r}")
        if status not in ALLOWED_STATUSES:
            errors.append(f"meta/source-registry.md: source {source_id!r} has unknown status {status!r}")
        if derived_path and derived_path != "-":
            target = (ROOT / derived_path).resolve()
            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"meta/source-registry.md: source {source_id!r} derived path leaves repository")
                continue
            if not target.exists():
                errors.append(f"meta/source-registry.md: source {source_id!r} derived path is missing: {derived_path}")


def validate_links(errors: list[str]) -> None:
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            href = match.group(1).strip()
            if should_skip_link(href):
                continue
            target_text = href.split("#", 1)[0]
            if not target_text:
                continue
            target = (path.parent / target_text).resolve()
            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"{rel(path)}: link leaves repository: {href}")
                continue
            if not target.exists():
                errors.append(f"{rel(path)}: broken link: {href}")


def linked_markdown_targets() -> set[str]:
    targets: set[str] = set()
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            href = match.group(1).strip()
            if should_skip_link(href):
                continue
            target_text = href.split("#", 1)[0]
            if not target_text:
                continue
            target = (path.parent / target_text).resolve()
            try:
                targets.add(rel(target))
            except ValueError:
                continue
    return targets


def title_values(path: Path, frontmatter: dict[str, object]) -> set[str]:
    values = {path.stem}
    title = frontmatter.get("title")
    if title:
        values.add(str(title).strip())
    aliases = frontmatter.get("aliases")
    if isinstance(aliases, list):
        values.update(str(alias).strip() for alias in aliases if str(alias).strip())
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            values.add(line[2:].strip())
            break
    return {value.casefold() for value in values if value}


def health_report(sources: dict[str, dict[str, str]]) -> str:
    frontmatter_by_path: dict[Path, dict[str, object]] = {}
    for path in markdown_files():
        frontmatter, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        if frontmatter:
            frontmatter_by_path[path] = frontmatter

    status_counts = Counter(
        str(frontmatter.get("status"))
        for frontmatter in frontmatter_by_path.values()
        if frontmatter.get("status")
    )
    unresolved = [
        f"{rel(path)} ({frontmatter.get('status')})"
        for path, frontmatter in frontmatter_by_path.items()
        if frontmatter.get("status") in {"needs-review", "conflicted"}
    ]

    linked_targets = linked_markdown_targets()
    orphan_candidates = [
        rel(path)
        for path, frontmatter in frontmatter_by_path.items()
        if is_health_artifact(path, frontmatter) and rel(path) not in linked_targets
    ]

    known_titles: set[str] = set()
    for path, frontmatter in frontmatter_by_path.items():
        known_titles.update(title_values(path, frontmatter))

    unresolved_wikilinks: set[str] = set()
    for path in markdown_files():
        text = strip_inline_code(path.read_text(encoding="utf-8"))
        for target in WIKILINK_RE.findall(text):
            if target.strip().casefold() not in known_titles:
                unresolved_wikilinks.add(f"{rel(path)} -> [[{target.strip()}]]")

    lines = [
        "",
        "Wiki health report",
        "==================",
        "Status counts:",
    ]
    if status_counts:
        lines.extend(f"- {status}: {count}" for status, count in sorted(status_counts.items()))
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Unresolved statuses:")
    lines.extend(format_report_items(unresolved))

    lines.append("")
    lines.append("Orphan candidates:")
    lines.extend(format_report_items(orphan_candidates))

    lines.append("")
    lines.append("Unresolved wikilinks:")
    lines.extend(format_report_items(sorted(unresolved_wikilinks)))

    lines.append("")
    lines.append("Registered sources:")
    lines.append(f"- {len(sources)}")
    return "\n".join(lines)


def is_health_artifact(path: Path, frontmatter: dict[str, object]) -> bool:
    artifact_type = frontmatter.get("artifact_type")
    if artifact_type in {"index", "log", "source-registry"}:
        return False
    rel_path = rel(path)
    return rel_path.startswith(("knowledge/", "reviews/", "projects/"))


def format_report_items(items: list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]


def strip_inline_code(text: str) -> str:
    return CODE_SPAN_RE.sub("", text)


def should_skip_link(href: str) -> bool:
    lowered = href.lower()
    return (
        lowered.startswith("http://")
        or lowered.startswith("https://")
        or lowered.startswith("mailto:")
        or lowered.startswith("#")
        or lowered.startswith("tel:")
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate structural wiki repository rules.")
    parser.add_argument(
        "--health-report",
        action="store_true",
        help="Print non-blocking wiki health signals after structural validation.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors: list[str] = []
    sources = registered_sources()
    validate_frontmatter(errors, sources)
    validate_registry(errors, sources)
    validate_links(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"\nRepository validation failed with {len(errors)} issue(s).")
        return 1
    print("Repository validation passed.")
    if args.health_report:
        print(health_report(sources))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
