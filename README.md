# RobbinsAnalytics.github.io

Aaron Robbins — Business Intelligence & Analytics portfolio site.

**Live URL:** <https://www.robbinsanalytics.com>

Built with [Quarto](https://quarto.org/) and published to GitHub Pages.

---

## Site Structure

```
RobbinsAnalytics.github.io/
├─ _quarto.yml                  # Quarto website config (cosmo theme + Cascadia palette)
├─ index.qmd                    # Landing page — Aaron Robbins identity + featured case studies
├─ about.qmd                    # Bio, skills, resume, contact
├─ cascadia/                    # Four-page Cascadia operating system and scoped assets
├─ cascadia.html                # Redirect from the former single-page URL
├─ projects/
│   ├─ cascadia-medical-devices.qmd   # Manufacturing case study
│   ├─ cascadia-pharmacy.qmd          # Healthcare/pharmacy case study
│   └─ cascadia-clothing.qmd          # Retail placeholder (coming soon)
├─ assets/
│   ├─ cascadia_analytics_tech_stack.svg   # Architecture diagram
│   └─ img/                                # Screenshots, GIFs per case study
└─ styles.scss                  # SCSS overrides — Cascadia color palette
```

This repo contains the portfolio shell and the four-page Cascadia operating-system presentation. The analytical build repos linked from those pages are separate:

| Project | Repo |
|---|---|
| Cascadia Medical Devices | [manufacturing-analytics](https://github.com/RobbinsAnalytics/manufacturing-analytics) |
| Cascadia Pharmacy | [cascadia-pharmacy-analytics](https://github.com/RobbinsAnalytics/cascadia-pharmacy-analytics) |

---

## Publish Workflow

**`.github/workflows/publish.yml` owns deployment. Merging a pull request into `main` is the deploy; `main` takes no direct push.**

- Source lives on `main` (what you're reading now).
- Every pull request runs `.github/workflows/candidate.yml`, which renders the branch inside the runner and runs the link, accessibility and visual checks against it; a ruleset on `main` requires that check and refuses direct pushes.
- Every merge to `main` triggers the publish workflow, which renders the site and pushes the result to the `gh-pages` branch.
- GitHub Pages serves that branch at the custom domain.
- The workflow then verifies itself against the live site: it asserts the Pages `cname` survived, polls `build.txt` until the edge serves the pushed commit, and checks the live pages and redirects. A miss fails the run.

### To publish a new version

Open a pull request and merge it — the merge is the whole deploy. In a Claude Code session, use `/publish`, which classifies line-ending noise, stages by name, commits, pushes the branch and opens or updates the pull request; the merge is done by hand in the GitHub interface after the candidate check is green.

> **Do not run `quarto publish gh-pages` by hand.** It races the workflow and can push a stale local build over a fresh one. The workflow is the only thing that should write `gh-pages`. This README instructed the manual command until 2026-08-25; that instruction was the hazard, not a shortcut.

### Local preview

```powershell
quarto preview
```

---

## Custom Domain

**Live at `www.robbinsanalytics.com`**, set by the `CNAME` file in the repo root.

`quarto publish gh-pages` rebuilds the `gh-pages` branch and force-pushes it, so any `CNAME` GitHub writes to that branch is destroyed on the next deploy — the custom domain silently clears and the site falls back to the `github.io` address. `_quarto.yml` lists `CNAME` under `resources:` so Quarto copies it into `_site` on every build, and the workflow asserts the Pages `cname` after deploying. Do not remove either control.

---

## Contributing / Updating

- **Copy updates:** Edit the `.qmd` files, commit on a branch, open a pull request, merge.
- **Screenshots / video:** Drop files into `assets/img/`, update the relevant `projects/*.qmd`, commit on a branch, open a pull request, merge.
- **New case study:** Copy a `projects/*.qmd` template, add a navbar entry in `_quarto.yml`, add a `MODULES` entry in `tools/build_thumbs.py` for its OG card, then push. The `surface-module` skill walks the full set of edits.

See `CLAUDE.md` for the facts about this repo that are not inferable from the code.

---

## License

MIT — see [LICENSE](LICENSE).

Data used in linked case studies (CMS Medicare Part D, CDC VaxView) is U.S. federal public-domain data. See individual build repo READMEs for full attribution.
