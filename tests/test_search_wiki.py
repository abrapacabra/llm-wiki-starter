import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.search_wiki import SearchOptions, discover_markdown_files, search_files


ROOT = Path(__file__).resolve().parents[1]


class SearchWikiTests(unittest.TestCase):
    def test_default_search_excludes_external_and_derived_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "knowledge").mkdir()
            (root / "raw" / "external").mkdir(parents=True)
            (root / "raw" / "derived" / "source-a").mkdir(parents=True)
            (root / "knowledge" / "note.md").write_text("Alpha durable note\n", encoding="utf-8")
            (root / "raw" / "external" / "source.md").write_text("Alpha external original\n", encoding="utf-8")
            (root / "raw" / "derived" / "source-a" / "chunk.md").write_text("Alpha derived chunk\n", encoding="utf-8")

            files = list(discover_markdown_files(root, include_derived=False))
            matches = search_files(["alpha"], files, SearchOptions(limit=10))

            self.assertEqual(["knowledge/note.md"], [match.path for match in matches])

    def test_include_derived_adds_raw_derived_without_external_originals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "knowledge").mkdir()
            (root / "raw" / "external").mkdir(parents=True)
            (root / "raw" / "derived" / "source-a").mkdir(parents=True)
            (root / "knowledge" / "note.md").write_text("Beta durable note\n", encoding="utf-8")
            (root / "raw" / "external" / "source.md").write_text("Beta external original\n", encoding="utf-8")
            (root / "raw" / "derived" / "source-a" / "chunk.md").write_text("Beta derived chunk\n", encoding="utf-8")

            files = list(discover_markdown_files(root, include_derived=True))
            matches = search_files(["beta"], files, SearchOptions(limit=10))

            self.assertEqual(
                ["knowledge/note.md", "raw/derived/source-a/chunk.md"],
                [match.path for match in matches],
            )

    def test_cli_prints_matches_in_path_line_text_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "knowledge").mkdir()
            (root / "knowledge" / "note.md").write_text(
                "No match here\nAlpha command line result\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "search_wiki.py"),
                    "alpha",
                    "--root",
                    str(root),
                    "--limit",
                    "1",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual("knowledge/note.md:2: Alpha command line result\n", result.stdout)
            self.assertEqual("", result.stderr)

    def test_cli_limit_zero_prints_no_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "knowledge").mkdir()
            (root / "knowledge" / "note.md").write_text("Alpha result\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "search_wiki.py"),
                    "alpha",
                    "--root",
                    str(root),
                    "--limit",
                    "0",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual("", result.stdout)
            self.assertEqual("", result.stderr)


if __name__ == "__main__":
    unittest.main()
