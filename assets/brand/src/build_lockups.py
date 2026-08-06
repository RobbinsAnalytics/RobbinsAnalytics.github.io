#!/usr/bin/env python3
"""Cut the four Robbins Analytics lockups from LOGO.md.

Everything here is derived, not typed in. The only authored constants are the
two ligature offsets (LOGO.md 1.4, re-cut against Source Serif 4 on 2026-08-05)
and the ANALYTICS cap ratio; every dimension below comes out of LOGO.md 1.2 as
a multiple of the wordmark cap height C, and the ANALYTICS tracking is solved,
never set (LOGO.md 1.3).

Shipped files are outlined paths (LOGO.md 1.5). The live-text masters written
alongside them are the editable originals and are not what the site loads.

    python assets/brand/src/build_lockups.py

Fonts: Source Serif 4 4.005 ships in this folder under the OFL. Segoe UI is a
Windows system font, read from C:\\Windows\\Fonts at build time; LOGO.md 4.3
requires it for the sub-line and 1.5 requires outlines, so the built artwork
carries Segoe UI outlines and this script only runs on Windows.
"""

import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen

HERE = Path(__file__).resolve().parent
BRAND = HERE.parent

SS4 = HERE / "SourceSerif4-Regular.ttf"
SEGOE = Path(r"C:\Windows\Fonts\segoeui.ttf")

# --- authored constants ------------------------------------------------------
# LOGO.md 1.4. Re-derived 2026-08-05 against Source Serif 4 4.005; the previous
# -0.14 / -0.13 were measured in Georgia. Both reproduce the approved Georgia
# join ratio (the fused stroke is 1.7x a single stem, not 1.0x); the reversed
# cut carries 0.01 less because light-on-dark optically fattens the strokes and
# so reads as fused at a smaller offset.
LIG = {"light": -0.16, "reversed": -0.15}

C = 100.0            # wordmark cap height, in output units. Everything scales.
ANALYTICS_CAP = 0.42 * C   # chosen so the solved tracking lands near 0.2 em

# --- LOGO.md 1.2, derived ----------------------------------------------------
TICK_W = 0.13 * C
TICK_GAP = 3 * TICK_W
CLEAR = 1.0 * C
SUB_GAP = 0.25 * C   # Robbins baseline -> ANALYTICS cap line

# --- LOGO.md 3.2 -------------------------------------------------------------
PALETTE = {
    "light": dict(word="#232B27", sub="#5B6660", tick="#1E7A4C",
                  ctx="#828E88", base="#232B27", bg="#FCFCFA"),
    "reversed": dict(word="#FCFCFA", sub="#9AA6A0", tick="#65A583",
                     ctx="#67726C", base="#9AA6A0", bg="#16241D"),
}

# LOGO.md 2.1 — the mark, on its 16-unit integer grid.
MARK = [("ctx", 1, 8, 4, 5), ("tick", 6, 3, 4, 10),
        ("ctx", 11, 10, 4, 3), ("base", 0, 13, 16, 2)]
MARK_UNIT = 9        # output units per mark unit; integer keeps every edge whole


