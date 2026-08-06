#!/usr/bin/env python3
"""Build Cascadia OG/social thumbnails to the v2.2 design system.

1200x630 (the Open Graph standard, and what iMessage/Slack/LinkedIn crop to).
Rendered through the same Chromium the charts are, so the type and the palette
are identical rather than merely similar.

The signature elements, from VIZ-PRINCIPLES.md:
  - Paper #FCFCFA surface, Basalt text, Slate moss secondary
  - Source Serif 4 carries the voice; the Segoe UI stack carries the data
  - the provenance strip's Evergreen tick, in the same position every time
  - restraint: no gradients, no shadows, no decoration touching the type
"""

import argparse
import sys
from pathlib import Path

# Default output is the site's assets/ folder, two levels up from tools/.
# CI regenerates in place before `quarto render`, so the images that deploy are
# always derived from this file rather than hand-carried between machines.
_DEFAULT_OUT = Path(__file__).resolve().parent.parent / "assets"
OUT = _DEFAULT_OUT

# The identity mark, read from the one file that defines it rather than copied
# here — LOGO.md 2.1's coordinates must never exist in two places. Rendered at
# 48 px, an integer 3x of the 16-unit grid (LOGO.md 2.1), in the top-right of
# the card where it is nowhere near the motif: the motif is a real chart form,
# and LOGO.md 4.1 keeps the mark off the canvas.
_MARK_SVG = (Path(__file__).resolve().parent.parent
             / "assets" / "brand" / "robbins-mark.svg")

C = {
    "evergreen": "#1E7A4C", "glacier": "#4C8BC0", "madrona": "#C05A2E",
    "lupine": "#7B68AE", "lichen": "#9C7A20", "rain": "#9AA6A0",
    "basalt": "#232B27", "slate": "#5B6660", "mist": "#E4E7E3",
    "paper": "#FCFCFA", "spruce": "#16241D",
}

# Rule 2.3.1 — fixed slots, never re-dealt. A module keeps its hue everywhere.
MODULES = [
    dict(slug="portfolio", data="seven modules · real and synthetic sources, labelled per module", kicker="Robbins Analytics", title="Analytics that shows its work",
         line="Seven governed BI modules — the data layer, the metric layer, and the review that let them ship.",
         accent="evergreen", motif="bars", landing=True),
    dict(slug="dealdesk", data="synthetic data, seeded generator", kicker="Cascadia Deal Desk", title="Pricing governance and margin leakage",
         line="A governed agreement register, a documented matching rule, and an exception report you calibrate before you automate.",
         accent="evergreen", motif="decay"),
    dict(slug="finance", data="SEC EDGAR XBRL · public filings", kicker="Cascadia Finance", title="An executive close pack from SEC XBRL",
         line="FormFactor's GAAP financials from EDGAR — Python, SQLite, and static ECharts.",
         accent="glacier", motif="line"),
    dict(slug="staffing", data="CMS PBJ daily nurse staffing · public data", kicker="Cascadia Staffing", title="Contingent-labor economics for nursing facilities",
         line="Real CMS payroll data, with a certified-metric governance layer.",
         accent="madrona", motif="bars"),
    dict(slug="pharmacy", data="CMS Part D and CDC · public data", kicker="Cascadia Pharmacy", title="GLP-1 spend growth and immunization coverage",
         line="Real CMS and CDC public data.",
         accent="lupine", motif="line"),
    dict(slug="medical-devices", data="NASA C-MAPSS + synthetic MES", kicker="Cascadia Medical Devices", title="Predictive maintenance and OEE",
         line="A 5.9M-row manufacturing dataset, from raw telemetry to a governed OEE metric.",
         accent="lichen", motif="decay"),
    dict(slug="bi-migration", data="program design · no production data", kicker="Cascadia BI Migration", title="Off legacy BI in 24 weeks",
         line="A governed, AI-assisted platform with a certified metric layer at the center.",
         accent="glacier", motif="steps"),
    dict(slug="clothing", data="synthetic data · in build", kicker="Cascadia Clothing", title="Retail and ecommerce analytics",
         line="In build — an apparel scenario.",
         accent="rain", motif="bars", muted=True),
]

MOTIFS = {
    # Small, honest marks. Not decoration — each is a real chart form from the
    # system, drawn at signature-chart rules (0.3): shape only, no axes.
    "bars":  [46, 62, 38, 74, 55, 88, 67, 96],
    "line":  [30, 44, 38, 58, 52, 71, 66, 84],
    "decay": [96, 74, 55, 41, 31, 24, 19, 15],
    "steps": [22, 22, 48, 48, 63, 63, 91, 91],
}


def motif_svg(kind, colour, muted=False):
    vals = MOTIFS[kind]
    n = len(vals)
    w, h, gap = 288.0, 68.0, 6.0
    col = C["rain"] if muted else C[colour]
    if kind in ("bars", "steps"):
        bw = (w - gap * (n - 1)) / n
        rects = "".join(
            f'<rect x="{i*(bw+gap):.1f}" y="{h - h*v/100:.1f}" '
            f'width="{bw:.1f}" height="{h*v/100:.1f}" fill="{col}"/>'
            for i, v in enumerate(vals))
        return f'<svg width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">{rects}</svg>'
    step = w / (n - 1)
    pts = " ".join(f"{i*step:.1f},{h - h*v/100:.1f}" for i, v in enumerate(vals))
    dots = "".join(
        f'<circle cx="{i*step:.1f}" cy="{h - h*v/100:.1f}" r="3.5" fill="{col}"/>'
        for i, v in enumerate(vals))
    return (f'<svg width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}">'
            f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.5" '
            f'stroke-linejoin="round" stroke-linecap="round"/>{dots}</svg>')


