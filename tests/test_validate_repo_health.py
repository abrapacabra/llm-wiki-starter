import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from tools import validate_repo


ROOT = Path(__file__).resolve().parents[1]


class ValidateRepoHealthTests(unittest.TestCase):
    def test_health_report_is_non_blocking_and_reports_sections(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "validate_repo.py"), "--health-report"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("Repository validation passed.", result.stdout)
        self.assertIn("Wiki health report", result.stdout)
        self.assertIn("Unresolved statuses", result.stdout)
        self.assertIn("Orphan candidates", result.stdout)

    def test_health_report_ignores_wikilinks_inside_inline_code_spans(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "knowledge").mkdir()
            (root / "knowledge" / "note.md").write_text(
                "\n".join(
                    [
                        "---",
                        "artifact_type: knowledge-note",
                        "status: active",
                        'title: "Inline Code Probe"',
                        "---",
                        "",
                        "# Inline Code Probe",
                        "",
                        "Literal examples: `[[Missing Single]]` and ``[[Missing Double]]``.",
                        "A real unresolved link remains: [[Visible Missing]].",
                    ]
                ),
                encoding="utf-8",
            )

            with mock.patch.object(validate_repo, "ROOT", root):
                report = validate_repo.health_report({})

            self.assertIn("knowledge/note.md -> [[Visible Missing]]", report)
            self.assertNotIn("Missing Single", report)
            self.assertNotIn("Missing Double", report)

    def test_validator_ignores_local_virtualenv_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".venv" / "lib").mkdir(parents=True)
            (root / ".venv" / "lib" / "third-party.md").write_text(
                "[broken](missing.md)\n",
                encoding="utf-8",
            )

            with mock.patch.object(validate_repo, "ROOT", root):
                errors = []
                validate_repo.validate_links(errors)

            self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
