# robbinsanalytics.com — what an agent needs to know

Quarto site, published to GitHub Pages. Twelve facts that are not inferable from
the code, each of which caused a real failure. Everything else, read the repo.

## Publishing

**The workflow owns deployment.** `.github/workflows/publish.yml` runs
`quarto publish gh-pages` on every push to `main`. **Never run
`quarto publish gh-pages` by hand** — it races CI and can push a stale build
over a fresh one. Merging a pull request into `main` is the deploy.

**`main` takes no direct push, and two mechanisms make it so rather than a
sentence.** GitHub ruleset 25126263 ("main releases by pull request (ADR
0003)") requires a pull request and the `candidate` status check on `main`,
with no bypass actor, not even the owner, so a direct push is refused
server-side whoever sends it. `.claude/hooks/no_merge_from_code.py`, a
`PreToolUse` hook, refuses a Code session `gh pr merge`, the same merge by
REST, any push whose destination is `main`, and a merge while `main` is checked
out — a Code session pushes with the owner's token, and GitHub cannot tell that
merge from Aaron's, so the hook is the only thing that says the token in a Code
session may not click it. **There is no `ask` entry for `git push`, on
purpose.** One stood in `.claude/settings.json` on the belief that it did not
bind under `bypassPermissions`; it did, and every push waited for Aaron's click
(2026-10-16, about 69 minutes of prompts in one day), so it was removed. The
ruleset and the hook are what stop a push to `main`; a push of a branch needs
no approval.
The hook matches the command text, so a Bash heredoc that merely quotes the
refused phrase is refused too; write such prose with the file-editing tools.

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
three with `python .claude/hooks/hook_test_matrix.py`; it prints its own case
count and exits non-zero on any miss. Do not reach for `--no-verify`.

**The Cowork device bridge leaves a stale `.git/index.lock`.** If git reports
another process is running, delete that file and retry. Nothing is wrong.

## Content

**Canonical domain is `https://www.robbinsanalytics.com`.** Every absolute URL
— `site-url`, `image:` front matter, in-body links — uses it. The `github.io`
address still resolves and redirects, but must not appear in the source.

**Thumbnails are generated, never edited.** `tools/build_thumbs.py` produces all
eighteen OG cards in `assets/` from the `MODULES` list at the top of that file. To
change a card, change the script. CI regenerates them on every build, so hand-
edited images are overwritten. That count is asserted in CI by
`tools/check_references.py` — it said "eight" for two modules longer than it was
true.

## How to publish

Use `/publish`. It fetches first, refuses to proceed if the branch is behind,
classifies whitespace noise, stages by name, commits, pushes the branch, opens
or updates the pull request, and stops. **The merge is the deploy and the
single approval** (ADR 0003, 2026-10-13), and two mechanisms make it so rather
than a sentence: a GitHub ruleset on `main` refuses every direct push and
requires the `candidate` status check, with no bypass actor, not even the
owner; and `.claude/hooks/no_merge_from_code.py`, a `PreToolUse` hook, refuses
a Code session `gh pr merge`, any push whose destination is `main`, and a merge
while on `main`. Nothing before the merge asks Aaron for approval; the hook and
the ruleset bind without asking anyone. Aaron merges
in the GitHub interface after reading the candidate run, and going live is
still one deliberate yes — his.

**Verification lives in two workflows, not in a local shell.** On every pull
request, `candidate.yml` renders the branch, serves it inside the runner, and
runs the link crawl, the accessibility regression check and the visual
regression check against that candidate; the ruleset requires it green before
the merge. After the merge, `publish.yml` deploys, asserts the Pages `cname`,
polls `build.txt` until the edge serves the merge commit, checks the core pages
and redirects, and runs the same three sweeps against the live edge — the
candidate cannot see a lost CNAME or a stale CDN, and only the live run can.
Any miss fails the run and emails Aaron. Do not re-add a local verification
loop — that is the thing that produced false passes. Do not improvise a shorter
version of `/publish`.