def page(m):
    accent = C["rain"] if m.get("muted") else C[m["accent"]]
    title_size = 62 if len(m["title"]) < 46 else 54
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">
<style>
  @page {{ size: 1200px 630px; margin: 0 }}
  * {{ box-sizing: border-box; margin: 0; padding: 0 }}
  html, body {{ width: 1200px; height: 630px; background: {C['paper']} }}
  body {{
    display: flex; flex-direction: column; justify-content: space-between;
    padding: 68px 76px 56px;
    font-family: "Segoe UI", -apple-system, "Helvetica Neue", Liberation Sans, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .head {{ display: flex; align-items: center; justify-content: space-between }}
  .kicker {{
    display: flex; align-items: center; gap: 14px;
    font-size: 19px; letter-spacing: .13em; text-transform: uppercase;
    color: {C['slate']}; font-weight: 600;
  }}
  /* LOGO.md 1.2 asks for 1 C of clear space on all four sides. The card's own
     68px/76px padding already exceeds it at this size, so the mark needs no
     margin of its own — but it must not be enlarged without re-checking that. */
  .brand {{ width: 48px; height: 48px; flex: none }}
  .brand svg {{ width: 48px; height: 48px; display: block }}
  .tick {{ display:block; width: 5px; height: 24px; background: {accent}; flex: none }}
  h1 {{
    font-family: "Source Serif 4", Georgia, Liberation Serif, "Times New Roman", serif;
    font-weight: 600; font-size: {title_size}px; line-height: 1.13;
    color: {C['basalt']}; max-width: 21ch; letter-spacing: -0.005em;
  }}
  .line {{
    font-family: "Source Serif 4", Georgia, Liberation Serif, serif;
    font-size: 25px; line-height: 1.45; color: {C['slate']}; max-width: 60ch;
  }}
  .mid {{ display:flex; flex-direction: column; gap: 22px; flex: 1; justify-content: center }}
  .foot {{ display: flex; flex-direction: column; align-items: stretch; gap: 0 }}
  .motifrow {{ display:flex; justify-content: flex-end; margin-bottom: 16px }}
  .motif {{ opacity: {0.55 if m.get('muted') else 1}; display: block }}
  .strip {{
    display:flex; align-items:center; gap: 11px;
    font-size: 17px; color: {C['slate']};
    border-top: 1px solid {C['mist']}; padding-top: 15px;
  }}
  .strip .tick {{ height: 17px; background: {C['evergreen']} }}
</style></head><body>
  <div class="head">
    <div class="kicker"><span class="tick"></span>{m['kicker']}</div>
    <div class="brand">{_MARK_SVG.read_text(encoding="utf-8")}</div>
  </div>
  <div class="mid">
    <h1>{m['title']}</h1>
    <div class="line">{m['line']}</div>
  </div>
  <div class="foot">
    <div class="motifrow"><div class="motif">{motif_svg(m['motif'], m['accent'], m.get('muted', False))}</div></div>
    <div class="strip"><span class="tick"></span>Aaron Robbins · robbinsanalytics.com · {m['data']}</div>
  </div>
</body></html>"""


def main():
    global OUT
    ap = argparse.ArgumentParser(description="Build Cascadia OG thumbnails.")
    ap.add_argument("--out", default=str(_DEFAULT_OUT),
                    help="output directory (default: the site's assets/ folder)")
    ap.add_argument("--strict", action="store_true",
                    help="fail if Source Serif 4 did not load, instead of warning")
    args = ap.parse_args()
    # resolve(): as_uri() below requires an absolute path, and a relative --out
    # (e.g. `--out assets` from a CI working directory) would otherwise fail
    # deep in the render loop with "relative path can't be expressed as a file
    # URI" rather than at the point the argument was supplied.
    OUT = Path(args.out).resolve()
    OUT.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright
    made = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_context(viewport={"width": 1200, "height": 630},
                           device_scale_factor=1).new_page()
        for m in MODULES:
            html = OUT / f"_{m['slug']}.html"
            html.write_text(page(m), encoding="utf-8")
            pg.goto(html.as_uri(), wait_until="networkidle")
            pg.wait_for_timeout(1200)          # let the webfont land
            png = OUT / f"thumb-{m['slug']}.png"
            pg.screenshot(path=str(png))
            made.append(png.name)
            print(f"  {png.name}")
        # did Source Serif 4 actually load, or did we silently fall back?
        pg.goto((OUT / "_dealdesk.html").as_uri(), wait_until="networkidle")
        pg.wait_for_timeout(800)
        loaded = pg.evaluate("document.fonts.check('600 62px \"Source Serif 4\"')")
        print(f"\nSource Serif 4 loaded: {loaded}")
        b.close()
    # A silent fallback to Liberation Serif produces cards that look almost
    # right and break the "same person" test. Worth failing the build over.
    if not loaded:
        msg = "Source Serif 4 did not load - cards would ship in a fallback serif"
        if args.strict:
            print(f"ERROR: {msg}", file=sys.stderr); return 1
        print(f"WARNING: {msg}", file=sys.stderr)
    for f in OUT.glob("_*.html"):
        f.unlink()
    print(f"{len(made)} thumbnails -> {OUT}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
