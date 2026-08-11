# Portfolio Site — Options Comparison
*Created 2026-06-29. Goal: one site Aaron can point to that links all Cascadia builds (Medical Devices, Pharmacy, future Clothing), each tying together its GitHub repo, explainer, and Power BI report. This is a decision aid — no build started yet.*

---

## The shape of the thing (regardless of tool)
One **hub/landing page** for the Cascadia family (intro + the existing `cascadia_analytics_tech_stack.svg`), then **one case-study page per module** following a repeatable template:

> Problem & business framing → Architecture (the shared Cascadia stack) → Data sources (with citations) → The headline skill (e.g., messy-data cleaning) → The report (screens/video/live) → Links (repo + explainer).

Everything below is just *how* you host and render that.

---

## Decision 1 — What hosts/builds the hub site

| Option | Effort | Control / "data cred" | Cost | Custom domain | Best when |
|---|---|---|---|---|---|
| **Quarto → GitHub Pages** | Low–Med | High | Free | Yes | You want a data-portfolio-native tool; case studies, embeds, notebooks, one-command publish. **Top pick.** |
| **Astro / static → Cloudflare or Netlify Pages** | Med | Highest | Free | Yes | You want maximum design flexibility and modern frontend; willing to do more hand-coding. |
| **MkDocs Material / Docsify → GitHub Pages** | Low | Med–High | Free | Yes | You want a clean docs-style site fast; less "designed," very low maintenance. |
| **Low-code (Notion+super.so, Carrd, Framer)** | Lowest | Low | Free–$ | Yes (paid tiers) | You want online this week and don't care about owning the stack. Reads more "marketing page." |

**Notes**
- **Quarto** is purpose-built for analytics/data-science portfolios: markdown + code, renders polished pages, embeds iframes and images, and `quarto publish gh-pages` ships it. Lives naturally beside your RobbinsAnalytics repos.
- **GitHub Pages vs Cloudflare/Netlify Pages**: all serve the same static output for free. GitHub Pages = simplest, in-repo. Cloudflare/Netlify add nicer custom-domain handling and preview deploys on each commit. You can switch hosts later without redoing the site.
- **Owning it in git** is itself a credibility signal for a BI/analytics role — the portfolio is reproducible, versioned, and public.
- A **custom domain** (e.g., `robbinsanalytics.com`) works with every option here and is worth the ~$12/yr for a job search.

---

## Decision 2 — How each Power BI report appears
You chose to use all four. They're complementary — layer them per build. Durability matters because public Power BI embedding got more fragile in 2026 (see note below).

| Method | Durability | Effort | What it shows | Role on the page |
|---|---|---|---|---|
| **Screenshots** | High (always works) | Low | Final visuals, polish | Baseline — every build has these. Annotated stills of each report page. |
| **Recorded walkthrough (video/GIF)** | High | Med | Interactivity **+ your narration** | The differentiator — proves you can explain data to non-technical people. 60–120s per build. |
| **Live embed (publish-to-web)** | Low (license-tied) | Low–Med | Full interactivity | "Bonus when live" — embed it, but never let it be the *only* thing or the page breaks if the license lapses. |
| **Repo + explainer links** | High | Low | Depth, rigor, reproducibility | Always present — links to the GitHub repo and the explainer doc for reviewers who want to go deep. |

**Recommended layering per case-study page:** lead with 1–2 screenshots → embed the walkthrough video → "View the live report" button (live embed, with screenshots as the visible fallback) → repo + explainer links at the bottom.

### Important 2026 caveat on live embeds
Microsoft now **blocks new Publish-to-Web embed codes by default**; enabling it requires the tenant setting on and a Pro/PPU license, and the public link is tied to your account — it can stop working when a trial/license lapses. You administer your own Entra tenant, so you *can* enable it, but treat live embeds as the perishable layer and keep screenshots + video as the durable record. (An import-mode `.pbix` in each repo is the other durable artifact.)

---

## Recommendation (when you're ready)
**Quarto site on GitHub Pages, custom domain, case-study-per-module template.** Render each Power BI build with screenshots + a short walkthrough video + an optional live embed + repo/explainer links. It's free, versioned, scales as Pharmacy and Clothing land, and reads as a builder's portfolio rather than a brochure.

**Fastest viable alternative** if you want it live in a day and will upgrade later: a single MkDocs Material or Carrd page now, migrate to Quarto once the Cascadia set is built out.

---

## Open questions to settle before scaffolding
1. **Domain**: register one (e.g., `robbinsanalytics.com`) or use the free `robbinsanalytics.github.io`?
2. **One repo or many**: a dedicated `robbinsanalytics.github.io` / `portfolio-site` repo that links out to each build repo (recommended), vs. folding the site into an existing repo.
3. **Identity scope**: Cascadia-branded showcase only, or also a top-level "Aaron Robbins" landing (bio, resume, contact) wrapping the case studies?
4. **Walkthrough format**: silent GIF (autoplay, no audio) vs. narrated video (stronger, but needs a hosting spot — YouTube unlisted or self-hosted MP4).

---
**Source:** [Power BI — Publish to web (Microsoft Learn)](https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-publish-to-web)
