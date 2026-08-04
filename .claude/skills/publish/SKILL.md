---
name: publish
description: Commit and deploy robbinsanalytics.com — fetch, classify whitespace noise, stage, commit, push, wait for the Action, and verify the live site over HTTP. Run this for any change that should go live.
disable-model-invocation: true
---

# Publish robbinsanalytics.com

Nine steps, in order. Do not skip step 2 or step 8 — those are the two that have
actually failed, and neither failure was visible at the time.

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
divergence that took an hour to unpick. Tell the user what is on origin that
they do not have, and let them decide.

## 3 · Classify every changed file

A file whose diff vanishes under `--ignore-all-space` is line-ending churn, not
a change. Five files in this repo do this chronically.

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

## 4 · Stage the real changes only

Stage by name. Never `git add -A` — it sweeps in the noise and any stray
`_to_delete/` the bridge created.

A `PreToolUse` hook will refuse the commit if whitespace-only files are staged.
If it fires, the classification in step 3 was wrong; re-run it rather than
bypassing the hook.

## 5 · Commit

Describe what changed and why, not which files. One subject line under ~72
characters, then a body if the change needs one.

## 6 · Push

```bash
git push origin main
```

That is the deploy. **Do not run `quarto publish gh-pages`** — the workflow does
it, and running both races them.

## 7 · Wait for the Action

```bash
gh run watch    # or: gh run list --limit 1
```

If `gh` is unavailable, wait ~90 seconds and proceed to verification, which will
catch a failed deploy anyway.

## 8 · Verify over HTTP — the step everyone skips

Origin-side evidence is not verification. Reading `gh-pages` proves the right
bytes reached the branch; it says nothing about what the edge serves.

```bash
curl -sSI https://www.robbinsanalytics.com/ | head -1
curl -sSI https://robbinsanalytics.com/ | head -1          # expect 301
curl -sSI https://robbinsanalytics.github.io/ | head -1    # expect 301
curl -sS https://www.robbinsanalytics.com/projects/cascadia-dealdesk.html \
  | grep -o 'og:image[^>]*'
curl -sSI https://www.robbinsanalytics.com/assets/thumb-finance.png | head -1
```

Expect `200` on the first, `301` on both redirects, an `og:image` pointing at
`www.robbinsanalytics.com`, and `200 image/png` on the thumbnail.

**Then confirm the custom domain is still set** in Settings → Pages. That is the
CNAME-survival check — the workflow force-pushes `gh-pages`, and if `CNAME` did
not ship in `_site` the field will be empty and the site has quietly fallen back
to `github.io`. It looks fine until someone follows an old link.

## 9 · Report

State what shipped, what was excluded as noise and why, and what verification
actually returned. If any check failed, say so plainly rather than describing
the deploy as successful — a green Action and a working site are different
claims.

---

## If something goes wrong

**Push rejected, non-fast-forward.** Origin has commits you do not. Stop at step
2 and report. If the local commit is already made and its tree is a superset of
origin's, `git reset --soft origin/main` then re-commit avoids a rebase entirely
— but confirm the superset claim with `git diff origin/main <local>` first.

**Action failed.** Read the log before changing anything. The two recurring
causes are a Quarto render error in a `.qmd` front-matter block, and the
thumbnail step failing because the font CDN did not answer — the latter is
deliberate, `--strict` fails the build rather than shipping cards in a fallback
serif.

**Site loads but cards are wrong.** Social platforms cache aggressively.
LinkedIn's Post Inspector force-refreshes; iMessage caches per thread and mostly
will not refetch.
