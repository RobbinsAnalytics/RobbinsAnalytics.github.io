#!/usr/bin/env python3
"""Plan portfolio PR visual labels and runner baselines before opening the PR.

This is a source and Git preflight. It does not render pages, approve images,
replace the candidate check, or infer visual impact from changed filenames.
"""

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VISUAL_CHECK = ROOT / "tools" / "visual_check.py"
WORKFLOWS = ("candidate.yml", "publish.yml", "visual-baselines.yml")


def git(*args):
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return result.stdout.strip()


def visual_config():
    tree = ast.parse(VISUAL_CHECK.read_text(encoding="utf-8"))
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("PAGES", "WIDTHS"):
                    values[target.id] = ast.literal_eval(node.value)
    if not isinstance(values.get("PAGES"), dict) or not isinstance(values.get("WIDTHS"), list):
        raise RuntimeError("PAGES or WIDTHS is not a literal in tools/visual_check.py")
    return values["PAGES"], values["WIDTHS"]


def runner_pins():
    pins = {}
    for name in WORKFLOWS:
        source = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        runner = re.findall(r"^\s*runs-on:\s*(\S+)", source, re.MULTILINE)
        browser = re.findall(r"playwright==([\d.]+)", source)
        if len(runner) != 1 or len(browser) != 1:
            raise RuntimeError("Expected one runner and Playwright pin in " + name)
        pins[name] = (runner[0], browser[0])
    if len(set(pins.values())) != 1:
        raise RuntimeError("Runner/Playwright pins differ: " + repr(pins))
    return next(iter(pins.values()))


def changed_files(base):
    ancestor = git("merge-base", base, "HEAD")
    names = set(git("diff", "--name-only", ancestor, "HEAD").splitlines())
    names.update(git("diff", "--name-only", "HEAD").splitlines())
    names.update(git("ls-files", "--others", "--exclude-standard").splitlines())
    return sorted(name for name in names if name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="origin/main", help="fetched PR base ref")
    parser.add_argument("--affected", action="append", default=[], metavar="SLUG",
                        help="compared page affected by the change; repeat as needed")
    parser.add_argument("--expected", action="append", default=[], metavar="SLUG",
                        help="affected page intentionally changing visually; repeat as needed")
    parser.add_argument("--unmonitored", action="append", default=[], metavar="ROUTE",
                        help="affected route outside PAGES; repeat as needed")
    parser.add_argument("--no-visual-change", action="store_true",
                        help="declare that no rendered page should change")
    args = parser.parse_args(argv)

    try:
        pages, widths = visual_config()
        runner, browser = runner_pins()
        files = changed_files(args.base)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))

    affected, expected = set(args.affected), set(args.expected)
    unknown = (affected | expected) - set(pages)
    if unknown:
        parser.error("Unknown compared page(s): " + ", ".join(sorted(unknown)))
    if not expected <= affected:
        parser.error("Every --expected slug must also be --affected")
    if args.no_visual_change and (affected or expected or args.unmonitored):
        parser.error("--no-visual-change cannot accompany affected routes")
    if not args.no_visual_change and not affected and not args.unmonitored:
        parser.error("Declare --affected, --unmonitored, or --no-visual-change")

    print("PR visual preflight")
    print("  Base: %s; HEAD: %s" % (args.base, git("rev-parse", "--short", "HEAD")))
    print("  Changed files: %d" % len(files))
    for name in files:
        print("    " + name)
    print("  Runner/Playwright: %s / %s (all three workflows)" % (runner, browser))
    print("  Compared pages: %d; widths: %s" % (len(pages), ", ".join(map(str, widths))))

    if args.no_visual_change:
        print("  Declared visual impact: none; candidate still compares every page.")
    else:
        for slug in sorted(affected):
            print("  Affected: %s %s" % (slug, pages[slug]))
        for route in args.unmonitored:
            print("  Unmonitored route: %s (decide whether to add it to PAGES)" % route)

    missing = []
    for slug in pages:
        for width in widths:
            name = "%s-%s.png" % (slug, width)
            if not (ROOT / ".github" / "visual-baselines" / name).is_file():
                missing.append((slug, name))
    if missing:
        print("  Missing runner baselines:")
        for _, name in missing:
            print("    " + name)
        print("  Open the PR with intended-page labels. The first candidate run must fail")
        print("  on missing baselines. Inspect its runner screenshots, commit only those")
        print("  images, and use the baseline-only fast path. Do not merge before green.")
        unplanned = {slug for slug, _ in missing} - affected
        if unplanned:
            print("  ERROR: missing-baseline pages not declared affected: " +
                  ", ".join(sorted(unplanned)))
            return 2
        unlabelled = {slug for slug, _ in missing} - expected
        if unlabelled:
            print("  ERROR: missing-baseline pages need an intended-change label: " +
                  ", ".join(sorted(unlabelled)))
            return 2
    else:
        print("  Baselines: present for every compared page and width.")

    if expected:
        labels = ["visual-skip:" + slug for slug in sorted(expected)]
        print("  Add when opening the PR: " + ", ".join(labels))
        print("  Review each reported diff; commit the run's screenshots before merge.")
    else:
        print("  Expected-change labels: none.")
    print("  Preflight complete. Candidate CI and owner review remain required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
