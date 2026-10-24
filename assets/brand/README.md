# Ribbon web identity · 2026-10-24

Approved: **A**, Ribbon beside the existing Inter Tight 600 / Fraunces italic
wordmark. Keep the period and match it to Analytics (`#1f6b63` on paper).
The footer and reversed exports use `#83c7bc` for both Analytics and its period
so they remain readable on ink. The website name stays Robbins Analytics.

## Assets and regeneration

| Use | Files |
| --- | --- |
| Transparent symbol | `robbins-mark.svg`, `robbins-mark-reversed.svg`; matching PNGs |
| Transparent horizontal | `robbins-lockup-primary.svg`, `robbins-lockup-reversed.svg`; matching PNGs |
| Transparent stacked | `robbins-lockup-stacked.svg`, `robbins-lockup-stacked-reversed.svg`; matching PNGs |
| Opaque lockups | PNG variants ending `-on-paper` and `-on-ink` |
| Browser icon | `favicon.svg`, `favicon-16.png`, `favicon-32.png` |
| Home screen / app export | Opaque `apple-touch-icon.png` (180), `icon-512.png` (512) |
| Avatar exports | Opaque `avatar-512.png`, `avatar-512-dark.png` |

SVGs contain real paths, including outlined exported wordmarks, without embedded
PNGs, SVG text or remote fonts. The website keeps readable live text and a
decorative image inside one home link. Preserve proportions; do not stretch.
At normal header widths the symbol is 60 × 51 CSS px with 12px to the text;
the bar is at least 76px tall. Below 371px the symbol is 46px wide, the type
18px and the gap 8px; below 341px the symbol is 32px and the gap 6px.
Stacked assets are supplied for other placements, not
used to increase the website header height.

`src/ribbon-selected.png` preserves the selected reference byte for byte
(SHA-256 in `src/ribbon-trace-receipt.json`). `src/ribbon-master.svg` traces
its opaque bird contours. It excludes raster glow and color noise and uses
flat representative colors. Polygon simplification is at most 0.85 original
pixels, less than 0.1 CSS pixel at the header width; the receipt's contour
overlap is a conversion check, not evidence of owner approval or a visual audit.
The split tail, separate feathers, beak and proportions are retained.

Reversed artwork changes color only. The small-icon cut adds a dark rounded
tile and keeps the same bird paths. Fine gaps naturally soften at 16px; no
replacement symbol or shortened beak is introduced. Lime is a decorative
accent; the dark body and teal feather carry the recognizable shape. No claim
is made that each colored region independently meets a contrast threshold.
Header accent text/period measure 5.41:1 on paper `#efeee9`; ink text 14.64:1.
The reversed accent measures over 8:1 on ink `#0f1f1e`.

Regenerate vectors with `python tools/build_ribbon_assets.py` (fonttools and
uharfbuzz). The pinned source fonts and their OFL licenses are in
`src/ribbon-fonts`, obtained from the [Google Fonts Inter Tight source](https://github.com/google/fonts/tree/main/ofl/intertight)
and [Fraunces source](https://github.com/google/fonts/tree/main/ofl/fraunces).
Source hashes are in `src/ribbon-asset-manifest.json`.
Regenerate PNGs with `python tools/build_icons.py --out assets/brand`
(Playwright). Normal CI consumes the committed vectors and needs no fonts for
these exports. The optional one-time contour converter is `src/trace_ribbon.py`.

## Placement inventory and boundaries

| Surface | Owning source and output |
| --- | --- |
| All Quarto headers | `_quarto.yml`, `felix.scss`; no separate Quarto logo link; live site name stays accessible |
| All footers | `tools/build_footer.py`, `felix.scss`; generated `_generated/footer.html` |
| Browser / home-screen links | `_quarto.yml`; generated page head links, favicon SVG/16/32 and Apple icon |
| Other exported brand assets | All files in the asset table; no site web-app manifest reference exists |
| Social cards | `tools/build_thumbs.py` reads the shared SVG into 18 existing cards; page titles, motifs, colors, source strips and image URLs remain page-specific |
| Open Graph / Twitter | `_quarto.yml` enables metadata; each existing `image:` front matter and redirect stub retains its chosen preview; pages without an image are not assigned a generic logo |
| Redirects | `projects/cascadia-semiconductors.html`, `projects/cascadia-early-warning.html`, `projects/cascadia-validation-playbook.html`, `cascadia-semiconductors/*.html`; destinations and existing preview URLs preserved |
| Structured data | No Organization / JSON-LD logo reference found in source or generated representative pages; none added |
| Historical assets | `archive/pre-ribbon-20261024/` holds all 19 previous brand files byte for byte, including their old source generator; no active reference uses them |

Linked deployments are separate repository sites even where their URL shares
the custom domain. Their headers, icons and social assets are **not** changed:
Build by Build, Claim Integrity, Early Warning, Validation Playbook, Finance,
Revenue Assurance, Fee Examiner, Matter Ledger, Control Tower, Deal Desk,
Staffing, Pharmacy, Medical Devices, Clothing and BI Migration. Local case-study
wrappers receive this site's chrome; their project destinations do not.

The original exploration directory, Flowing refinements, earlier header
comparison worktree and private review pages remain preserved. The new wordmark
decision does not rewrite the shared Cascadia standards repository or document
identity of separately maintained projects.

## Review, publication and rollback

Run `python tools/check_brand.py --rendered` after rendering. Candidate CI
checks links, accessibility regressions and the seven representative pages at
390 / 414 / 768 / 1440px. Refresh changed baselines only from that run's own
screenshots; Windows previews are not valid CI baselines. Green automation is
regression prevention, not proof of WCAG conformance or physical-phone testing.

The publish skill stops at the green pull request: the owner merges in GitHub.
The publish workflow then checks CNAME, the deployed commit in `build.txt`,
asset URLs and generated sharing metadata, plus its existing live sweeps.
Before that merge, deployed production verification is pending.

Rollback is a new pull request reverting the Ribbon implementation and its
baseline follow-up together; merge through the same candidate process. The
pre-Ribbon source commit is `e7909e9`. Do not publish locally or force-push
`main`/`gh-pages`. The archive is an additional artwork recovery copy.

Sharing services may cache the previous image at unchanged URLs. A verified
asset response does not prove that LinkedIn, Slack, X or iMessage has refreshed
its preview. Service-side inspection/refetch tools can refresh supported
services; existing messages may retain their original card. No direct preview
test on those services is implied by generated metadata checks.
