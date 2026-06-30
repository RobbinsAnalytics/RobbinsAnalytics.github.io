# RobbinsAnalytics.github.io

Aaron Robbins — Business Intelligence & Analytics portfolio site.

**Live URL:** <https://robbinsanalytics.github.io>

Built with [Quarto](https://quarto.org/) and published to GitHub Pages.

---

## Site Structure

```
RobbinsAnalytics.github.io/
├─ _quarto.yml                  # Quarto website config (cosmo theme + Cascadia palette)
├─ index.qmd                    # Landing page — Aaron Robbins identity + featured case studies
├─ about.qmd                    # Bio, skills, resume, contact
├─ cascadia.qmd                 # Cascadia family concept + shared architecture
├─ projects/
│   ├─ cascadia-medical-devices.qmd   # Manufacturing case study
│   ├─ cascadia-pharmacy.qmd          # Healthcare/pharmacy case study
│   └─ cascadia-clothing.qmd          # Retail placeholder (coming soon)
├─ assets/
│   ├─ cascadia_analytics_tech_stack.svg   # Architecture diagram
│   └─ img/                                # Screenshots, GIFs per case study
└─ styles.scss                  # SCSS overrides — Cascadia color palette
```

This repo is a **site shell only**. The build repos it links to are separate:

| Project | Repo |
|---|---|
| Cascadia Medical Devices | [manufacturing-analytics](https://github.com/RobbinsAnalytics/manufacturing-analytics) |
| Cascadia Pharmacy | [cascadia-pharmacy-analytics](https://github.com/RobbinsAnalytics/cascadia-pharmacy-analytics) |

---

## Publish Workflow

This site uses the **`quarto publish gh-pages`** approach:

- Source lives on `main` (what you're reading now).
- Rendered HTML is pushed to the `gh-pages` branch automatically by Quarto.
- GitHub Pages is configured to serve from the `gh-pages` branch.

### To publish a new version

```powershell
# From the repo root
quarto publish gh-pages --no-browser
```

Quarto renders the site locally, then force-pushes the rendered output to the `gh-pages` branch. The live site updates within ~30 seconds.

### Local preview

```powershell
quarto preview
```

---

## Custom Domain (future)

A custom domain can be added later without rebuilding:

1. Buy a domain (e.g., `aaronrobbins.io`).
2. Add a `CNAME` file to the repo root containing only your domain:
   ```
   aaronrobbins.io
   ```
3. Add the appropriate DNS records at your registrar (GitHub docs: [Managing a custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)).
4. Re-run `quarto publish gh-pages --no-browser`.

> **Note:** `quarto publish gh-pages` will overwrite the `gh-pages` branch including any `CNAME` file. Always keep the `CNAME` file in the `main` branch source and re-publish after DNS changes.

---

## Contributing / Updating

- **Copy updates (Cowork):** Edit the `.qmd` files, then run `quarto publish gh-pages --no-browser`.
- **Screenshots / video (Aaron):** Drop files into `assets/img/`, update the relevant `projects/*.qmd`, then publish.
- **New case study:** Copy a `projects/*.qmd` template, add a navbar entry in `_quarto.yml`, publish.

---

## License

MIT — see [LICENSE](LICENSE).

Data used in linked case studies (CMS Medicare Part D, CDC VaxView) is U.S. federal public-domain data. See individual build repo READMEs for full attribution.
