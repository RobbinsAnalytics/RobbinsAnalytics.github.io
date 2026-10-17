#!/usr/bin/env python3
"""Screenshot the live pages at four widths and compare against committed baselines.

    python tools/visual_check.py                 compare, fail on drift
    python tools/visual_check.py --update        write new baselines
    python tools/visual_check.py --shots-dir D   compare, and keep every
                                                 screenshot taken in D

Exit 0 if every page matches its baseline within tolerance, 1 otherwise. Diff
images are written to the --diff-dir so a failing run can be looked at rather
than argued about.

WHY THE BASELINES ARE GENERATED ON THE RUNNER

They are produced by `.github/workflows/visual-baselines.yml`, which runs on
`workflow_dispatch` on the same ubuntu-latest image as the deploy, and uploads
them as an artifact to be committed deliberately. Generating them on Windows
would guarantee a permanently red check: font hinting, subpixel rendering and
the available font set all differ from a Linux runner, and every screenshot
would differ for reasons that have nothing to do with the site.

That the baselines must come from the runner is the reason they are produced by
a workflow and committed by a person rather than written on first run. No
workflow in this repo pushes to `main` -- the pull-request merge is the release
and the single deliberate approval (ADR 0003), and a CI job that commits to
`main` would quietly break that. So the runner generates, a human commits.

Since the candidate workflow (`.github/workflows/candidate.yml`), the usual
source is not the dispatch workflow at all: a pull request's candidate run
writes every screenshot it compared to `--shots-dir` and uploads them, so a
changed page's new baseline is the exact image that was compared, taken on the
runner from the candidate. The dispatch workflow remains for a whole-set
refresh, such as a runner-image move.

WHAT A FAILURE MEANS

Usually that a style changed. That is not automatically wrong -- it is a
prompt to look at the diff and either fix the regression or re-dispatch the
baseline workflow and commit the new images. It is a review gate, not an
assertion that the design is finished.

IT WILL ALSO GO RED WHEN THE RUNNER IMAGE CHANGES

GitHub updates ubuntu-latest, Chromium and the font packages move, and text
renders a pixel differently. That is a known, real maintenance cost of pixel
comparison, stated here rather than discovered later. The remedy is the same:
look at the diff, confirm it is uniform text jitter and not a layout change,
re-dispatch, commit. The per-channel threshold below absorbs ordinary
antialiasing; it does not absorb a font substitution.
"""

import argparse
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_ORIGIN = "https://www.robbinsanalytics.com"

# The pages `publish.yml` already asserts, minus the /cascadia-semiconductors/*
# paths, which are served by the Cascadia Finance repo. A visual regression
# there cannot be fixed from here, so failing this deploy for one would be
# pointing at the wrong repo.
PAGES = {
    "index": "/",
    "case-studies": "/case-studies.html",
    "about": "/about.html",
    "cascadia": "/cascadia.html",
    "finance": "/projects/cascadia-finance.html",
    "dealdesk": "/projects/cascadia-dealdesk.html",
    "sibling-conflict": "/projects/sibling-conflict.html",
}

# 390 iPhone 14/15, 414 the larger Plus/Max class, 768 tablet portrait and the
# Bootstrap md breakpoint, 1440 desktop.
WIDTHS = [390, 414, 768, 1440]

# A pixel counts as different only if a channel moves by more than this, and
# only against the baseline's 3x3 neighbourhood (see compare()). Text
# antialiasing moves by one or two levels, and glyph edges by one pixel,
# between otherwise identical runs.
CHANNEL_THRESHOLD = 12

# And the page fails only if more than this share of pixels differ. A real
# layout or colour change moves far more than 0.05% of a full-page screenshot;
# antialiasing jitter moves far less.
TOLERANCE = 0.0005


# Font evidence, collected across the run (added 2026-10-16). Two runs of the
# same source once wrapped the About heading differently on the same image and
# browser; the fonts come from Google Fonts on every run, so they are the
# leading suspect. FONT_FILES records which font files were actually served;
# FONT_ERRORS turns a face that failed to load -- a silent fallback that would
# surface as a confusing pixel diff -- into a named failure.
FONT_FILES = set()
FONT_ERRORS = []


def note_font(response):
    if "fonts.gstatic.com" in response.url:
        FONT_FILES.add(response.url)


