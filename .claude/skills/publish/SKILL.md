---
name: publish
description: Open or update the pull request that releases robbinsanalytics.com — classify whitespace noise, stage by name, commit, push the branch, make sure the pull request exists, and stop. Aaron's merge in the GitHub interface is the deploy; the candidate workflow checks the pull request and the publish workflow self-verifies the live site after the merge. Run this for any change that should go live.
disable-model-invocation: false
---

# Publish robbinsanalytics.com

Six steps, and the sixth is stopping. Under ADR 0003 the site releases by pull
request: a Code session gets a change onto a branch and into a pull request
that is green on the candidate check, and **Aaron merges it in the GitHub
interface after reading the run. That merge is the deploy and the single
approval.** Two mechanisms make that structural rather than remembered: a
ruleset on `main` refuses every direct push and requires the `candidate` status
check, with no bypass actor, not even the owner; and
`.claude/hooks/no_merge_from_code.py`, a `PreToolUse` hook, refuses this
session `gh pr merge`, any push whose destination is `main`, and a merge while
`main` is checked out. The `ask` entry for `git push` in
`.claude/settings.json` does not bind under `bypassPermissions`; those two do.

Verification lives in two workflows, not in this skill and not in a local
shell. `.github/workflows/candidate.yml` runs on the pull request: it renders
the branch, serves it inside the runner, and runs the link crawl, the
accessibility regression check and the visual regression check against that
candidate. `.github/workflows/publish.yml` runs on the merge commit: it
deploys, then verifies what the live edge actually serves. This skill is the
part that still needs judgment: deciding what is a real change, and writing
the pull request so Aaron can decide.

## 1 · Clear the way

```bash
git rev-parse --abbrev-ref HEAD
git status --short
```

**The branch must not be `main`.** If it is, branch first, named for the
change (`build/<thing>`, `fix/<thing>`); nothing in this skill pushes `main`,
and the ruleset would refuse it if something did.

A stale `.git/index.lock` is what the Cowork device bridge leaves behind, and
it is also what a git process that is still running holds. Delete it only when
both halves of the test say it is stale: no git process is running, and the
lock is older than the index or older than a few minutes.

```bash
if [ -f .git/index.lock ]; then
  if ! (tasklist //FI "IMAGENAME eq git.exe" 2>/dev/null | grep -qi git.exe || pgrep -x git >/dev/null 2>&1) \
     && { [ .git/index.lock -ot .git/index ] || [ -n "$(find .git/index.lock -mmin +3)" ]; }; then
    rm -f .git/index.lock && echo "removed a stale index.lock"
  else
    echo "index.lock is held or fresh — a git process may own it; wait, then re-check"
  fi
fi
```

If it will not clear by that test, something still holds it: close any editor
or Git GUI on this repo. Do not work around it.

## 2 · Fetch, and stop if behind

```bash
git fetch origin
git rev-list --left-right --count origin/main...HEAD       # <main has> <branch has>
git rev-list --left-right --count @{upstream}...HEAD 2>/dev/null   # if already pushed
```

**If the branch's own upstream has commits this checkout lacks, stop and
report.** Do not rebase, do not force. A previous session auto-resolved a
divergence and manufactured one that took an hour to unpick. Tell Aaron what
is on origin that he does not have.

**If `main` has moved** since the branch was cut, the ruleset will not let the
pull request merge until the branch is up to date with it. Bring `main` into
the branch, never the other way round:

```bash
git merge --no-edit origin/main
```

If that merge conflicts, stop and report; resolving it is a decision.

## 3 · Classify every changed file

A file whose diff vanishes under `--ignore-all-space` is line-ending churn, not
a change. Five files in this repo do this chronically: `LICENSE`, `.gitignore`,
`styles.scss`, `.github/workflows/publish.yml`, and
`assets/cascadia_analytics_tech_stack.svg`.

```bash
for f in $(git diff --name-only; git diff --cached --name-only); do
  if [ -n "$(git diff HEAD --numstat -- "$f")" ] &&
     [ -z "$(git diff HEAD --ignore-all-space --numstat -- "$f")" ]; then
    echo "NOISE: $f"
  else
    echo "REAL:  $f"
  fi
done | sort -u
```

Binary files report `-` for both counts and are always real — do not exclude an
image because this check looks ambiguous.

## 4 · Stage by name and commit

Stage the real changes explicitly. Blanket staging is refused by the
`PreToolUse` hook `no_blanket_add_or_force_push.py` (the matching `deny`
entries in `.claude/settings.json` are documentation under
`bypassPermissions`), because it sweeps in the noise and any stray
`_to_delete/` the bridge created.

