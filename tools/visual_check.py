#!/usr/bin/env python3
"""Screenshot the live pages at four widths and compare against committed baselines.

    python tools/visual_check.py                 compare, fail on drift
    python tools/visual_check.py --update        write new baselines

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

That the baselines must come from the runner is the reason this is a separate
dispatch workflow rather than a step that writes them on first run. The deploy
workflow does not push to `main` -- in this repo the push IS the deploy and the
single deliberate approval, and a CI job that commits to `main` would quietly
break that. So the runner generates, a human commits.

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
    "about": "/about.html",
    "cascadia": "/cascadia.html",
    "finance": "/projects/cascadia-finance.html",
    "dealdesk": "/projects/cascadia-dealdesk.html",
    "sibling-conflict": "/projects/sibling-conflict.html",
}

# 390 iPhone 14/15, 414 the larger Plus/Max class, 768 tablet portrait and the
# Bootstrap md breakpoint, 1440 desktop.
WIDTHS = [390, 414, 768, 1440]

# A pixel counts as different only if a channel moves by more than this. Text
# antialiasing moves by one or two levels between otherwise identical runs.
CHANNEL_THRESHOLD = 12

# And the page fails only if more than this share of pixels differ. A real
# layout or colour change moves far more than 0.05% of a full-page screenshot;
# antialiasing jitter moves far less.
TOLERANCE = 0.0005


def shoot(page, url, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(url, wait_until="networkidle", timeout=60000)
    # Fonts load asynchronously; a screenshot taken before they swap in compares
    # a fallback stack against the real one and fails for no reason.
    page.evaluate("() => document.fonts.ready")
    page.wait_for_timeout(600)
    return page.screenshot(full_page=True, animations="disabled", scale="css")


def png_width(png):
    """Pixel width straight from the IHDR chunk. No decode, no dependency."""
    return struct.unpack(">I", png[16:20])[0]


def compare(baseline_png, current_png, diff_path):
    """Return (ratio_differing, note). ratio is 1.0 for a size mismatch."""
    from PIL import Image, ImageChops
    import io as _io

    a = Image.open(_io.BytesIO(baseline_png)).convert("RGB")
    b = Image.open(_io.BytesIO(current_png)).convert("RGB")
    if a.size != b.size:
        return 1.0, "size changed: baseline %sx%s, now %sx%s" % (a.size + b.size)

    diff = ImageChops.difference(a, b)
    # Collapse to the largest per-channel move at each pixel, then threshold.
    mono = diff.convert("L").point(lambda v: 255 if v > CHANNEL_THRESHOLD else 0)
    differing = sum(mono.histogram()[1:])
    total = a.size[0] * a.size[1]
    ratio = differing / float(total) if total else 0.0
    if ratio > TOLERANCE and diff_path:
        diff_path.parent.mkdir(parents=True, exist_ok=True)
        mono.save(diff_path)
    return ratio, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origin", default=DEFAULT_ORIGIN)
    ap.add_argument("--cache-bust", default="")
    ap.add_argument("--baseline-dir", default=str(ROOT / ".github" / "visual-baselines"))
    ap.add_argument("--diff-dir", default=str(ROOT / "visual-diffs"))
    ap.add_argument("--update", action="store_true",
                    help="write baselines instead of comparing")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    base_dir = Path(args.baseline_dir)
    diff_dir = Path(args.diff_dir)
    origin = args.origin.rstrip("/")
    suffix = ("?cb=%s" % args.cache_bust) if args.cache_bust else ""

    if args.update:
        base_dir.mkdir(parents=True, exist_ok=True)

    missing, failed, ok = [], [], 0
    rejected = []
    pending = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for width in WIDTHS:
                ctx = browser.new_context(viewport={"width": width, "height": 900},
                                          device_scale_factor=1)
                page = ctx.new_page()
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

                    if not target.exists():
                        missing.append(name)
                        continue

                    ratio, note = compare(target.read_bytes(), png, diff_dir / name)
                    if ratio > TOLERANCE:
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

    if not failed:
        print("\nNo visual drift.")
        return 0

    sys.stderr.write("\nVISUAL DRIFT\n\n")
    for name, ratio, note in failed:
        sys.stderr.write("  ::error::%s — %.3f%% of pixels differ%s\n"
                         % (name, ratio * 100, (" (%s)" % note) if note else ""))
    sys.stderr.write(
        "\nDiff images are in the uploaded artifact. Look at them before deciding:\n"
        "a real regression gets fixed, an intended design change gets new baselines\n"
        "from the 'Generate visual baselines' workflow.\n\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
