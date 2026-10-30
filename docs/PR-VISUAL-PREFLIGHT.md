# Portfolio PR visual preflight

**Scope:** PRs against this portfolio site. This is an application procedure,
not a Cascadia OS standard or a change to the owner merge boundary.

Before opening a PR, fetch `main`, review the changed files and every route they
can affect, and run the source-only preflight. The script reads the current
`PAGES` and `WIDTHS` in `tools/visual_check.py`, checks committed baseline
coverage and the three runner pins, and prints labels for declared intended
changes. It cannot infer the effects of shared CSS, navigation, fonts or build
templates; name those affected pages explicitly.

```text
git fetch origin main
python tools/pr_visual_preflight.py --affected index --expected index
python tools/pr_visual_preflight.py --unmonitored /new-route/
python tools/pr_visual_preflight.py --no-visual-change
```

Use `--affected` once per compared page that could render differently. Add
`--expected` for each page deliberately changing visually. For a route outside
`PAGES`, use `--unmonitored` and decide whether the route needs comparison
coverage. If it does, add it to `PAGES` before opening the PR and repeat the
preflight. A new compared page needs one runner baseline at every listed width.
Do not generate those screenshots on Windows.

Create the PR with all intended-change labels present at opening, for example
`gh pr create --label visual-skip:index`. Create any new `visual-skip:<slug>`
repository label first. `visual-skip:all` is for an actual site-wide design
change, not a shortcut for an uncertain page inventory. Labels report expected
diffs but do not approve them; unlabelled pages still fail on unexpected drift.

The manual `Generate visual baselines` workflow reads the **live origin** by
default. Dispatching it on a feature branch does not make it screenshot that
branch's unpublished page. For a missing new-page baseline, open the PR after
the preflight identifies the gap. The first candidate visual check must fail
and upload its runner screenshots and a new-page preview in `visual-diffs`.
Inspect the screenshot at each width, commit only the missing baseline images
from `candidate-screenshots-<head-sha>`, and push a single baseline-only commit.
The fast path accepts that follow-up only when the previous run's other checks
passed, the base commit is unchanged, the changed images exactly match the
failed visual set, and every committed image is byte-identical to its runner
screenshot. If any condition fails, the normal candidate check runs again.

For an existing compared page with an expected diff, inspect the candidate's
diff and runner screenshot, then commit the intended new baselines as a separate
baseline-only commit before merge. A labelled first run can be green while its
old baselines remain in the branch; that run alone is not ready for merge.
An unexpected diff on an unlabelled page is a defect to investigate, not a
baseline to promote automatically.

Before reporting the PR ready, confirm a green `candidate` check on the final
head, the intended labels, reviewed images for every changed compared page,
and baseline files matching those images. Record extra full CI runs caused by
late labels or missing-baseline recovery, separately from legitimate defects.
The public edge is checked after merge by `publish.yml`.
