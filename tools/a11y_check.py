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

An entry matches on rule AND page, never on rule alone. Each carries `page`:
a path, a list of paths, or "*" for every page, stated explicitly rather than
by omission. It may also carry `selector`: then only violating nodes whose
axe target contains that string are accepted, and any other node failing the
same rule on the same page is new. Until 2026-10-14 the match was on rule id
alone, so a violation of either accepted rule in this site's own markup, on
any page, would have passed -- the third-party scope the ledger described was
not the scope the code enforced.

WHICH PAGES

Built, not typed: see site_pages(). The hand list this replaced named
thirteen pages and had been missing five case studies for as long as they had
existed, because nothing added a page to it when a page was added.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_ORIGIN = "https://www.robbinsanalytics.com"

# Redirect stubs under projects/: hand-written .html files that are not render
# inputs and reach _site through _quarto.yml's resources list. Each carries an
# instant <meta http-equiv="refresh"> to a page served by another repository.
# They are this site's own markup and are checked as such; see page_route().
STUBS = sorted("/projects/%s" % p.name for p in (ROOT / "projects").glob("*.html"))


def site_pages():
    """Every page this repo renders or ships, derived from the tree.

    THIS LIST IS BUILT, NOT TYPED. The roots are the top-level .qmd files
    (index.qmd is "/"); every projects/*.qmd by its rendered name; every
    projects/*.html redirect stub. A page added to the site is checked on its
    next run with no edit here.

    Not included, deliberately: the /cascadia-semiconductors/* paths and the
    other module paths under this domain, which are served by their own
    repositories and cannot be fixed from here; and the apex and github.io
    hosts, which the publish workflow asserts redirect -- they are hosts, not
    pages of a candidate, and have nothing for axe to read.
    """
    pages = []
    for q in sorted(ROOT.glob("*.qmd")):
        pages.append("/" if q.stem == "index" else "/%s.html" % q.stem)
    for q in sorted((ROOT / "projects").glob("*.qmd")):
        pages.append("/projects/%s.html" % q.stem)
    pages.extend(STUBS)
    return pages


PAGES = site_pages()

# A stub redirects on load with a zero delay, so a plain navigation lands axe
# on the destination -- another repository's page -- and never on the stub.
# The stub's own markup is what this repo authors and answers for, so its
# refresh directive is stripped in transit and the page is checked as it is
# served otherwise. Nothing checkable is lost: axe's own meta-refresh rule
# permits a zero delay, which is the only thing the removed tag said.
_REFRESH = re.compile(r'<meta\s+http-equiv="refresh"[^>]*>', re.I)


def page_route(origin):
    stub_urls = {origin + s for s in STUBS}

    def handler(route):
        url = route.request.url.split("?", 1)[0]
        if route.request.resource_type == "document" and url in stub_urls:
            response = route.fetch()
            route.fulfill(response=response, body=_REFRESH.sub("", response.text()))
        else:
            route.continue_()
    return handler

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
    """The accepted entries, as a list. Each must say which page(s) it covers."""
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("accepted", [])
    for e in entries:
        if "page" not in e:
            sys.exit("a11y baseline entry %r has no `page`; say \"*\" if it "
                     "really is every page" % e.get("id"))
    return entries


def entry_covers(entry, path):
    page = entry["page"]
    if page == "*":
        return True
    if isinstance(page, list):
        return path in page
    return page == path


def entry_label(entry):
    page = entry["page"]
    if isinstance(page, list):
        page = ", ".join(page)
    return "%s on %s" % (entry["id"], "every page" if page == "*" else page)


def split_nodes(violation, path, baseline):
    """Partition a violation's nodes into (accepted targets, new targets, entries hit)."""
    entries = [e for e in baseline
               if e["id"] == violation["id"] and entry_covers(e, path)]
    accepted, new, hit = [], [], []
    for node in violation.get("nodes", []):
        targets = [str(t) for t in node.get("target", [])]
        covering = [e for e in entries
                    if "selector" not in e
                    or any(e["selector"] in t for t in targets)]
        if covering:
            accepted.extend(targets)
            hit.extend(covering)
        else:
            new.extend(targets)
    return accepted, new, hit


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
    hits = {}       # id(entry) -> accepted nodes this run
    checked = 0
    route = page_route(origin)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for label, w, h in VIEWPORTS:
                ctx = browser.new_context(viewport={"width": w, "height": h})
                page = ctx.new_page()
                page.route("**/*", route)
                for path in PAGES:
                    url = origin + path + suffix
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    result = axe.run(page, options={
                        "runOnly": {"type": "tag", "values": TAGS},
                    })
                    checked += 1
                    for v in result.get("violations", []):
                        _, new_targets, hit = split_nodes(v, path, baseline)
                        for e in hit:
                            hits[id(e)] = hits.get(id(e), 0) + 1
                        if new_targets:
                            new.append((v["id"], path, label, v.get("impact") or "n/a",
                                        v.get("help", ""), new_targets[:4]))
                ctx.close()

            for w in REFLOW_WIDTHS:
                ctx = browser.new_context(viewport={"width": w, "height": 844})
                page = ctx.new_page()
                page.route("**/*", route)
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

    n_proj = len(list((ROOT / "projects").glob("*.qmd")))
    print("  pages: %d, derived from the tree (%d roots, %d projects/*.qmd, %d stubs)"
          % (len(PAGES), len(PAGES) - n_proj - len(STUBS), n_proj, len(STUBS)))
    print("  axe-core over %d page/viewport combinations" % checked)
    print("  tags: %s" % ", ".join(TAGS))
    print("  viewports: %s" % ", ".join("%s %dx%d" % v for v in VIEWPORTS))
    print("  reflow (WCAG 1.4.10) over %d page/width combinations at %s"
          % (reflow_checked, ", ".join(str(w) for w in REFLOW_WIDTHS)))

    if baseline:
        print()
        print("  ACCEPTED VIOLATIONS — recorded in %s, reported every run, not failing:"
              % Path(args.baseline).name)
        for entry in sorted(baseline, key=entry_label):
            print("    %-60s %d node(s) this run"
                  % (entry_label(entry), hits.get(id(entry), 0)))
            if "selector" in entry:
                print("        only nodes whose target contains %r" % entry["selector"])
            print("        %s" % entry.get("reason", "(no reason recorded)"))
        # An entry marked intermittent depends on third-party script timing and
        # legitimately matches nothing on some runs. Exempting it keeps the
        # stale-entry warning meaningful for the entries where it is real.
        stale = [entry_label(e) for e in baseline
                 if not e.get("intermittent") and not hits.get(id(e))]
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
        "Fix these, or record one in %s with its page and a reason if it is genuinely\n"
        "accepted. An entry there is reported on every run — it is a ledger, not a mute.\n\n"
        % Path(args.baseline).name
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
