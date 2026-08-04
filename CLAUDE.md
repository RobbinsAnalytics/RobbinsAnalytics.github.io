# robbinsanalytics.com — what an agent needs to know

Quarto site, published to GitHub Pages. Seven facts that are not inferable from
the code, each of which caused a real failure. Everything else, read the repo.

## Publishing

**The workflow owns deployment.** `.github/workflows/publish.yml` runs
`quarto publish gh-pages` on every push to `main`. **Never run
`quarto publish gh-pages` by hand** — it races CI and can push a stale build
over a fresh one. Pushing `main` is the deploy.

**`CNAME` must ship in `_site`.** The workflow rebuilds the `gh-pages` branch
from `_site` and force-pushes it, so any `CNAME` GitHub writes to that branch is
destroyed on the next deploy — the custom domain then silently clears and the
site falls back to the `github.io` address. `_quarto.yml` lists `CNAME` under
`resources:` for exactly this reason. Do not remove it.

**`_site/` is build output and is gitignored.** Never commit it.

## Committing

**Five files chronically show line-ending-only diffs**: `LICENSE`,
`.gitignore`, `styles.scss`, `.github/workflows/publish.yml`, and
`assets/cascadia_analytics_tech_stack.svg`. They are not real changes.
**Verify every file before staging** — if
`git diff --ignore-all-space --numstat -- <file>` returns nothing, the diff is
whitespace and the file must not be staged. A `PreToolUse` hook enforces this
and will refuse the commit; the hook is the control, this note is the reason.

**The Cowork device bridge leaves a stale `.git/index.lock`.** If git reports
another process is running, delete that file and retry. Nothing is wrong.

## Content

**Canonical domain is `https://www.robbinsanalytics.com`.** Every absolute URL
— `site-url`, `image:` front matter, in-body links — uses it. The `github.io`
address still resolves and redirects, but must not appear in the source.

**Thumbnails are generated, never edited.** `tools/build_thumbs.py` produces all
eight OG cards in `assets/` from the `MODULES` list at the top of that file. To
change a card, change the script. CI regenerates them on every build, so hand-
edited images are overwritten.

## How to publish

Use `/publish`. It fetches first, refuses to proceed if the branch is behind,
classifies whitespace noise, commits, pushes, waits for the Action, and verifies
the live site over HTTP. Do not improvise a shorter version of this.
