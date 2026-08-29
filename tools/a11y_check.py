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

# WCAG 1.4.10 reflow. axe-core does not test it, and the gap is not academic:
# this check reported green on every run for months while cascadia.html was
# 542 px wide at a 390 px viewport and the whole page -- navbar included --
# scrolled sideways on a phone. A check whose name implies coverage it does
# not have is worse than no check, because it is believed.
#
# 320 px is the width the criterion actually names. 390 is added because that
# is where the real defect lived and where a reader meets it.
REFLOW_WIDTHS = [320, 390]

TAGS = ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]


def load_baseline(path):
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {e["id"]: e for e in data.get("accepted", [])}


def load_reflow_baseline(path):
    """Pages whose horizontal overflow is accepted, keyed by path.

    Kept apart from `accepted` because the two are accepted for different
    reasons and only one of them is unfixable. See the comments in the ledger.
    """
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {e["page"]: e for e in data.get("accepted_reflow", [])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origin", default=DEFAULT_ORIGIN)
    ap.add_argument("--cache-bust", default="")
    ap.add_argument("--baseline", default=str(ROOT / ".github" / "a11y-baseline.json"))
    args = ap.parse_args()

    from axe_core_python.sync_playwright import Axe
    from playwright.sync_api import sync_playwright

    baseline = load_baseline(Path(args.baseline))
    reflow_baseline = load_reflow_baseline(Path(args.baseline))
    axe = Axe()
    origin = args.origin.rstrip("/")
    suffix = ("?cb=%s" % args.cache_bust) if args.cache_bust else ""

    new = []        # (rule_id, page, viewport, impact, help, [targets])
    reflow = []     # (page, width, scrollWidth, clientWidth)
    reflow_accepted = []
    reflow_checked = 0
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

            for w in REFLOW_WIDTHS:
                ctx = browser.new_context(viewport={"width": w, "height": 844})
                page = ctx.new_page()
                for path in PAGES:
                    page.goto(origin + path + suffix, wait_until="networkidle",
                              timeout=60000)
                    page.evaluate("() => document.fonts.ready")
                    page.wait_for_timeout(200)
                    m = page.evaluate(
                        "() => ({s: document.documentElement.scrollWidth,"
                        "        c: document.documentElement.clientWidth})")
                    reflow_checked += 1
                    if m["s"] > m["c"] + 1:
                        if path in reflow_baseline:
                            reflow_accepted.append((path, w, m["s"], m["c"]))
                        else:
                            reflow.append((path, w, m["s"], m["c"]))
                ctx.close()
        finally:
            browser.close()

    print("  axe-core over %d page/viewport combinations" % checked)
    print("  tags: %s" % ", ".join(TAGS))
    print("  viewports: %s" % ", ".join("%s %dx%d" % v for v in VIEWPORTS))
    print("  reflow (WCAG 1.4.10) over %d page/width combinations at %s"
          % (reflow_checked, ", ".join(str(w) for w in REFLOW_WIDTHS)))

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

    if reflow_baseline:
        print()
        print("  ACCEPTED REFLOW \u2014 recorded, reported every run, not failing:")
        for page, entry in sorted(reflow_baseline.items()):
            hits = sorted({w for p, w, _, _ in reflow_accepted if p == page})
            print("    %-46s overflows at %s"
                  % (page, ", ".join("%d px" % w for w in hits) or "nothing this run"))
            print("        %s" % entry.get("reason", "(no reason recorded)"))
        stale_reflow = [pg for pg in reflow_baseline
                        if not any(p == pg for p, _, _, _ in reflow_accepted)]
        if stale_reflow:
            print()
            print("  ::warning::these reflow entries matched nothing and look "
                  "fixed \u2014 remove them: %s" % ", ".join(sorted(stale_reflow)))

    if reflow:
        sys.stderr.write("\nREFLOW — the page scrolls sideways (WCAG 1.4.10)\n\n")
        for path, w, sw, cw in sorted(reflow):
            sys.stderr.write(
                "  ::error::%s is %d px wide at a %d px viewport (over by %d)\n"
                % (path, sw, w, sw - cw))
        sys.stderr.write(
            "\nWide content belongs in its own overflow-x container; the page "
            "around it must not scroll.\n\n")

    if not new and not reflow:
        print()
        print("No new machine-detectable violations. This is not a conformance claim.")
        return 0

    if not new:
        return 1

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
