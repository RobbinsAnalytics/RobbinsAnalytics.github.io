#!/usr/bin/env python3
"""Build the raster icon set from the mark (LOGO.md 4.2).

Rendered through the same Chromium that renders the OG cards and the charts,
for the same reason: one renderer, one result. ImageMagick's built-in MSVG
renderer mishandles the stylesheet in favicon.svg, so nothing here goes near it.

Every icon rasterises from robbins-mark.svg or robbins-mark-reversed.svg — the
plain marks, which carry no prefers-color-scheme block. Rasterising favicon.svg
would bake in whichever palette the headless browser happened to be in.

LOGO.md 2.1: the mark scales by integer factors only. Every size below places
the 16-unit grid at a whole number of pixels per unit; where a platform forces
a canvas that is not a multiple of 16 (apple-touch-icon's 180), the canvas is
padded with the opaque background rather than the mark being scaled to fit.

    python tools/build_icons.py [--out assets/brand]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "assets" / "brand"
_DEFAULT_OUT = BRAND

PAPER = "#FCFCFA"      # LOGO.md 3.2
SPRUCE = "#16241D"

# name, canvas px, mark px (integer multiple of 16), background, source mark
ICONS = [
    ("favicon-32.png",       32,  32, None,   "robbins-mark.svg"),
    ("favicon-16.png",       16,  16, None,   "robbins-mark.svg"),
    ("apple-touch-icon.png", 180, 128, PAPER,  "robbins-mark.svg"),
    ("icon-512.png",         512, 384, PAPER,  "robbins-mark.svg"),
    ("avatar-512.png",       512, 384, PAPER,  "robbins-mark.svg"),
    ("avatar-512-dark.png",  512, 384, SPRUCE, "robbins-mark-reversed.svg"),
]


def page(svg, canvas, mark, bg):
    fill = f"background:{bg}" if bg else "background:transparent"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0 }}
  html, body {{ width:{canvas}px; height:{canvas}px; {fill} }}
  body {{ display:flex; align-items:center; justify-content:center }}
  svg {{ width:{mark}px; height:{mark}px; display:block;
         shape-rendering: crispEdges }}
</style></head><body>{svg}</body></html>"""


def main():
    ap = argparse.ArgumentParser(description="Build the Robbins Analytics icons.")
    ap.add_argument("--out", default=str(_DEFAULT_OUT))
    args = ap.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright
    made = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for name, canvas, mark, bg, src in ICONS:
            if mark % 16:
                print(f"ERROR: {name} draws the mark at {mark}px, not a multiple "
                      f"of 16 (LOGO.md 2.1)", file=sys.stderr)
                return 1
            svg = (BRAND / src).read_text(encoding="utf-8")
            html = out / f"_{name}.html"
            html.write_text(page(svg, canvas, mark, bg), encoding="utf-8")
            pg = b.new_context(viewport={"width": canvas, "height": canvas},
                               device_scale_factor=1).new_page()
            pg.goto(html.as_uri(), wait_until="load")
            pg.screenshot(path=str(out / name),
                          omit_background=bg is None)
            pg.close()
            html.unlink()
            made.append(name)
            print(f"  {name:<22} {canvas}px canvas, mark at {mark}px "
                  f"({mark // 16}x grid), {bg or 'transparent'}")
        b.close()
    print(f"{len(made)} icons -> {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