def shoot(page, url, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(url, wait_until="networkidle", timeout=60000)
    # Fonts load asynchronously; a screenshot taken before they swap in compares
    # a fallback stack against the real one and fails for no reason.
    page.evaluate("() => document.fonts.ready")
    failed = page.evaluate(
        "() => [...document.fonts].filter(f => f.status === 'error')"
        ".map(f => f.family + ' ' + f.weight + ' ' + f.style)")
    if failed:
        FONT_ERRORS.append((url, width, sorted(set(failed))))
    page.wait_for_timeout(600)
    return page.screenshot(full_page=True, animations="disabled", scale="css")


def report_fonts():
    """Print the font files served this run; return False if any face failed."""
    if FONT_FILES:
        print("  fonts served this run (%d files):" % len(FONT_FILES))
        for u in sorted(FONT_FILES):
            print("    %s" % u.split("fonts.gstatic.com/", 1)[-1])
    if not FONT_ERRORS:
        return True
    sys.stderr.write("\nFONT LOAD FAILURE: a screenshot taken now would compare a fallback\n"
                     "face against the baseline. Re-run; if it persists, check fonts.gstatic.com.\n")
    for url, width, faces in FONT_ERRORS:
        sys.stderr.write("  ::error::%s at %d px: %s\n" % (url, width, ", ".join(faces)))
    return False


def png_width(png):
    """Pixel width straight from the IHDR chunk. No decode, no dependency."""
    return struct.unpack(">I", png[16:20])[0]


def compare(baseline_png, current_png, diff_path):
    """Return (ratio_differing, note). ratio is 1.0 for a size mismatch."""
    from PIL import Image, ImageChops, ImageFilter
    import io as _io

    a = Image.open(_io.BytesIO(baseline_png)).convert("RGB")
    b = Image.open(_io.BytesIO(current_png)).convert("RGB")
    note = ""
    if a.size != b.size:
        # A page whose height changed is a change, full stop, and the ratio
        # says so. But it is also the most common INTENDED change -- a
        # sentence got longer -- and until 2026-10-14 this returned here
        # without writing anything, so the diff artifact was empty exactly
        # when a person most needed to look. Diff the overlapping region:
        # the first band of difference is where the text moved.
        note = "size changed: baseline %sx%s, now %sx%s" % (a.size + b.size)
        w, h = min(a.size[0], b.size[0]), min(a.size[1], b.size[1])
        a, b = a.crop((0, 0, w, h)), b.crop((0, 0, w, h))

    # A pixel counts as different only if the candidate's value lies outside
    # the range the baseline shows anywhere in the 3x3 neighbourhood around it,
    # by more than the channel threshold. Text antialiasing moves glyph edges
    # by a pixel between otherwise identical runs, and on a narrow page with
    # many serif headings that alone crossed TOLERANCE: on 2026-10-14 a commit
    # whose tree was identical to a green run failed about-414 (0.083%) and
    # sibling-conflict-414 (0.158%), and every one of those pixels had its
    # value within one pixel in the baseline. A real change moves content by
    # a line, a border, a colour -- far more than one pixel -- and is still
    # caught; a one-pixel shift of a whole element is the price, stated here.
    lo = a.filter(ImageFilter.MinFilter(3))
    hi = a.filter(ImageFilter.MaxFilter(3))
    below = ImageChops.subtract(lo, b)     # how far under the neighbourhood's floor
    above = ImageChops.subtract(b, hi)     # how far over its ceiling
    out = ImageChops.lighter(below, above)
    # Collapse to the largest per-channel move at each pixel, then threshold.
    mono = ImageChops.lighter(ImageChops.lighter(*out.split()[:2]), out.split()[2])
    mono = mono.point(lambda v: 255 if v > CHANNEL_THRESHOLD else 0)
    differing = sum(mono.histogram()[1:])
    total = a.size[0] * a.size[1]
    ratio = differing / float(total) if total else 0.0
    if note:
        ratio = 1.0
    if ratio > TOLERANCE and diff_path:
        diff_path.parent.mkdir(parents=True, exist_ok=True)
        mono.save(diff_path)
    return ratio, note


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origin", default=DEFAULT_ORIGIN)
    ap.add_argument("--cache-bust", default="")
    ap.add_argument("--baseline-dir", default=str(ROOT / ".github" / "visual-baselines"))
    ap.add_argument("--diff-dir", default=str(ROOT / "visual-diffs"))
    ap.add_argument("--update", action="store_true",
                    help="write baselines instead of comparing")
    ap.add_argument("--expect-change", default="",
                    help="comma-separated page slugs (or 'all') the change is meant "
                         "to alter: a difference there is reported and its diff "
                         "saved, but it does not fail the run. candidate.yml fills "
                         "this from the PR's visual-skip:<page> labels.")
    ap.add_argument("--shots-dir", default="",
                    help="when comparing, also write every screenshot taken "
                         "to this directory, named as its baseline is")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    base_dir = Path(args.baseline_dir)
    diff_dir = Path(args.diff_dir)
    shots_dir = Path(args.shots_dir) if args.shots_dir else None
    origin = args.origin.rstrip("/")
    suffix = ("?cb=%s" % args.cache_bust) if args.cache_bust else ""

    if args.update:
        base_dir.mkdir(parents=True, exist_ok=True)

    expect = {s.strip() for s in args.expect_change.split(",") if s.strip()}
    if "all" in expect:
        expect = set(PAGES)
    unknown = expect - set(PAGES)
    if unknown:
        sys.stderr.write("::error::--expect-change names unknown page(s): %s; known: %s\n"
                         % (", ".join(sorted(unknown)), ", ".join(PAGES)))
        return 2
    if expect:
        print("  expected to change (reported, not failed): %s" % ", ".join(sorted(expect)))

    missing, failed, ok = [], [], 0
    expected = []
    rejected = []
    pending = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for width in WIDTHS:
                ctx = browser.new_context(viewport={"width": width, "height": 900},
                                          device_scale_factor=1)
                page = ctx.new_page()
                page.on("response", note_font)
                for slug, path in PAGES.items():
                    name = "%s-%d.png" % (slug, width)
                    target = base_dir / name
                    png = shoot(page, origin + path + suffix, width)

                    if args.update:
                        # A baseline is a claim about what correct looks like,
                        # so it has to pass the cheapest test of correctness
                        # before it earns that status. A full-page screenshot
                        # wider than its viewport means the page scrolls
                        # sideways -- WCAG 1.4.10, Rule 5.3.
                        #
                        # This is not hypothetical. cascadia-390.png sat in
                        # this directory at 509 px wide against a 390 px
                        # viewport, so the gate spent months comparing one
                        # broken rendering against another and reporting
                        # green. A generator that cannot reject its own input
                        # will eventually certify a bug as the standard.
                        shot_w = png_width(png)
                        if shot_w != width:
                            rejected.append((name, shot_w, width))
                            print("  REFUSED  %s  -- %d px wide at a %d px "
                                  "viewport" % (name, shot_w, width))
                            continue
                        # Held, not written. A baseline set is adopted whole or
                        # not at all: writing half of one and then reporting
                        # that none were accepted would be its own false claim.
                        pending.append((target, name, png))
                        print("  ok     %s  (%d bytes)" % (name, len(png)))
                        continue

                    if shots_dir is not None:
                        # The image the comparison used, byte for byte, so
                        # promoting it to a baseline changes nothing about
                        # what was compared.
                        shots_dir.mkdir(parents=True, exist_ok=True)
                        (shots_dir / name).write_bytes(png)

                    if not target.exists():
                        missing.append(name)
                        continue

                    ratio, note = compare(target.read_bytes(), png, diff_dir / name)
                    if ratio > TOLERANCE and slug in expect:
                        expected.append((name, ratio, note))
                    elif ratio > TOLERANCE:
                        failed.append((name, ratio, note))
                    else:
                        ok += 1
                ctx.close()
        finally:
            browser.close()

    if rejected:
        print("")
        print("NO BASELINES WERE WRITTEN. %d passed and were discarded with "
              "them." % len(pending))
        print("A screenshot wider than its viewport is a defect, not a "
              "baseline:")
        for name, got, want in rejected:
            print("  %s  %d px wide at a %d px viewport (over by %d)"
                  % (name, got, want, got - want))
        print("")
        print("Fix the page's horizontal overflow, deploy it, then regenerate.")
        sys.exit(1)

    fonts_ok = report_fonts()
    if args.update and not fonts_ok:
        print("NO BASELINES WERE WRITTEN: a font failed to load.")
        sys.exit(1)

    for target, name, png in pending:
        target.write_bytes(png)
        print("  wrote  %s  (%d bytes)" % (name, len(png)))

    if args.update:
        print("\nBaselines written to %s." % base_dir)
        print("Commit them from the artifact this workflow uploads — they are only")
        print("valid because they were produced on the runner.")
        return 0

    print("  compared  %d page/width combinations at %s"
          % (ok + len(failed), ", ".join(str(w) for w in WIDTHS)))
    print("  tolerance %.3f%% of pixels, per-channel threshold %d/255"
          % (TOLERANCE * 100, CHANNEL_THRESHOLD))

    if missing:
        sys.stderr.write(
            "\nNO BASELINE for %d image(s):\n    %s\n\n"
            "Run the 'Generate visual baselines' workflow (workflow_dispatch),\n"
            "download its artifact, and commit the images to %s.\n\n"
            % (len(missing), "\n    ".join(missing),
               base_dir.relative_to(ROOT).as_posix())
        )
        return 1

    if not fonts_ok:
        return 1

    if expected:
        print("\nCHANGED AS INTENDED (labelled visual-skip; diff images saved, not failed):")
        for name, ratio, note in expected:
            print("  %s — %.3f%% of pixels differ%s" % (name, ratio * 100, (" (%s)" % note) if note else ""))
        print("Commit these pages' screenshots from this run as their own commit; the\n"
              "fast path accepts it (tools/baseline_fastpath.py).")

    if not failed:
        print("\nNo unexpected visual drift.")
        return 0

    sys.stderr.write("\nVISUAL DRIFT\n\n")
    for name, ratio, note in failed:
        sys.stderr.write("  ::error::%s — %.3f%% of pixels differ%s\n"
                         % (name, ratio * 100, (" (%s)" % note) if note else ""))
    sys.stderr.write(
        "\nDiff images are in the uploaded artifact. Look at every one before deciding:\n"
        "a real regression gets fixed; an intended change gets that page's new\n"
        "baselines from this run's candidate-screenshots artifact (CLAUDE.md, How\n"
        "to publish), and a follow-up commit of only those images is accepted by\n"
        "tools/baseline_fastpath.py without a second full run.\n\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
