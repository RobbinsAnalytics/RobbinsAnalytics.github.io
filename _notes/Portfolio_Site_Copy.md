# Portfolio Site — Drafted Copy (A2)
*Created 2026-06-29. Ready-to-paste copy for the TODO placeholders in `RobbinsAnalytics.github.io`. Each section maps to a `.qmd` file. Paste into the matching `{.todo-block}`, then run `quarto publish gh-pages --no-browser --no-prompt`.*

> **Fill-ins / decisions (settled 2026-06-29):** LinkedIn — include it (paste the actual URL into https://www.linkedin.com/in/aaron-robbins-6b25a2136/). Email — **keep private**; no public email address on the site (add a contact form later if desired). Résumé — **omit for now** (no résumé button/link). GitHub org URL = `https://github.com/RobbinsAnalytics`. Pharmacy `[VERIFY: …]` figures — confirm against the built report's real CMS numbers before publishing; do not publish unverified dollar amounts.

---

## index.qmd

### Hero
**Aaron Robbins**
*Business Intelligence & Analytics Leader*

12+ years turning messy data into decisions leaders trust — across healthcare and ecommerce. I design the full stack: SQL data models, Microsoft Fabric pipelines, and Power BI reporting that non-technical teams actually use.

Buttons: **View Work** (#projects) · **LinkedIn** (https://www.linkedin.com/in/aaron-robbins-6b25a2136/) · **GitHub** (https://github.com/RobbinsAnalytics)
*(No résumé button for now; no public email.)*

### The Cascadia portfolio (intro blurb)
Cascadia is a family of end-to-end analytics builds that share one production-grade architecture — SQL Server → Microsoft Fabric medallion lakehouse → Power BI — applied across different industries. The point: a strong data platform pattern generalizes. Same rigor, different domain.

### Project cards
**Cascadia Medical Devices** — *Manufacturing analytics & predictive maintenance*
A dimensional model over 5.9M production events plus real NASA turbofan sensor data, tracing a root-cause story from station degradation to on-time delivery. **Status: Live**

**Cascadia Pharmacy** — *Pharmacy growth analytics on real public data*
GLP-1 spending trends (CMS Medicare Part D) and adult immunization coverage (CDC), with a messy/incomplete-data cleaning showcase. **Status: In build**

**Cascadia Clothing** — *Retail & ecommerce analytics*
Demand, merchandising, and fulfillment analytics for a retail apparel scenario. **Status: Coming soon**

---

## about.qmd

### Bio
I'm a business intelligence and analytics leader with 12+ years building the systems that turn raw, messy data into decisions teams trust. Most recently I led BI and analytics programs at Philips Healthcare, where I built the single source of truth and self-service Power BI reporting across a global manufacturing operation — ten factories on three continents. Before that I led business intelligence for Lowe's ecommerce arm, working high-volume commercial and operational data.

My core strength is the full analytics stack: modeling data in SQL, moving it through governed pipelines, and delivering it in Power BI in a way non-technical stakeholders can act on. I care as much about data governance and trustworthiness as I do about the final dashboard — a report is only as good as the data behind it.

This site is where I build in the open. The Cascadia projects are real, reproducible analytics stacks I've built end to end, with the code public on GitHub.

### Skills
- **BI & visualization:** Power BI (data modeling, DAX, Power Query/M), Tableau, advanced Excel
- **Data & modeling:** SQL Server, dimensional/star-schema modeling, data governance, Microsoft Fabric (medallion lakehouse, semantic models)
- **Domains:** healthcare (manufacturing, quality, pharmacy/public-health data), ecommerce & retail
- **Ways of working:** stakeholder management, turning complex data into simple insights, self-service enablement

### Contact
LinkedIn: https://www.linkedin.com/in/aaron-robbins-6b25a2136/ · GitHub: https://github.com/RobbinsAnalytics
*(Email kept private for now — no public address; a contact form can be added later.)*

---

## cascadia.qmd

### Architecture overview (above the embedded SVG)
Every Cascadia build runs on the same modern Microsoft data stack, end to end:

1. **Source (SQL Server).** A relational, star-schema-ready operational database — the system of record. Dimensions and facts, a date dimension, surrogate keys, loaded reproducibly from source files.
2. **Pipeline (Microsoft Fabric medallion lakehouse).** Bronze (raw) → Silver (cleaned/conformed) → Gold (modeled) layers, so the path from raw data to trustworthy tables is explicit and auditable.
3. **Semantic model & reporting (Power BI).** A governed semantic model with a dedicated measures layer and clean relationships, surfaced in focused reports designed for non-technical audiences.

The value of doing it as a family is repeatability: once the pattern is proven on one domain, standing up the next is fast and consistent. Cascadia Medical Devices proved the pattern on manufacturing; Cascadia Pharmacy applies it to real public healthcare data; Cascadia Clothing extends it to retail.

---

## projects/cascadia-medical-devices.qmd

**Overview.** A full analytics stack for a fictional 3-line medical-device manufacturer, built on ~5.9M synthetic production events across 29 months, paired with real NASA C-MAPSS turbofan run-to-failure sensor data for predictive maintenance. It demonstrates dimensional modeling at scale, a medallion pipeline, and root-cause operational analytics.

**Business problem.** Manufacturing leaders couldn't see why on-time delivery was slipping on certain product lines. The data existed but was fragmented across systems with no single, trusted view.

**Architecture.** SQL Server (`CascadiaMES`: star schema — 4 fact tables, 8 dimensions, `dim_date`, ~5.9M rows, plus a separate schema for the NASA sensor data) → Microsoft Fabric medallion lakehouse (Bronze→Silver→Gold) → Direct Lake semantic model → Power BI. Reproducible build via PowerShell; DP-600-aligned.

**Data sources.** Synthetic MES data from a deterministic generator (seed-controlled, fully reproducible) + real NASA C-MAPSS Turbofan Engine Degradation dataset (FD001–FD004; 265K cycle rows). NASA data cited and disclosed.

**Headline skill — root-cause analytics & predictive maintenance.** The dataset carries an engineered, discoverable story: a single station's cycle time drifts up (≈58→69s), dragging First Pass Yield down on one line (≈95.5%→90.2%) and on-time-in-full delivery down on the affected product (≈92%→69%) — while control lines stay flat. The reporting isolates the root cause rather than just showing the symptom. The NASA layer adds reliability/remaining-useful-life analysis.

**The report.** `[TODO: screenshots]` → `[TODO: walkthrough video]` → `[TODO: live embed or "view report" button]`.

**Tech stack.** SQL Server · Microsoft Fabric · Power BI · Python (data generation) · Git.

**Links.** Repo: https://github.com/RobbinsAnalytics/manufacturing-analytics · Build explainer in the repo `docs/`.

---

## projects/cascadia-pharmacy.qmd

**Overview.** A pharmacy-growth analytics stack built on real public data — CMS Medicare Part D drug spending and CDC adult immunization coverage — applying the Cascadia architecture to healthcare. It's also a deliberate showcase of cleaning messy, incomplete real-world data.

**Business problem.** Two of the biggest growth areas in retail pharmacy are GLP-1 medications and immunization services. Both questions — where is GLP-1 spend going, and where are the immunization coverage gaps — live in public datasets that are real, valuable, and genuinely messy.

**Architecture.** SQL Server (`CascadiaRx`: star schema — 5 dimensions, 2 fact tables, `dim_date`) → Microsoft Fabric medallion lakehouse → Power BI semantic model + report. Same pattern as Cascadia Medical Devices.

**Data sources.** CMS Medicare Part D Spending by Drug (annual) and CDC VaxView (FluVaxView / RSVVaxView / COVIDVaxView) adult coverage by state and season. Both real, public, and cited.

**Headline skill — cleaning messy & incomplete data.** Real government data isn't clean: CMS suppresses small-cell counts (blanks/asterisks), spend arrives as currency strings, drug names vary in casing, and CDC suppresses or flags unstable estimates for small samples. The pipeline preserves that reality and handles it honestly — suppressed values are flagged, never silently zero-filled — and the report surfaces a "suppressed records" counter so the audience understands why a national total doesn't equal the sum of states.

**Key findings.**
- GLP-1 medications are the standout growth story in Medicare Part D: `[VERIFY: class spend grew from ~$X to ~$Y over Z years]`, led by `[VERIFY: Ozempic / Mounjaro figures]`. Both volume (beneficiaries) and cost-per-beneficiary are rising — not just price.
- Adult immunization coverage varies widely by state — `[VERIFY: ~N-point spread top to bottom]` — which maps directly to a pharmacy-access growth opportunity.
> `[VERIFY]` figures must be confirmed against the built report's real CMS/CDC numbers before publishing.

**The report.** `[TODO: screenshots]` → `[TODO: walkthrough video]` → `[TODO: live embed or "view report" button]`.

**Tech stack.** SQL Server · Microsoft Fabric · Power BI (Power Query/M, DAX) · Python · Git.

**Links.** Repo: https://github.com/RobbinsAnalytics/cascadia-pharmacy-analytics · Build explainer in the repo `docs/`.

---

## projects/cascadia-clothing.qmd

**Cascadia Clothing — coming soon.**
The next Cascadia build: retail and ecommerce analytics for an apparel scenario — demand and inventory, merchandising performance, and fulfillment/OTIF — on the same SQL Server → Fabric → Power BI stack. Drawing on my ecommerce BI background, it will extend the Cascadia pattern into retail. Check back, or follow along on [GitHub](https://github.com/RobbinsAnalytics).

---
**Sources (for cited pages):** [CMS Medicare Part D Spending by Drug](https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-spending-by-drug/medicare-part-d-spending-by-drug) · [CDC FluVaxView](https://www.cdc.gov/fluvaxview/dashboard/adult-coverage.html) · [NASA C-MAPSS / PCoE Datasets](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe-datasets/)
