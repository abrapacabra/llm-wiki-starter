#!/usr/bin/env python3
"""Search durable Markdown wiki artifacts without touching heavy source originals."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {
    ".git",
    ".cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "scratch",
    "tmp",
    "venv",
}

TOP_LEVEL_SEARCH_DIRS = {"docs", "knowledge", "meta", "projects", "raw", "reviews"}


@dataclass(frozen=True)
class SearchOptions:
    limit: int = 20
    case_sensitive: bool = False


@dataclass(frozen=True)
class SearchMatch:
    path: str
    line: int
    text: str


def discover_markdown_files(root: Path = ROOT, *, include_derived: bool = False) -> Iterable[Path]:
    root = root.resolve()
    for path in sorted(root.rglob("*.md")):
        if not is_searchable_path(path, root, include_derived=include_derived):
            continue
        yield path


def is_searchable_path(path: Path, root: Path, *, include_derived: bool) -> bool:
    rel_parts = path.resolve().relative_to(root).parts
    if any(part in SKIP_DIRS for part in rel_parts):
        return False
    if rel_parts[0] == "raw":
        return include_derived and len(rel_parts) > 1 and rel_parts[1] == "derived"
    return True


def search_files(queries: list[str], files: Iterable[Path], options: SearchOptions) -> list[SearchMatch]:
    terms = [term for term in queries if term]
    if not terms or options.limit <= 0:
        return []
    if not options.case_sensitive:
        terms = [term.lower() for term in terms]

    matches: list[SearchMatch] = []
    for path in files:
        root = find_root(path)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            haystack = line if options.case_sensitive else line.lower()
            if all(term in haystack for term in terms):
                matches.append(
                    SearchMatch(
                        path=path.resolve().relative_to(root).as_posix(),
                        line=line_number,
                        text=line.strip(),
                    )
                )
                if len(matches) >= options.limit:
                    return matches
    return matches


def find_root(path: Path) -> Path:
    for parent in [path.resolve().parent, *path.resolve().parents]:
        if (parent / ".git").exists() or (parent / "AGENTS.md").exists():
            return parent
        if parent.name in TOP_LEVEL_SEARCH_DIRS:
            return parent.parent
    return ROOT


def format_match(match: SearchMatch) -> str:
    return f"{match.path}:{match.line}: {match.text}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search durable Markdown wiki artifacts before creating new notes."
    )
    parser.add_argument("query", nargs="+", help="One or more terms; all terms must appear on a line.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root to search.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of matching lines to print.")
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Use case-sensitive matching.",
    )
    parser.add_argument(
        "--include-derived",
        action="store_true",
        help="Also search raw/derived parser outputs. raw/external remains excluded.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    options = SearchOptions(limit=args.limit, case_sensitive=args.case_sensitive)
    files = discover_markdown_files(args.root, include_derived=args.include_derived)
    matches = search_files(args.query, files, options)
    for match in matches:
        print(format_match(match))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
