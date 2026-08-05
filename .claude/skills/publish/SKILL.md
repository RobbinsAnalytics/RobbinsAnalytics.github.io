---
name: publish
description: Commit and deploy robbinsanalytics.com — classify whitespace noise, stage by name, commit, push. The push is the deploy; the Action self-verifies the live site. Run this for any change that should go live.
disable-model-invocation: false
---

# Publish robbinsanalytics.com

Five steps. The old nine-step version ended with the agent verifying the live
site from a local shell — which could pass against a stale CDN edge, and did.
That verification now lives in `.github/workflows/publish.yml`, where it runs
after propagation and can fail the deploy. This skill is the part that still
needs judgment: deciding what is a real change.

**The push is the only approval.** Everything before it is local and
reversible; everything after it is the Action's job.

## 1 · Clear the way

```bash
git rev-parse --abbrev-ref HEAD          # must be main
rm -f .git/index.lock                    # the Cowork bridge leaves these behind
git status --short
```

If `index.lock` will not delete, something still holds it — close any editor or
Git GUI on this repo. Do not work around it.

## 2 · Fetch, and stop if behind

```bash
git fetch origin
git rev-list --left-right --count origin/main...main
```

Output is `<behind> <ahead>`.

**If behind is greater than zero, stop and report.** Do not rebase, do not
merge, do not force. A previous session auto-resolved this and manufactured a
divergence that took an hour to unpick. Tell Aaron what is on origin that he
does not have, and let him decide.

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

Stage the real changes explicitly. `git add -A` and `git add .` are denied in
`.claude/settings.json`, because they sweep in the noise and any stray
`_to_delete/` the bridge created.

Write the message to a temp file and use `git commit -F` — an inline `-m` with
a multi-line body mangled the message once already.

```bash
git add -- <paths>
git commit -F <tempfile>
```

A `PreToolUse` hook refuses the commit if whitespace-only files are staged. If
it fires, step 3 was wrong; re-run it rather than bypassing the hook. Allow
rules do not bypass hooks, and neither does `--no-verify`.

Describe what changed and why, not which files. One subject line under ~72
characters, then a body if the change needs one.

## 5 · Push — this is the deploy, and the one approval

```bash
git push origin main
```

**Do not run `quarto publish gh-pages`.** The workflow does it; running both
races them and can push a stale build over a fresh one.

The push triggers the Action, which renders, deploys, and then verifies itself:

1. asserts the Pages `cname` is still `www.robbinsanalytics.com` (the
   force-push to `gh-pages` is what can silently clear it),
2. polls `https://www.robbinsanalytics.com/build.txt` until the edge returns
   the pushed SHA — up to 10 minutes, which is what waits out CDN propagation,
3. checks the core pages for `200` and both redirects for `301`.

Any miss fails the Action, which turns it red and emails Aaron.

## 6 · Report

Watch the run and confirm independently:

```bash
gh run watch
```

Then fetch a changed page yourself — WebFetch works even when the shell has no
network — and report:

- what shipped,
- what was excluded as noise and why,
- whether the Action's own verification passed, naming any failed check.

A green Action now *does* mean the live site serves this build; that is the
whole point of moving verification into CI. But if the run is red, say the
deploy failed. A completed push and a working site are still different claims.

---

## If something goes wrong

**The Action is red on "Wait for the edge to serve this commit."** The build
deployed but the live site is not serving it. Do not re-push blindly. Check
whether the CNAME step also failed — a cleared custom domain makes the edge
poll fail for a reason that has nothing to do with the content.

**The Action is red on "Assert the custom domain survived the force-push."**
`CNAME` did not ship in `_site`. Confirm `_quarto.yml` still lists `CNAME`
under `resources:`, then re-set the custom domain in Settings → Pages.

**Push rejected, non-fast-forward.** Origin has commits you do not. Stop and
report. If the local commit is already made and its tree is a superset of
origin's, `git reset --soft origin/main` then re-commit avoids a rebase — but
confirm the superset claim with `git diff origin/main <local>` first.

**Build failed before deploy.** The two recurring causes are a Quarto render
error in a `.qmd` front-matter block, and the thumbnail step failing because
the font CDN did not answer — the latter is deliberate, `--strict` fails the
build rather than shipping cards in a fallback serif.

**Site loads but social cards are wrong.** Platforms cache aggressively.
LinkedIn's Post Inspector force-refreshes; iMessage caches per thread and
mostly will not refetch.
