"""Focused checks for the PR visual plan and new-page baseline recovery."""

import contextlib
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import pr_visual_preflight, visual_check


class VisualPreflightTests(unittest.TestCase):
    def test_missing_new_page_baseline_needs_intended_label(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "tools").mkdir()
            (root / "tools" / "visual_check.py").write_text(
                'PAGES = {"new": "/new/"}\nWIDTHS = [390]\n', encoding="utf-8"
            )
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            for name in pr_visual_preflight.WORKFLOWS:
                (workflows / name).write_text(
                    "    runs-on: ubuntu-24.04\n"
                    "    run: python -m pip install playwright==1.64.0\n",
                    encoding="utf-8",
                )
            with patch.object(pr_visual_preflight, "ROOT", root), patch.object(
                pr_visual_preflight, "VISUAL_CHECK", root / "tools" / "visual_check.py"
            ), patch.object(pr_visual_preflight, "changed_files", return_value=["new.qmd"]), patch.object(
                pr_visual_preflight, "git", return_value="abcdef0"
            ), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(
                    pr_visual_preflight.main(["--affected", "new"]), 2
                )
                self.assertEqual(
                    pr_visual_preflight.main(
                        ["--affected", "new", "--expected", "new"]
                    ), 0
                )
            self.assertIn("Missing runner baselines", output.getvalue())
            self.assertIn("visual-skip:new", output.getvalue())

    def test_missing_labelled_baseline_fails_and_retains_runner_image(self):
        class FakePage:
            def on(self, *_):
                return None

        class FakeContext:
            def new_page(self):
                return FakePage()

            def close(self):
                return None

        class FakeBrowser:
            def new_context(self, **_):
                return FakeContext()

            def close(self):
                return None

        class FakePlaywright:
            chromium = types.SimpleNamespace(launch=lambda: FakeBrowser())

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return None

        fake_sync_api = types.ModuleType("playwright.sync_api")
        fake_sync_api.sync_playwright = lambda: FakePlaywright()
        fake_package = types.ModuleType("playwright")

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            args = [
                "visual_check.py", "--baseline-dir", str(root / "baselines"),
                "--diff-dir", str(root / "diffs"), "--shots-dir", str(root / "shots"),
                "--expect-change", "new",
            ]
            with patch.dict(sys.modules, {"playwright": fake_package,
                                          "playwright.sync_api": fake_sync_api}), patch.object(
                visual_check, "PAGES", {"new": "/new/"}
            ), patch.object(visual_check, "WIDTHS", [390]), patch.object(
                visual_check, "ROOT", root
            ), patch.object(visual_check, "shoot", return_value=b"runner image"), patch.object(
                visual_check, "report_fonts", return_value=True
            ), patch.object(sys, "argv", args), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result = visual_check.main()
            self.assertEqual(result, 1)
            self.assertEqual((root / "diffs" / "new-390.png").read_bytes(), b"runner image")
            self.assertEqual((root / "shots" / "new-390.png").read_bytes(), b"runner image")


if __name__ == "__main__":
    unittest.main()
