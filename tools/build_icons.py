#!/usr/bin/env python3
"""Build Ribbon raster icons and lockups from checked-in vector assets.

Rendered through the same Chromium that renders the OG cards and charts.

The same bird paths serve each size. Favicons use the explicit contrast tile;
the old bar mark's integer-grid and crispEdges rules do not apply to curves.

    python tools/build_icons.py [--out assets/brand]
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "assets" / "brand"
_DEFAULT_OUT = BRAND

PAPER = "#efeee9"
SPRUCE = "#0f1f1e"

# name, canvas px, artwork box px, background, source SVG
ICONS = [
    ("favicon-32.png",       32,  32, None,   "favicon.svg"),
    ("favicon-16.png",       16,  16, None,   "favicon.svg"),
    ("apple-touch-icon.png", 180, 180, SPRUCE,"favicon.svg"),
    ("icon-512.png",         512, 512, SPRUCE,"favicon.svg"),
    ("avatar-512.png",       512, 384, PAPER,  "robbins-mark.svg"),
    ("avatar-512-dark.png",  512, 384, SPRUCE, "robbins-mark-reversed.svg"),
]


def page(svg, canvas, mark, bg):
    fill = f"background:{bg}" if bg else "background:transparent"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0 }}
  html, body {{ width:{canvas}px; height:{canvas}px; {fill} }}
  body {{ display:flex; align-items:center; justify-content:center }}
  svg {{ width:{mark}px; height:{mark}px; display:block }}
</style></head><body>{svg}</body></html>"""


def export_lockups(browser, out):
    made = []
    sources = [
        ("robbins-lockup-primary", None), ("robbins-lockup-reversed", None),
        ("robbins-lockup-stacked", None), ("robbins-lockup-stacked-reversed", None),
        ("robbins-lockup-primary", PAPER), ("robbins-lockup-reversed", SPRUCE),
        ("robbins-lockup-stacked", PAPER), ("robbins-lockup-stacked-reversed", SPRUCE),
        ("robbins-mark", None), ("robbins-mark-reversed", None),
    ]
    for stem, bg in sources:
        svg = (BRAND / (stem + '.svg')).read_text(encoding='utf-8')
        _, _, width, height = map(float, ET.fromstring(svg).attrib['viewBox'].split())
        width, height = round(width * 2), round(height * 2)
        suffix = '-on-paper' if bg == PAPER else '-on-ink' if bg else ''
        name = stem + suffix + '.png'
        html = out / ('_' + name + '.html')
        html.write_text(f'<!doctype html><html><meta charset="utf-8"><style>*{{margin:0}}html,body{{width:{width}px;height:{height}px;background:{bg or "transparent"}}}svg{{display:block;width:100%;height:100%}}</style>{svg}</html>',encoding='utf-8')
        pg = browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
        pg.goto(html.as_uri(),wait_until='load')
        pg.screenshot(path=str(out/name),omit_background=bg is None)
        pg.close();html.unlink();made.append(name)
        print(f'  {name} {width}x{height}')
    return made


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
                  f"{bg or 'transparent'}")
        made.extend(export_lockups(b, out))
        b.close()
    print(f"{len(made)} raster brand assets -> {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
