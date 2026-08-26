#!/usr/bin/env python3
"""Run axe-core over the live site and fail on any violation it can detect.

    python tools/a11y_check.py [--origin URL] [--cache-bust SHA] [--baseline FILE]

Exit 0 if no new violation is found, 1 otherwise.

THIS IS REGRESSION PREVENTION. IT IS NOT PROOF OF CONFORMANCE.

Automated accessibility tooling reaches roughly 30-40% of WCAG success
criteria. The rest -- whether alt text says the right thing, whether a heading
structure matches the document's actual shape, whether a chart's description
carries its finding, whether focus order follows reading order -- needs a
person. A green run here means no machine-detectable regression. It does not
mean the page conforms to anything, and nothing in this repo may say that it
does.

That is not a hedge bolted on afterwards. This repo's own history is the
reason: five places on this site asserted "WCAG 2.2 AA" as settled fact when
nothing had ever checked it, and correcting those claims is the commit this
check was built on top of. A CI job that turns green and is then quoted as
conformance would re-create exactly the defect that commit removed. The site
says "WCAG 2.2 AA target (unverified)" and it stays that way until a person
audits it.

WHAT IS CHECKED

The four tag sets named in the run brief -- wcag2a, wcag2aa, wcag21aa,
wcag22aa -- at a desktop and a mobile viewport, because some criteria (target
size, reflow) only fail at one of them.

THE BASELINE FILE

`.github/a11y-baseline.json` records violations that exist today and are
accepted for now, each with a reason. A recorded violation is reported on every
run and does not fail it; anything not in the file does. The file is a ledger,
not a mute: it is printed in full every run, so an accepted violation cannot
quietly become permanent by being invisible. Removing an entry is how one gets
fixed.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_ORIGIN = "https://www.robbinsanalytics.com"

# The site's own pages. The /cascadia-semiconductors/* paths are served by the
# Cascadia Finance repo and cannot be fixed from here, so they are not asserted
# by this check -- the publish workflow already asserts they return 200.
PAGES = [
    "/",
    "/about.html",
    "/cascadia.html",
    "/projects/cascadia-finance.html",
    "/projects/cascadia-dealdesk.html",
    "/projects/cascadia-controltower.html",
    "/projects/cascadia-medical-devices.html",
    "/projects/cascadia-pharmacy.html",
    "/projects/cascadia-staffing.html",
    "/projects/cascadia-bi-migration.html",
    "/projects/sibling-conflict.html",
]

VIEWPORTS = [("desktop", 1440, 900), ("mobile", 390, 844)]

TAGS = ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]


def load_baseline(path):
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {e["id"]: e for e in data.get("accepted", [])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origin", default=DEFAULT_ORIGIN)
    ap.add_argument("--cache-bust", default="")
    ap.add_argument("--baseline", default=str(ROOT / ".github" / "a11y-baseline.json"))
    args = ap.parse_args()

    from axe_core_python.sync_playwright import Axe
    from playwright.sync_api import sync_playwright

    baseline = load_baseline(Path(args.baseline))
    axe = Axe()
    origin = args.origin.rstrip("/")
    suffix = ("?cb=%s" % args.cache_bust) if args.cache_bust else ""

    new = []        # (rule_id, page, viewport, impact, help, [targets])
    accepted_hits = []
    checked = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for label, w, h in VIEWPORTS:
                ctx = browser.new_context(viewport={"width": w, "height": h})
                page = ctx.new_page()
                for path in PAGES:
                    url = origin + path + suffix
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    result = axe.run(page, options={
                        "runOnly": {"type": "tag", "values": TAGS},
                    })
                    checked += 1
                    for v in result.get("violations", []):
                        targets = [t for n in v.get("nodes", []) for t in n.get("target", [])]
                        row = (v["id"], path, label, v.get("impact") or "n/a",
                               v.get("help", ""), targets[:4])
                        if v["id"] in baseline:
                            accepted_hits.append(row)
                        else:
                            new.append(row)
                ctx.close()
        finally:
            browser.close()

    print("  axe-core over %d page/viewport combinations" % checked)
    print("  tags: %s" % ", ".join(TAGS))
    print("  viewports: %s" % ", ".join("%s %dx%d" % v for v in VIEWPORTS))

    if baseline:
        print()
        print("  ACCEPTED VIOLATIONS — recorded in %s, reported every run, not failing:"
              % Path(args.baseline).name)
        for rid, entry in sorted(baseline.items()):
            hits = sum(1 for r in accepted_hits if r[0] == rid)
            print("    %-28s %d hit(s) this run" % (rid, hits))
            print("        %s" % entry.get("reason", "(no reason recorded)"))
        # An entry marked intermittent depends on third-party script timing and
        # legitimately matches nothing on some runs. Exempting it keeps the
        # stale-entry warning meaningful for the entries where it is real.
        stale = [rid for rid, e in baseline.items()
                 if not e.get("intermittent")
                 and not any(r[0] == rid for r in accepted_hits)]
        if stale:
            print()
            print("  ::warning::these baseline entries matched nothing and look fixed — "
                  "remove them: %s" % ", ".join(sorted(stale)))

    if not new:
        print()
        print("No new machine-detectable violations. This is not a conformance claim.")
        return 0

    sys.stderr.write("\nACCESSIBILITY VIOLATIONS\n\n")
    for rid, path, label, impact, help_text, targets in sorted(new):
        sys.stderr.write("  ::error::%s [%s] on %s (%s)\n" % (rid, impact, path, label))
        sys.stderr.write("           %s\n" % help_text)
        for t in targets:
            sys.stderr.write("           at %s\n" % t)
        sys.stderr.write("\n")
    sys.stderr.write(
        "Fix these, or record one in %s with a reason if it is genuinely accepted.\n"
        "An entry there is reported on every run — it is a ledger, not a mute.\n\n"
        % Path(args.baseline).name
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