class Face:
    def __init__(self, path):
        self.tt = TTFont(str(path))
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        self.cap = self.tt["OS/2"].sCapHeight
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
        self.version = self.tt["name"].getDebugName(5)

    def shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        # Real GPOS pair kerning. Ligature substitution stays off: the bb fusion
        # is ours and hand-set, and no font feature may be allowed to move it.
        hb.shape(self.hb, buf, {"kern": True, "liga": False})
        return [(self.order[i.codepoint], p.x_advance, p.x_offset)
                for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def draw_word(face, text, size, baseline_y, x0=0.0,
              lig_em=0.0, lig_after=None, track=0.0):
    """Outline `text` into one SVG path. Returns (d, ink_bounds).

    size        output units per em
    baseline_y  y of the baseline in output space (y grows downward)
    lig_em      extra offset applied after glyph index `lig_after`
    track       extra advance after every glyph except the last
    """
    s = size / face.upem
    pen = SVGPathPen(face.gs)
    bounds = BoundsPen(face.gs)
    shaped = face.shape(text)
    x = x0
    for i, (gname, adv, xoff) in enumerate(shaped):
        dx = x + (xoff * s)
        # (s, 0, 0, -s, dx, baseline_y): scale, flip y to SVG's downward axis,
        # then place. Flipping per glyph is the same affine as flipping the
        # group, and it keeps every contour in a single path so the fused bb
        # unions under fill-rule="nonzero" instead of being two stacked shapes.
        m = (s, 0, 0, -s, dx, baseline_y)
        face.gs[gname].draw(TransformPen(pen, m))
        face.gs[gname].draw(TransformPen(bounds, m))
        x += adv * s
        if lig_after is not None and i == lig_after:
            x += lig_em * size
        if i < len(shaped) - 1:
            x += track
    return pen.getCommands(), bounds.bounds


def word_extent(face, text, size, **kw):
    _, b = draw_word(face, text, size, 0.0, **kw)
    return b


def solve_tracking(serif, sans, lig_em, cap_px):
    """LOGO.md 1.3 — ANALYTICS is tracked until its right ink edge lands on
    the right ink edge of Robbins. The tracking is the output.

    Both words are placed with their left ink edge at the same x, so the two
    lines share one measure. Linear in `track`, so two probes solve it exactly.
    """
    rb = word_extent(serif, "Robbins", cap_px, lig_em=lig_em, lig_after=2)
    target = rb[2] - rb[0]                       # Robbins ink width

    size = ANALYTICS_CAP / (sans.cap / sans.upem)
    w0 = word_extent(sans, "ANALYTICS", size, track=0.0)
    w1 = word_extent(sans, "ANALYTICS", size, track=1.0)
    span0, span1 = w0[2] - w0[0], w1[2] - w1[0]
    track = (target - span0) / (span1 - span0)   # 8 gaps, linear in track
    return track, size, target


def svg_open(w, h, title, extra=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {w:.2f} {h:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'role="img" aria-labelledby="ra-title"{extra}>\n'
            f'  <title id="ra-title">{title}</title>\n')


def mark_rects(pal, ox, oy, unit):
    out = []
    for role, x, y, w, h in MARK:
        out.append(f'  <rect x="{ox + x*unit:.0f}" y="{oy + y*unit:.0f}" '
                   f'width="{w*unit:.0f}" height="{h*unit:.0f}" '
                   f'fill="{pal[role]}"/>')
    return "\n".join(out)


def build_primary(serif, sans, cut):
    pal = PALETTE[cut]
    lig = LIG[cut]
    track, sub_size, measure = solve_tracking(serif, sans, lig, C)

    cap_top = CLEAR
    base_y = cap_top + C
    sub_cap = base_y + SUB_GAP
    sub_base = sub_cap + ANALYTICS_CAP

    tick_x = CLEAR
    word_x = tick_x + TICK_W + TICK_GAP

    rb = word_extent(serif, "Robbins", C, lig_em=lig, lig_after=2)
    d_word, _ = draw_word(serif, "Robbins", C, base_y, x0=word_x - rb[0],
                          lig_em=lig, lig_after=2)
    sb = word_extent(sans, "ANALYTICS", sub_size, track=track)
    d_sub, _ = draw_word(sans, "ANALYTICS", sub_size, sub_base,
                         x0=word_x - sb[0], track=track)

    w = word_x + measure + CLEAR
    h = sub_base + CLEAR
    body = (
        f'  <rect x="{tick_x:.2f}" y="{cap_top:.2f}" width="{TICK_W:.2f}" '
        f'height="{sub_base - cap_top:.2f}" fill="{pal["tick"]}"/>\n'
        f'  <path fill="{pal["word"]}" fill-rule="nonzero" d="{d_word}"/>\n'
        f'  <path fill="{pal["sub"]}" fill-rule="nonzero" d="{d_sub}"/>\n'
    )
    return svg_open(w, h, "Robbins Analytics") + body + "</svg>\n", track, sub_size


def build_stacked(serif, sans, cut):
    pal = PALETTE[cut]
    lig = LIG[cut]
    track, sub_size, measure = solve_tracking(serif, sans, lig, C)

    mark_w = 16 * MARK_UNIT
    mark_gap = 0.5 * C
    cap_top = CLEAR + mark_w + mark_gap
    base_y = cap_top + C
    sub_cap = base_y + SUB_GAP
    sub_base = sub_cap + ANALYTICS_CAP

    content_w = max(measure, mark_w)
    w = content_w + 2 * CLEAR
    h = sub_base + CLEAR

    word_x = (w - measure) / 2
    rb = word_extent(serif, "Robbins", C, lig_em=lig, lig_after=2)
    d_word, _ = draw_word(serif, "Robbins", C, base_y, x0=word_x - rb[0],
                          lig_em=lig, lig_after=2)
    sb = word_extent(sans, "ANALYTICS", sub_size, track=track)
    d_sub, _ = draw_word(sans, "ANALYTICS", sub_size, sub_base,
                         x0=word_x - sb[0], track=track)

    mx = round((w - mark_w) / 2)
    body = (mark_rects(pal, mx, round(CLEAR), MARK_UNIT) + "\n"
            f'  <path fill="{pal["word"]}" fill-rule="nonzero" d="{d_word}"/>\n'
            f'  <path fill="{pal["sub"]}" fill-rule="nonzero" d="{d_sub}"/>\n')
    return svg_open(w, h, "Robbins Analytics") + body + "</svg>\n"


def master(cut, track, sub_size, stacked=False):
    """Editable original: live <text>, never shipped (LOGO.md 1.5)."""
    pal = PALETTE[cut]
    ser_size = C / (0.670)
    cap_top = CLEAR + (16 * MARK_UNIT + 0.5 * C if stacked else 0)
    base_y = cap_top + C
    sub_base = base_y + SUB_GAP + ANALYTICS_CAP
    x = CLEAR + (0 if stacked else TICK_W + TICK_GAP)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="400" '
        f'role="img" aria-labelledby="m-title">\n'
        f'  <title id="m-title">Robbins Analytics — editable master</title>\n'
        f'  <!-- LOGO.md 1.5: this file keeps live text and is the editable\n'
        f'       original. The shipped lockup is the outlined derivative built\n'
        f'       by build_lockups.py. Do not link this file from the site.\n'
        f'       Ligature: the bb offset cannot be expressed in live text; it\n'
        f'       is applied by the build. -->\n'
        f'  <text x="{x:.2f}" y="{base_y:.2f}" fill="{pal["word"]}"\n'
        f'        font-family="Source Serif 4" font-size="{ser_size:.2f}">Robbins</text>\n'
        f'  <text x="{x:.2f}" y="{sub_base:.2f}" fill="{pal["sub"]}"\n'
        f'        font-family="Segoe UI" font-size="{sub_size:.2f}"\n'
        f'        letter-spacing="{track:.3f}">ANALYTICS</text>\n'
        f'</svg>\n'
    )


def main():
    if not SEGOE.exists():
        sys.exit("Segoe UI not found — LOGO.md 4.3 requires it for the sub-line.")
    serif, sans = Face(SS4), Face(SEGOE)
    print(f"Source Serif 4 : {serif.version}  cap {serif.cap}/{serif.upem}")
    print(f"Segoe UI       : {sans.version}  cap {sans.cap}/{sans.upem}")

    for cut, name in (("light", "primary"), ("reversed", "reversed")):
        svg, track, sub_size = build_primary(serif, sans, cut)
        (BRAND / f"robbins-lockup-{name}.svg").write_text(svg, encoding="utf-8")
        (HERE / f"master-{name}.svg").write_text(
            master(cut, track, sub_size), encoding="utf-8")
        print(f"  {name:<9} lig {LIG[cut]:+.2f} em · ANALYTICS "
              f"{sub_size:.2f}u/em, tracking {track:.3f}u "
              f"({track/sub_size:.4f} em)")

    for cut, name in (("light", "stacked"), ("reversed", "stacked-reversed")):
        svg = build_stacked(serif, sans, cut)
        (BRAND / f"robbins-lockup-{name}.svg").write_text(svg, encoding="utf-8")
    _, track, sub_size = build_primary(serif, sans, "light")
    (HERE / "master-stacked.svg").write_text(
        master("light", track, sub_size, stacked=True), encoding="utf-8")
    print("  stacked, stacked-reversed")


if __name__ == "__main__":
    main()