Write the message to a temp file and use `git commit -F` — an inline `-m` with
a multi-line body mangled the message once already.

```bash
git add -- <paths>
git commit -F <tempfile>
```

**The git `pre-commit` gate** (`.githooks/pre-commit`, active only where
`git config core.hooksPath .githooks` has been run in this clone) runs
`secret_scan.py` first and `no_whitespace_commits.py` second, and refuses the
commit if a credential or a whitespace-only file is staged. If the whitespace
gate fires, step 3 was wrong; re-run it rather than bypassing the gate. Allow
rules do not bypass hooks, and `--no-verify` is not used here.

Describe what changed and why, not which files. One subject line under ~72
characters, then a body if the change needs one.

## 5 · Push the branch, and open or update the pull request

```bash
git push -u origin "$(git rev-parse --abbrev-ref HEAD)"
gh pr view --json number,url,state 2>/dev/null \
  || gh pr create --base main --head "$(git rev-parse --abbrev-ref HEAD)" \
       --title "<what this releases>" --body-file <tempfile>
```

The push starts the candidate workflow. The pull request body is written for
Aaron: what changed and why, in his words, and anything he must look at
before merging (a visual diff, a rewritten sentence). Link the candidate run
once it exists.

```bash
gh run list --workflow candidate.yml --branch "$(git rev-parse --abbrev-ref HEAD)" --limit 1
gh run watch <run-id>
```

**If the candidate is red**, fix it on the branch and push again; the next run
supersedes the last. Three red outcomes and what each means:

- **Crawl**: a link on the candidate is broken. Fix the link.
- **Accessibility**: a new machine-detectable violation, or a page that
  scrolls sideways. Fix the markup; the ledger is for third-party markup only.
- **Visual**: pixels moved on one of the six compared pages. Download the
  run's `visual-diffs-<sha>` artifact and look. A regression gets fixed. An
  intended change gets its new baselines from the same run: download
  `candidate-screenshots-<sha>`, copy the changed pages' images into
  `.github/visual-baselines/`, commit them on the branch, push. They were
  taken on the runner from the candidate, which is what makes them valid.

**Do not run `quarto publish gh-pages`.** The publish workflow does it after
the merge; running it by hand races the workflow and can push a stale build
over a fresh one.

## 6 · Report, and stop

Report:

- the pull request URL and the candidate run's link and result,
- what shipped onto the branch, and what was excluded as noise and why,
- anything Aaron needs to look at before merging.

**Do not merge.** Not `gh pr merge`, not a push to `main`, not a local merge
on `main`; the hook refuses all three and the ruleset refuses the push. The
merge is Aaron's, in the GitHub interface, after reading the candidate run.
Once he merges, `publish.yml` runs on the merge commit, deploys, and then
verifies itself against the live edge: the Pages `cname`, `build.txt` polled
until the edge serves the merge commit, the core pages and redirects, the
link crawl, the accessibility check and the visual check. A red run emails
him. A later session confirms the release; this one is done.

---

## If something goes wrong

**`git push` to `main` is rejected with `GH013: Repository rule violations
found`.** That is the ruleset working. Nothing is wrong with the repo; push
the branch instead and open the pull request.

**The pull request shows "merging is blocked" with the candidate green.**
The branch is behind `main` (the ruleset requires it up to date). Step 2's
merge of `origin/main` into the branch, then push, re-runs the candidate.

**The publish Action is red on "Wait for the edge to serve this commit."** The
build deployed but the live site is not serving it. Do not re-deploy blindly.
Check whether the CNAME step also failed — a cleared custom domain makes the
edge poll fail for a reason that has nothing to do with the content.

**The publish Action is red on "Assert the custom domain survived the
force-push."** `CNAME` did not ship in `_site`. Confirm `_quarto.yml` still
lists `CNAME` under `resources:`, then re-set the custom domain in Settings →
Pages.

**Build failed before deploy.** The two recurring causes are a Quarto render
error in a `.qmd` front-matter block, and the thumbnail step failing because
the font CDN did not answer — the latter is deliberate, `--strict` fails the
build rather than shipping cards in a fallback serif. The candidate workflow
runs the same steps, so this is normally caught before the merge.

**Site loads but social cards are wrong.** Platforms cache aggressively.
LinkedIn's Post Inspector force-refreshes; iMessage caches per thread and
mostly will not refetch.
