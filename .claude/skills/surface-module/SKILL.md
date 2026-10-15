---
name: surface-module
description: Surface a new or extended Cascadia module across robbinsanalytics.com — case study page, navbar, home page card, family page, OG thumbnail, link check, publish. Run after any module build ships, and after any extension that adds a page.
---

# Surfacing a Cascadia module on the site

A module is not shipped when its build is done. It is shipped when a reader can
find it. Six files carry a module, and they drift apart silently because five of
them are obvious and one is not.

Since reskin phase one (2026-10-14, ADR 0002) the home page and the
case-study index are rendered from one inventory, `data/portfolio.yml`,
through one template. A new module is **one inventory entry plus one
dropdown entry**; no card is hand-written anywhere.

**The one that drifts is `cascadia.qmd`.** When Deal Desk shipped it landed in the
navbar, the home page, its own case-study page and the thumbnail generator — and
was completely absent from the Cascadia family page: no row in the builds table,
no stack pattern, and none of its governance work in the design principles. The
page whose entire job is to explain the standard was the one page that had gone
stale. Check it first, not last.

---

## The six surfaces

Work through all of them. A module that touches five is not finished.

### 1 · `projects/cascadia-<slug>.qmd` — the case study

Usually written during the build. Confirm it has: front-matter `title`,
`subtitle`, `image` (absolute `https://www.robbinsanalytics.com/assets/thumb-<slug>.png`)
and `image-alt`; a `.case-study-header` block; buttons to every live page the
module publishes; Overview, Why This Stack, Architecture, Headline Skill,
Validation, Tech Stack, Disclosure and Links sections.

### 2 · `_quarto.yml` — the navbar

Add under `navbar: left: - text: "Case Studies" menu:`, above the first data
build (the playbooks sit at the top, the process map and the paper at the
bottom, "All case studies" last). Newest build first, since this menu is how
most readers navigate. Every entry in this menu has a row in the inventory
and nothing else does; the two must agree.

### 3 · `data/portfolio.yml` — the inventory (home page and index)

Add one entry. The fields are documented at the top of the file; the ones
that take judgment are:

- `status`, in the site's own words: `Published` for a live build,
  `Complete` for a finished case study with no live page, `Coming Soon` for
  a planned one. `Playbook` and `Preprint` are for the design pieces and the
  paper, not for a module.
- `order`: the position in the family page's Builds & Their Stacks table,
  which is newest first, so a new build takes the order of the first data
  build and every entry below it moves down by one. The card number on the
  index is this position, not a build number.
- `summary`: three lines at card width, no em dashes, no count that goes
  stale. Aaron reads it in the pull request.
- `featured`: **`false` by default.** The home page carries three featured
  builds under "Selected builds", chosen by capability and not by recency,
  with the newest of them first. Today they are Early Warning, Revenue
  Assurance and Matter Ledger. **Whether a new build is featured, and
  which of the three it replaces, is Aaron's call: ask in the report, never
  assume.** The index lists every entry regardless, and "See all N case
  studies" under the featured three counts itself from the inventory.

The home page's Leadership Portfolio (Build by Build, the Operating Charter,
the Validation Playbook, BI Migration) and Beyond the Portfolio are rendered
from the same file by `type`; a module never lands there.

### 4 · `cascadia.qmd` — the family page  ← the one that drifts

Four separate edits, and it is normal to remember the first and forget the rest:

- **The Builds & Their Stacks table.** New row: linked domain, Status, Stack,
  Data, Headline Skill. Newest first.
- **Three Patterns, One Standard.** Assign the module to its pattern —
  lightweight analytical, pragmatic local, or enterprise-BI. If it shares a
  pattern with an existing module, say so and name both; a pattern heading that
  names one module when two exist reads as a one-off rather than a standard.
- **Design Principles.** Only if the module introduces a genuinely new
  governance move. Deal Desk's "the run fails rather than guessing" was a
  sharper claim than anything on the page and sat invisible for weeks. Ask what
  this build does that the others do not, and whether a reader could tell.
- **Tech Stack chips.** Add anything genuinely new (e.g. `dbt Core`). Do not
  duplicate an existing chip. A chip states a fact about the stack, not a claim
  about a result — anything unverified has to say so, the way
  `WCAG 2.2 AA target (unverified)` does.

### 5 · `tools/build_thumbs.py` — the OG card

Add an entry to `MODULES`: `slug`, `data` (the provenance strip — name the real
source), `kicker`, `title`, `line`, `accent`, `motif`, plus `landing=True` or
`muted=True` where they apply.

**Accent colours are fixed slots and are never re-dealt** — a module keeps its
hue everywhere it appears. Never edit the PNGs by hand; CI regenerates all of
them from this list on every build, so a hand-edited image is overwritten.

### 6 · Link check — every module, every time

Repo links rot quietly. `cascadia-pharmacy-analytics` was linked twice from a
live page and had 404'd, unnoticed, because nothing checked.

```bash
for u in $(grep -rhoE "https://github\.com/RobbinsAnalytics/[A-Za-z0-9._-]+" \
           --include="*.qmd" . | sort -u); do
  code=$(curl -s -o /dev/null -w '%{http_code}' -L "$u")
  echo "$code  $u"
done
```

Anything not `200` is either a repo that was never made public or one named
differently. Fix the link or remove it — a 404 on a portfolio page costs more
than a missing link.

---

## Then publish

Use `/publish`. It fetches first, refuses to proceed if the branch is behind,
classifies whitespace noise, stages by name, commits, pushes, and verifies the
live site over HTTP. **Do not improvise a shorter version, and never run
`quarto publish gh-pages` by hand** — the workflow does it, and running both
races them.

## Then verify what a reader sees

Origin-side evidence is not verification. After the deploy lands, load the
family page and the home page at `www.robbinsanalytics.com` and confirm the new
module appears in both. GitHub's CDN caches for roughly ten minutes, so a stale
read shortly after deploying is expected — check the `gh-pages` blob to tell a
caching lag apart from a bad deploy before assuming something failed.

## Report

Say which of the six surfaces changed, which were already correct, what the
link check returned, and what the live pages showed. If a surface was
deliberately skipped, say why. **Ask whether the new build should be
featured on the home page and, if so, which of the current three it
replaces.**
