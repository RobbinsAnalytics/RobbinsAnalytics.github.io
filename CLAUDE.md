# robbinsanalytics.com — what an agent needs to know

Quarto site, published to GitHub Pages. Nine facts that are not inferable from
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

**`build.txt` is the deploy's receipt, and CI overwrites it.** The committed
value is the placeholder `local`; the workflow writes the pushed commit SHA
into it before rendering, then polls
`https://www.robbinsanalytics.com/build.txt` until the edge returns that same
SHA. This exists because verifying from a local shell could pass against a
stale CDN edge — the Action went green while the site served the previous build
for another two minutes. Like `CNAME`, it is listed under `resources:` in
`_quarto.yml` so Quarto copies it into `_site`. Do not remove either, and do
not commit a real SHA into it.

## Committing

**Five files chronically show line-ending-only diffs**: `LICENSE`,
`.gitignore`, `styles.scss`, `.github/workflows/publish.yml`, and
`assets/cascadia_analytics_tech_stack.svg`. They are not real changes.
**Verify every file before staging** — if
`git diff --ignore-all-space --numstat -- <file>` returns nothing, the diff is
whitespace and the file must not be staged. `.gitattributes` prevents most of
this churn at the source and `.githooks/no_whitespace_commits.py` refuses what
gets through; the gates are the control, this note is the reason.

**Three commit gates run here, and the activation does not travel with a
clone.** `.githooks/secret_scan.py` and `.githooks/no_whitespace_commits.py` run
as a git `pre-commit` hook, **credential gate first** — the order is
load-bearing, because under `set -e` a whitespace complaint would otherwise
abort the commit before the credential scan ran, and a staged credential would
go unreported behind a complaint about line endings.
`.claude/hooks/no_blanket_add_or_force_push.py` runs as a `PreToolUse` hook and
refuses blanket staging and force pushes; it binds under `bypassPermissions`,
where the `deny` block in `.claude/settings.json` does not. The scripts are
tracked and arrive with a clone — **`git config core.hooksPath .githooks` does
not.** Run it once per clone or there is no git-side gate at all. Verify all
three with `python .claude/hooks/hook_test_matrix.py`: 50 declared cases, exit
non-zero on any miss. Do not reach for `--no-verify`.

**The Cowork device bridge leaves a stale `.git/index.lock`.** If git reports
another process is running, delete that file and retry. Nothing is wrong.

## Content

**Canonical domain is `https://www.robbinsanalytics.com`.** Every absolute URL
— `site-url`, `image:` front matter, in-body links — uses it. The `github.io`
address still resolves and redirects, but must not appear in the source.

**Thumbnails are generated, never edited.** `tools/build_thumbs.py` produces all
ten OG cards in `assets/` from the `MODULES` list at the top of that file. To
change a card, change the script. CI regenerates them on every build, so hand-
edited images are overwritten. That count is asserted in CI by
`tools/check_references.py` — it said "eight" for two modules longer than it was
true.

## How to publish

Use `/publish`. It fetches first, refuses to proceed if the branch is behind,
classifies whitespace noise, stages by name, commits, and pushes. **The push is
the deploy and the single approval** — `git push` is on `ask` in
`.claude/settings.json` while the read-only preflight calls are on `allow`, so
going live is always one deliberate yes.

**Verification lives in the Action, not in a local shell.** After deploying,
the workflow asserts the Pages `cname`, polls `build.txt` until the edge serves
the pushed SHA, and checks the core pages and redirects. Any miss fails the run
and emails Aaron. Do not re-add a local verification loop — that is the thing
that produced false passes. Do not improvise a shorter version of `/publish`.
