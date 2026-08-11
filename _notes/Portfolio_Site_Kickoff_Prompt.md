# Kickoff Prompt — Portfolio Site (Quarto on GitHub Pages)
*Created 2026-06-29. The single site that links all Cascadia builds together. Decisions locked: Quarto + GitHub Pages, free `robbinsanalytics.github.io` for now (custom domain later), a dedicated site repo that links OUT to each build repo, and a top-level Aaron Robbins landing/identity page wrapping case-study-per-module.*
*Workflow: paste Section 7 into Claude Code (local git/Quarto/Pages). Cowork drafts the page copy (Sections 5–6).*

---

## 1. Goal & decisions
- **One hub** at `https://robbinsanalytics.github.io` showcasing the Cascadia family (Medical Devices, Pharmacy, and a planned Clothing), each case study linking to its own build repo + explainer + Power BI report.
- **Tooling:** Quarto website project, published to GitHub Pages.
- **Repo strategy:** a **dedicated site repo** named **`RobbinsAnalytics.github.io`** (so it serves at the account root URL). It **links out** to the individual build repos (`manufacturing-analytics`, `cascadia-pharmacy-analytics`, …) — it does not contain them.
- **Identity:** top-level **landing page = Aaron Robbins** (headline, short bio, contact/resume/LinkedIn/GitHub), with the Cascadia case studies featured below.
- **Domain:** free `*.github.io` now; structure for a custom domain later (add a `CNAME` file + DNS; no rebuild needed).
- **Free tier only.**

## 2. Repo / site structure
```
RobbinsAnalytics.github.io/
├─ _quarto.yml                  # project: website; navbar; theme; output to docs/ or gh-pages
├─ index.qmd                    # Aaron Robbins landing (identity + featured case studies)
├─ about.qmd                    # fuller bio / resume / contact
├─ cascadia.qmd                 # the Cascadia family concept + shared architecture
├─ projects/
│   ├─ cascadia-medical-devices.qmd
│   ├─ cascadia-pharmacy.qmd
│   └─ cascadia-clothing.qmd    # "coming soon" placeholder
├─ assets/
│   ├─ cascadia_analytics_tech_stack.svg   # reuse existing asset
│   └─ img/                     # screenshots, GIFs per build
├─ styles.scss                  # theme to match Cascadia palette
├─ CNAME                        # added later for custom domain
└─ .github/workflows/publish.yml  # optional: CI publish (or use `quarto publish gh-pages`)
```

## 3. Build & deploy
- Install Quarto (if not present). `quarto create project website .` then adapt to the structure above.
- **Publish:** simplest is `quarto publish gh-pages` (creates/updates the `gh-pages` branch and Pages config). Alternative: render to `/docs` on `main` and set Pages → Deploy from branch → `/docs`. Pick one; document it in the repo README.
- Confirm the site is live at `https://robbinsanalytics.github.io` before handoff back.

## 4. Theme
- Match the Cascadia look (same palette/fonts as the Power BI reports and the existing `cascadia_analytics_tech_stack.svg`). Use a Quarto theme (e.g., `cosmo`/`flatly`) + `styles.scss` overrides for accent colors. Clean, professional, fast.

## 5. Case-study page template (reuse for every build)
Each `projects/*.qmd` follows this skeleton:
1. **Title + one-line hook** (what it proves).
2. **Overview** — 2–3 sentences: domain, the business question, the headline skill.
3. **Business problem / framing.**
4. **Architecture** — the shared Cascadia stack (SQL Server → Fabric medallion → Power BI); embed the tech-stack SVG.
5. **Data sources** — with citations (real public data where applicable).
6. **Headline skill** — e.g., messy/incomplete-data cleaning (Pharmacy), predictive maintenance (Medical Devices).
7. **The report** — screenshots first (durable), then walkthrough video/GIF, then an optional "View live report" embed/button, with screenshots as the visible fallback.
8. **Tech stack** — quick chip list.
9. **Links** — GitHub repo + explainer doc.

## 6. Landing page (`index.qmd`) — content outline
- **Hero:** "Aaron Robbins — Business Intelligence & Analytics Leader." One-line positioning (12+ yrs BI/analytics; healthcare + ecommerce; SQL + Power BI). CTAs: View Work · Resume · LinkedIn · GitHub.
- **The Cascadia portfolio:** 2–3 sentences on the idea — one production-grade analytics architecture, applied across domains to prove it generalizes.
- **Featured case studies:** cards → Cascadia Medical Devices (live), Cascadia Pharmacy (in build), Cascadia Clothing (coming soon).
- **Footer:** contact + links.

> Cowork will draft the actual prose for index/about/cascadia and the first two case studies; Claude Code wires up the Quarto scaffolding and styling.

## 7. READY-TO-PASTE — Claude Code handoff block
```
Create a new public repo RobbinsAnalytics.github.io (NOT in OneDrive; e.g. C:\Projects\RobbinsAnalytics.github.io)
under the RobbinsAnalytics account. Build a Quarto WEBSITE that publishes to GitHub Pages and serves at
https://robbinsanalytics.github.io.

Requirements:
1. Quarto website project with this structure: index.qmd (Aaron Robbins landing/identity), about.qmd,
   cascadia.qmd (Cascadia family + shared architecture), projects/cascadia-medical-devices.qmd,
   projects/cascadia-pharmacy.qmd, projects/cascadia-clothing.qmd (coming-soon placeholder),
   assets/ (copy in cascadia_analytics_tech_stack.svg from the Portfolio Project folder) + assets/img/,
   styles.scss, _quarto.yml with a navbar (Home, About, Cascadia, Projects, GitHub).
2. Clean professional theme (cosmo or flatly) + styles.scss accent colors matching the Cascadia palette.
3. Each projects/*.qmd uses the case-study template from Portfolio_Site_Kickoff_Prompt.md §5
   (Overview → Problem → Architecture → Data → Headline skill → Report [screenshots/video/embed] →
   Tech stack → Links to build repo + explainer). Leave clearly-marked TODO placeholders where
   Cowork-drafted copy and screenshots/video will drop in.
4. The site LINKS OUT to the build repos (manufacturing-analytics, cascadia-pharmacy-analytics);
   it does not vendor them.
5. Publish via `quarto publish gh-pages` (or render to /docs + Pages from branch — your call, document it
   in README). Confirm the live URL works.
6. Add a placeholder CNAME mechanism noted in the README for adding a custom domain later (don't buy one).
7. MIT license, README explaining the site, free tier only.

When the scaffold is live, report the URL back so Cowork can fill in the landing copy and case studies.
```

---
## 8. Note — downstream updates to circle back on (after the site scaffold)
- **Pharmacy kickoff + explainer 03 / Cowork build guide:** add "capture report screenshots + a 60–120s walkthrough video for the portfolio site" to the Pharmacy outputs, and have the `cascadia-pharmacy-analytics` README link back to the site case-study page.
- **Cascadia Medical Devices repo:** same back-link to its case-study page.
- These are small edits; do them once the site structure exists so the links resolve.
