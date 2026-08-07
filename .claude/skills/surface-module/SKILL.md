---
name: surface-module
description: Surface a new or extended Cascadia module across robbinsanalytics.com — case study page, navbar, home page card, family page, OG thumbnail, link check, publish. Run after any module build ships, and after any extension that adds a page.
---

# Surfacing a Cascadia module on the site

A module is not shipped when its build is done. It is shipped when a reader can
find it. Six files carry a module, and they drift apart silently because five of
them are obvious and one is not.

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

Add under `navbar: left: - text: "Projects" menu:`. Order matters — newest and
strongest first, since this menu is how most readers navigate.

### 3 · `index.qmd` — the home page card

Add a `.project-card` under **Featured Case Studies**: `.card-label` domain,
title, status badges (`New`, `Live`, `Playbook`, `Coming Soon`), the one-line
hook, then a `View Case Study` primary button plus outline buttons for each live
page. Only the strongest three or four modules belong here; demote one if needed
rather than letting the section grow without limit.

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
- **Tech Stack chips.** Add anything genuinely new (e.g. `WCAG 2.2 AA`). Do not
  duplicate an existing chip.

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
deliberately skipped, say why.