**The accessibility job is regression prevention. It is not proof of
conformance, and nothing here may say that it is.** Automated tooling reaches
roughly 30–40% of WCAG success criteria; whether alt text says the right thing,
whether a heading structure matches the document, whether focus order follows
reading order — all of that needs a person. A green run means no
machine-detectable regression and nothing more. This repo's HEAD once had to
remove five unverified "WCAG 2.2 AA" claims; the site says
`WCAG 2.2 AA target (unverified)` and that stays true until someone audits it.
`.github/a11y-baseline.json` records the two accepted third-party violations
(Quarto's navbar toggler on every page, MathJax's speech layer on the paper),
each scoped to its page and its selector — it is a ledger printed on every run,
not a mute, and this site's own HTML does not belong in it. The pages axe
visits are derived from the tree by `site_pages()` in `tools/a11y_check.py`,
not typed: the hand list it replaced had been missing five case studies.

Visual regression compares seven pages at 390 / 414 / 768 / 1440 against
baselines in `.github/visual-baselines/`. **Those baselines are only valid
because they were generated on the runner** — a Windows screenshot differs from
a Linux one in font rendering alone. **The runner image and Playwright are
pinned for the same reason**: `runs-on: ubuntu-24.04` and `playwright==1.64.0`
(Chromium build 1248) in all three workflows. `ubuntu-latest` was moving to
Ubuntu 26 from 2026-10-19; move the pins together, on purpose, with a
whole-set refresh. A page that is meant to change gets its new baselines from
the pull request's own candidate run: download its
`candidate-screenshots-<sha>` artifact and commit the changed pages' images on
the branch, so the baseline is the very image the comparison took, on the
runner, from the candidate. **That commit does not need a second full run.**
If it is the only new commit, changes nothing but those images, and each is
byte-identical to a screenshot the previous run took of a page that run
failed, `tools/baseline_fastpath.py` accepts it in seconds; its header lists
all six conditions, and anything else falls back to the full run. The "Generate visual baselines" workflow
(`workflow_dispatch`) remains for a whole-set refresh when the runner image
moves. Neither commits anything itself, deliberately: the merge is the deploy
and the single approval, CI writing to `main` would break that, and the ruleset
would refuse it besides. **Each full regeneration costs about 15 MB of git
history** — the 28 full-page PNGs are already well compressed, so that is the
real price of pixel comparison rather than something a flag can fix. Commit
only the pages that changed, and regenerate the set when a runner-image move
needs it, not as routine hygiene.

**A change runs start to finish in one pass, and Aaron supervises none of
it.** Once a change is authorized, the session edits, renders, pushes, gives
Aaron the local preview and the pull request link straight away, and keeps
ownership of the candidate run while he looks. It does not end its turn to ask
about routine steps. **Label every compared page the change is meant to
alter** when opening the pull request: `visual-skip:<page>` with the slug from
`PAGES` in `tools/visual_check.py` (index, about, cascadia, case-studies,
finance, dealdesk, sibling-conflict), or `visual-skip:all` for a site-wide
change. A difference on a labelled page is reported with its diff image and
does not fail the run, so an intended change gives a green first run and no
email; every unlabelled page must still match, so an accidental effect on
another page still fails, and that is a defect to fix, not to promote. Then
commit the labelled pages' screenshots from that run, as one commit of only
those images; the fast path accepts it in seconds and main's baselines match
the page Aaron merges. Aaron's preview review covers the labelled pages, which
the pixel check does not. Verification stays proportional — a copy or style
edit gets `tools/check_references.py` and CI; multi-width comparisons are for
layout and design ports; the link crawl and the accessibility suite run in CI,
not locally. Report the candidate as ready only when it is green, and say what
was checked. A visible edit to a compared page takes one full run plus a
fast-path acceptance, about 5 minutes end to end; an edit to a page the visual
check does not cover takes one run.
