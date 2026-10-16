# RCA: About page turnaround, 2026-10-16

**This document:** `C:\Projects\RobbinsAnalytics.github.io\_notes\2026-10-16_RCA_About-page-turnaround.md` (untracked; not committed).

**Scope.** Everything from Aaron's request "Implement the approved About page exactly as provided in this handoff package" (about 13:08 PDT) to the last green candidate run on pull request #7 (14:25 PDT). That covers two pieces of work: the About page prototype port, and the Skills section update.

**Outcome.** Both changes are on `build/about-page-positioning` in [PR #7](https://github.com/RobbinsAnalytics/RobbinsAnalytics.github.io/pull/7). The candidate check is green and the PR is mergeable. Nothing has been merged or deployed.

**Headline.** The work was already designed, yet it took about 77 minutes of wall time to reach a green check. The Code session's own work was about 20 minutes of that. The rest was six serial candidate executions (five runs, one of them re-run; about 26 minutes) and 27 minutes waiting on a question the session should not have asked.

---

## 0. Corrections and status (added after the evaluation, 2026-10-16)

This RCA was evaluated in `C:\Users\Ajayr\OneDrive\AI_Projects\robbins-analytics-system-review\08_ABOUT_PAGE_RCA_EVALUATION_AND_RECOMMENDATIONS_2026-10-16.md`. The evaluation was right on the points below, and they are corrected in this document.

1. **Six executions, not seven.** Five run IDs, one re-run. The right allocation is two initial runs (one per change), two normal baseline follow-ups, and two caused by the heading (the re-run and the extra round). The earlier "four extra baseline runs" plus "two for the heading" counted the same run twice.
2. **The heading's cause is a hypothesis, not established.** Both images came from the runner, so "Linux renders wider than Windows" explains why the line is sensitive, not why two runner runs differed. New evidence: all five runs used the same runner image (ubuntu-24.04, 20261012.601), Chromium 156.0.8078.4 and Quarto 1.10.19, and the checker already waits for `document.fonts.ready`. That rules out image, browser and renderer. The leading suspect is font delivery, since every run loads its fonts from Google Fonts. The visual check now logs the exact font files served, so the next mismatch can confirm or rule this out.
3. **An edited page can carry an unintended defect.** "Every difference on a changed page is intended" is not a safe rule. Every failed page's diff is now opened before its baseline is promoted.
4. **Fix 1 removed more than stated.** The page list is shared by the candidate check, the post-merge live check and baseline generation. Fix 1 was not adopted.
5. **Fix 2 left the post-merge check comparing against images that stop updating.** It was not adopted. A narrower fast path (below) removes the second run without that loop.
6. **The memory rule is a mitigation until a real edit shows it works.** The durable rule now lives in the tracked `CLAUDE.md`.
7. **Fix 3's estimate was optimistic.** Running the two slow checks side by side saves about 73 seconds of a 4m15s job, not 1.5 minutes.

Missed by both documents: GitHub's notice on every run that `ubuntu-latest` moves to Ubuntu 26 from 2026-10-19, which would have invalidated all 28 baselines.

### What was implemented (branch `build/release-cycle-speed`)

| Change | File(s) | Effect |
|---|---|---|
| Runner image pinned to `ubuntu-24.04` | `.github/workflows/candidate.yml`, `publish.yml`, `visual-baselines.yml` | Baselines stay valid through the 2026-10-19 image move |
| Playwright pinned to `1.64.0` (Chromium build 1248) | same three workflows | Same browser every run |
| Baseline fast path | `tools/baseline_fastpath.py` (new), `candidate.yml` | A commit of only the promoted images, byte-identical to the previous run's screenshots of the pages it failed, is accepted in seconds instead of a second full run |
| Run record for the fast path | `candidate.yml` (writes `candidate-meta.json` into the screenshots artifact) | The fast path only accepts when `main` has not moved |
| Accessibility check alongside crawl and visual | `tools/run_and_record.sh` (new), `candidate.yml` | About 73 s off each full run; the check still fails the job under its own name |
| Font-load verification and logging | `tools/visual_check.py` | A face that fails to load is a named failure; served font files are listed every run |
| One-pass release rule, inspect every diff | `CLAUDE.md`, `.claude/skills/publish/SKILL.md` | No routine questions; unintended differences get fixed, not promoted |
| Stale "six pages" and "24 PNGs" | `CLAUDE.md`, `SKILL.md`, `publish.yml` comment | Now seven and 28 |

Not done, with reasons: **self-hosting the fonts** (the direct test of the heading hypothesis) changes every page's font source and forces a whole-set baseline refresh, about 15 MB of history, so it waits for evidence from the new font log; **caching the browser** saves at most part of a 19-second step, so it was not worth the added moving part; **skipping OG thumbnail regeneration** needs a complete map of its inputs first.

---

## 1. Summary

| Cause | Wall time lost | Type | Status |
|---|---|---|---|
| Session asked "refresh the About images?" between two check runs | about 27 min | Agent process | Mitigated: rule in `CLAUDE.md`; effectiveness to be verified |
| Visual-check rule forces two runs per visible About edit | about 9 min (2 normal follow-up runs) | Release rule | Fixed: baseline fast path |
| Flaky architect heading forced two extra runs | about 9 min (re-run plus an extra round) | Unexplained; font delivery suspected | Fast path avoids re-rendering; font log added |
| Each candidate run takes about 4.3 min, checks run one after another | multiplies every run | Workflow | Fix proposed (session card) |
| Local link and accessibility checks that CI repeats | about 2.5 min | Agent process | Mitigated: rule in `CLAUDE.md` |
| Local preview server stopped mid-session | about 1 min | Environment | Noted |

---

## 2. Timeline

All times PDT. Run times are GitHub's own timestamps. Request arrival times are reconstructed from the first file each request produced, so they are accurate to about a minute.

### 2.1 The prototype port

| Time | Event | Elapsed |
|---|---|---|
| ~13:08 | Request arrives; handoff package extracted and read | 0 |
| 13:08 to 13:10 | Handoff, source fragments and prototype CSS read; prototype diffed against the branch render | 2 min |
| 13:10 | Portrait web copy written (1200 x 1800, 257 KB, from the 11.56 MB original) | |
| 13:11 to 13:12 | Fragments spliced into `about.qmd`; styles ported into `felix.scss` | 2 min |
| 13:12 to 13:16 | Render, reference check, link crawl, accessibility check (local); preview server restarted once | 4 min |
| 13:16 to 13:18 | Side-by-side measurement against the prototype at 5 widths; one image-margin fix; interaction checks | 2 min |
| 13:19:13 | Commit 634c779 pushed | **11 min of agent work** |
| 13:19:21 to 13:23:36 | Candidate run 38961389889: red on the four About images (expected under the rule) | 4m15s |
| 13:24:31 | Four About images copied from that run's artifact; commit f93f4ae pushed | 1 min |
| 13:24:44 to ~13:29:30 | Candidate run 38962041483, attempt 1: red, about-1440 differs 0.098% | ~4m45s |
| 13:29:30 to 13:30:30 | Diff inspected: the architect heading wrapped one word differently; measured 6 px of slack | 1 min |
| 13:30:30 to 13:34:49 | Same run, attempt 2 (re-run): red, pixel-identical to attempt 1 | ~4m20s |
| 13:35:40 | about-1440 promoted from the re-run; commit 5cc4112 pushed | 1 min |
| 13:35:48 to 13:40:04 | Candidate run 38963382526: **green** | 4m16s |
| 13:40:32 | PR description updated | |

**Prototype port total: about 32 minutes to green.** Agent work about 14 minutes; CI about 18 minutes across four runs.

### 2.2 The Skills update

| Time | Event | Elapsed |
|---|---|---|
| ~13:43 | Request arrives ("add a couple of buttons") | 0 |
| 13:43 to 13:47 | Seven chips edited, render, reference check, overflow check at 390 and 1440 | 4 min |
| 13:47:10 | Commit 00e07b7 pushed | |
| 13:47:17 to 13:51:34 | Candidate run 38964751072: red on the four About images (expected under the rule) | 4m17s |
| ~13:52 | **Session ended its turn asking whether to refresh the images** | |
| 13:52 to ~14:19 | Waiting for the answer | **~27 min** |
| 14:20:20 | Four About images promoted; commit efad308 pushed | 1 min |
| 14:20:28 to 14:24:51 | Candidate run 38968684253: **green** | 4m23s |

**Skills update total: about 42 minutes to green.** Agent work about 5 minutes; CI about 9 minutes; waiting about 27 minutes.

### 2.3 Where the 77 minutes went

| Bucket | Minutes | Share |
|---|---|---|
| Waiting on the session's question | ~27 | 35% |
| Candidate runs (7 runs including one re-run) | ~27 | 35% |
| Agent implementation and verification | ~20 | 26% |
| Gaps between steps | ~3 | 4% |

Of the six executions, two were the irreducible "check this change" run, two were the normal follow-up the baseline rule forced, and two (the re-run and the extra round) came from the heading mismatch.

---

## 3. Root causes

### RC1. The session asked a question that had only one answer (agent process)

**What happened.** After the Skills edit's first run went red as expected, the session ended its turn and asked whether to refresh the four About images. Aaron had said "make it quick", and the session split the job to report sooner.

**Why it was wrong.** Promoting a changed page's images from the PR's own candidate artifact is the established workflow in `CLAUDE.md`, not a decision. The only time it needs a person is when a page that was not meant to change has moved, which is a style leak. That was not the case.

**Cost.** About 27 minutes, the single largest item.

**Fix status.** Fixed. A standing rule is saved for this repo's sessions: run the whole cycle in one turn, never stop between the two runs to ask about images, state the expected time up front.

### RC2. The visual-check rule doubles every visible About edit (release rule)

**What the rule is.** `tools/visual_check.py` takes full-page screenshots of seven pages, About included, at four widths and compares them to committed baseline images. `CLAUDE.md` requires the baselines to come from GitHub's runner, and no workflow may commit anything. So:

1. Any edit that changes About's height fails the first run; the screenshot no longer matches.
2. The new baseline must be downloaded from that run's artifact and committed by the session.
3. A second run must then pass on the new commit.

**Why it matters.** About is the page that changes most often, and almost every About edit changes its height. Each visible About edit therefore costs two serial runs (about 9 minutes) plus a manual image copy, however small the edit. Adding seven skill chips cost the same as a page redesign.

**What the rule is for.** It catches unintended visual changes, especially a style change for one page leaking to another. That purpose is real. The cost falls mostly on the page being deliberately edited, where a diff is expected and tells the reviewer nothing new.

**Cost here.** Two normal follow-up runs, about 9 minutes, plus three image-copy commits. (Corrected: an earlier version said four, which double-counted the heading runs.)

### RC3. A heading on the edge of its line made the check flaky (rule plus design edge)

**What happened.** At 1440 px the title-defined heading ("An AI Analytics Architect owns the what and the proof, not the how.") fills its 54rem box to within about 6 px on Windows, so its last word sits on the edge. One runner run wrapped it on the first line; the next run on identical code wrapped it onto the second. That moved 0.098% of the page's pixels, above the check's 0.05% tolerance. **Why two runner runs differed is not established** (see section 0): the image, browser and renderer were identical, and font delivery is the leading suspect.

**Cost.** A failed run, a re-run, and a third round: about 10 minutes.

**Why it is a rule problem as much as a design one.** The design is fine on screen either way. The check fails only because it compares the page being edited against a baseline. Taking that page out of blocking comparison (fix 1 or fix 2) removes this whole class of failure.

**Not fixed by changing the design.** Moving the break would mean changing the heading width or type size, which is a design decision. The approved design stays as supplied.

### RC4. Each candidate run is slower than it needs to be (workflow)

Measured on run 38968684253:

| Step | Time |
|---|---|
| Setup and checkout | ~13 s |
| Install Playwright, Pillow, axe | 19 s |
| Regenerate OG thumbnails | 33 s |
| Render | 15 s |
| Serve and crawl links | 18 s |
| Accessibility check | 80 s |
| Visual check | 73 s |
| Uploads | 3 s |
| **Total** | **about 4m20s** |

The two slowest steps run one after the other although they read the same rendered site and do not depend on each other. The browser is downloaded fresh every run. Every extra run in RC2 and RC3 pays this full cost.

### RC5. Local checks duplicated CI (agent process, minor)

During the port the session ran the link crawl and the accessibility check locally (about 2.5 minutes). The candidate run does both on the runner, and `CLAUDE.md` says not to re-add a local verification loop. Local render, the reference check and the prototype comparison were worth running; the other two were not.

**Fix status.** Fixed in the same standing rule: content edits skip local crawl and accessibility runs.

### Contributing factors

- **The preview server stopped** between turns, so the first local crawl and accessibility runs failed on a refused connection and had to be repeated. About 1 minute.
- **The prototype request asked for verification** at desktop and mobile against the prototype, including navigation, links, portrait framing and overflow. That verification was in scope and took about 4 minutes of the 11. It was not the bottleneck.
- **Stale fact in `CLAUDE.md`.** It says visual regression "compares six pages". `tools/visual_check.py` compares seven (28 comparisons = 7 pages x 4 widths). Correct it with whichever fix is chosen.

### What went well

- The port matched the prototype exactly: every measured box at five widths equal, copy byte for byte, the outcomes block unchanged.
- No style leaked. In every red run only the About images moved; the other 24 comparisons passed, which is the check doing its real job.
- The portrait shipped at 257 KB instead of 11.56 MB, and the original photograph stayed untouched.

---

## 4. Proposed fixes

*Sections 4 to 7 are the original proposals, kept as written for the record. Section 0 says which were adopted, which were replaced, and why.*

### Fix 0. Agent process (already done, no approval needed)

- One pass per change: edit, push, wait for run 1, promote images if the rule still requires it, wait for run 2, report. No mid-way question unless a page that was not meant to change has moved.
- State the expected time in the first line of the reply.
- Proportional verification: copy or chip edits get render, reference check and one overflow look at 390 and 1440. Multi-width comparisons are for layout or design ports.
- No local link crawl or accessibility run for content edits; CI does both.

**Effect.** Removes RC1 and RC5. Under the current rules a Skills-sized edit becomes about 13 to 15 minutes, not 42.

### Fix 1. Take About out of the visual check (release rule change, small)

**Change.**
1. Remove `"about"` from `PAGES` in `tools/visual_check.py`.
2. Delete the four `about-*.png` files from `.github/visual-baselines/`.
3. No prose edit: `CLAUDE.md`, the publish skill and a `publish.yml` comment already say "six pages", which becomes true. See section 5.

**Effect.**
- About edits need one candidate run, not two. No image download, no image commit.
- RC3's flaky heading can no longer fail a run.
- Every About edit saves about 5 minutes of CI and about 1 minute of agent work.

**What still guards About.** The link crawl and the accessibility check still run on every page. The other six pages keep their pixel check, which catches shared-style changes leaking from an About edit.

**What is lost.** A visual regression that shows only on the About page, such as a broken About-only style, would no longer be caught automatically. It would be caught by the preview review before merge.

**Effort.** About 10 minutes of work plus one candidate run, as its own small PR. Aaron merges.

### Fix 2. Compare against the live site instead of committed images (release rule change, larger)

**Change.**
1. `publish.yml` uploads the screenshots it takes of the live edge after each deploy as an artifact.
2. `candidate.yml` downloads the latest successful deploy's screenshots and compares the candidate against them, instead of committed images.
3. Pages whose source files the PR changes are compared and reported, but do not fail the run. Every other page must still match, which is the leak check.
4. Committed baselines remain only as a fallback if the deploy artifact has expired (GitHub's default retention is 90 days).

**Effect.**
- No baseline image is ever committed again, for any page. That removes the manual copy step and the roughly 15 MB of git history each full image refresh costs.
- About keeps a pixel check; it simply does not block when About is the page being edited.
- RC2 and RC3 disappear for all seven pages, not just About.

**Trade-offs.** More moving parts: artifact lookup, retention, a rule for mapping source files to pages, and a fallback path. Needs its own testing on a PR.

**Effort.** About 1 hour of work plus testing runs, as its own PR. Aaron merges.

### Fix 3. Make each run faster (workflow change, keeps every check)

Already proposed as a separate session card ("Speed up the candidate check on site PRs").

**Change.**
1. Cache the Playwright browser download between runs.
2. Run the accessibility check and the visual check side by side, with the required `candidate` status kept as the single gating result.
3. Evaluate skipping OG thumbnail regeneration on PRs that do not touch thumbnail inputs; recommend, do not assume.

**Effect.** Each run drops from about 4.3 minutes to an estimated 2.5 to 3 minutes. Tolerances, page lists and the accessibility ledger stay unchanged.

**Effort.** About 30 to 60 minutes plus testing runs, as its own PR.

### Fix 4. End the session at the push (agent process, enabled by fix 1 or 2)

Once an About edit needs only one run, there is nothing for the session to do after pushing. It can hand over the local preview and the PR link immediately. The candidate run finishes while Aaron looks, and he merges when it is green.

---

## 5. Exactly what each fix changes

Paths are absolute. Repository root: `C:\Projects\RobbinsAnalytics.github.io`. "Repo" means the file is tracked in that repository and ships through a PR; "outside repo" means it is not.

### Fix 0. Agent process (already done)

| File | Location | Change | Status |
|---|---|---|---|
| `small-site-edits-one-pass.md` | `C:\Users\Ajayr\.claude\projects\C--Projects-RobbinsAnalytics-github-io\memory\` (outside repo) | New memory: one-pass cycle, no mid-way baseline question, time stated up front, proportional verification, no local crawl or accessibility run for content edits | Written |
| `MEMORY.md` | same folder (outside repo) | One index line pointing at the memory above | Written |

This memory is read by Code sessions on this machine for this project only. To make the rule bind every session on any machine, the same four lines can go into `C:\Projects\RobbinsAnalytics.github.io\CLAUDE.md` under "How to publish". That is optional and would ship as a PR.

### Fix 1. Take About out of the visual check

| File | Location | Change |
|---|---|---|
| `visual_check.py` | `C:\Projects\RobbinsAnalytics.github.io\tools\` (repo) | Delete the line `"about": "/about.html",` from the `PAGES` dictionary |
| `about-390.png` | `C:\Projects\RobbinsAnalytics.github.io\.github\visual-baselines\` (repo) | Delete |
| `about-414.png` | same folder (repo) | Delete |
| `about-768.png` | same folder (repo) | Delete |
| `about-1440.png` | same folder (repo) | Delete |

No prose needs editing. These files already say "six pages", which is wrong today (seven are compared) and becomes true with fix 1:

| File | Location | Line | Text |
|---|---|---|---|
| `CLAUDE.md` | `C:\Projects\RobbinsAnalytics.github.io\` (repo) | 128 | "Visual regression compares six pages at 390 / 414 / 768 / 1440" |
| `CLAUDE.md` | same file | 140 | "the 24 full-page PNGs" (6 pages x 4 widths) |
| `SKILL.md` | `C:\Projects\RobbinsAnalytics.github.io\.claude\skills\publish\` (repo; this repo copy is the one that runs) | 155 | "pixels moved on one of the six compared pages" |
| `publish.yml` | `C:\Projects\RobbinsAnalytics.github.io\.github\workflows\` (repo) | 177 | comment "Compares six pages at four widths" |

Not touched: `candidate.yml`, `publish.yml` logic and `visual-baselines.yml` all call `tools\visual_check.py`, which reads its page list from `PAGES`, so they follow automatically. GitHub ruleset 25126263 is unchanged.

### Fix 2. Compare against the live site

| File | Location | Change |
|---|---|---|
| `publish.yml` | `C:\Projects\RobbinsAnalytics.github.io\.github\workflows\` (repo) | Keep the screenshots the live visual check takes (`--shots-dir`) and upload them as an artifact after each successful deploy |
| `candidate.yml` | same folder (repo) | Before the visual check, download the latest successful deploy's screenshots; pass the list of pages this PR changes |
| `visual_check.py` | `C:\Projects\RobbinsAnalytics.github.io\tools\` (repo) | Accept a baseline directory from the downloaded artifact; report but do not fail pages named as changed; fall back to the committed images if no artifact exists |
| `visual-baselines.yml` | `C:\Projects\RobbinsAnalytics.github.io\.github\workflows\` (repo) | Re-scope as the fallback refresh only, or retire |
| `visual-baselines\*.png` (28 files) | `C:\Projects\RobbinsAnalytics.github.io\.github\visual-baselines\` (repo) | Kept as fallback only; no longer refreshed per PR |
| `CLAUDE.md` | `C:\Projects\RobbinsAnalytics.github.io\` (repo) | Rewrite the visual-regression paragraph: baselines come from the last deploy; changed pages report, others gate; the count corrected |
| `SKILL.md` | `C:\Projects\RobbinsAnalytics.github.io\.claude\skills\publish\` (repo) | Rewrite the "Visual" bullet in step 5: no baseline download or commit step |

GitHub ruleset 25126263 is unchanged as long as the gating job is still named `candidate`.

### Fix 3. Make each run faster

| File | Location | Change |
|---|---|---|
| `candidate.yml` | `C:\Projects\RobbinsAnalytics.github.io\.github\workflows\` (repo) | Cache the Playwright browser; run the accessibility and visual checks side by side; keep a single gating job named `candidate` |
| `publish.yml` | same folder (repo) | Optional: the same browser cache, for faster post-merge verification |

If the gating job's name changed, GitHub ruleset 25126263 (repository Settings, Rules, not a file) would have to change in the same breath. The proposal keeps the name, so the ruleset is untouched.

### Fix 4. End the session at the push

No file changes beyond fix 0's memory: one more line in `small-site-edits-one-pass.md` once fix 1 or 2 is merged.

---

## 6. Estimated times, before and after

### A small content edit (the Skills update)

| Setup | Agent work | Check runs | Total to green | Aaron sees the preview after |
|---|---|---|---|---|
| What happened today | ~5 min | 2 runs, ~9 min | **~42 min** (27 min waiting) | ~4 min |
| Fix 0 only (current rules) | ~5 min | 2 runs, ~9 min | **~13 to 15 min** | ~4 min |
| Fix 0 + fix 1 or 2 | ~3 to 4 min | 1 run, ~4.3 min | **~7 to 8 min** | ~3 to 4 min |
| Fix 0 + fix 1 or 2 + fix 3 | ~3 to 4 min | 1 run, ~2.5 to 3 min | **~6 to 7 min** | ~3 to 4 min |

### A design port (the prototype)

| Setup | Agent work | Check runs | Total to green |
|---|---|---|---|
| What happened today | ~14 min | 4 runs, ~18 min | **~32 min** |
| Fix 0 only (current rules, no flake) | ~11 min | 2 runs, ~9 min | **~20 to 21 min** |
| Fix 0 + fix 1 or 2 | ~10 to 11 min | 1 run, ~4.3 min | **~15 min** |
| Fix 0 + fix 1 or 2 + fix 3 | ~10 to 11 min | 1 run, ~3 min | **~13 to 14 min** |

A design port keeps about 10 minutes of agent work because the request asks for verification against the prototype at several widths.

### The floor

The ruleset on `main` requires one green `candidate` run before any merge (ADR 0003). That is the deliberate safety gate and none of these fixes removes it. The realistic floor for a small edit is therefore one run plus a few minutes of editing: about 6 to 7 minutes to green, with the preview in hand after 3 to 4.

---

## 7. Recommendation and decisions needed

**Recommended:** fix 1 now, fix 3 alongside it, fix 2 later only if About's pixel check is wanted back.

| Decision | Options | Owner |
|---|---|---|
| Change the visual-check rule for About | Fix 1 (drop About), fix 2 (compare to live), or keep as is | Aaron |
| Speed up the candidate run | Start the "Speed up the candidate check" session, or not | Aaron |
| Allow CI to commit images to PR branches | Not proposed. Would change the "no workflow commits" rule, and commits made with the workflow's own token do not trigger the required check, so it needs a separate token. Listed for completeness. | Aaron |

Fix 0 is already in effect. Fixes 1, 2 and 3 each ship as their own PR through the normal release path, and none merges without Aaron.

---

## Appendix: evidence

**Commits on `build/about-page-positioning` in scope**

| Commit | Time | What |
|---|---|---|
| 634c779 | 13:19:13 | About page: portrait, Bio stories and title-defined cards |
| f93f4ae | 13:24:31 | New About baselines from the candidate run, after the prototype port |
| 5cc4112 | 13:35:40 | New about-1440 baseline: the architect heading's runner wrap |
| 00e07b7 | 13:47:10 | About page: Skills additions, Databricks scoped to SQL |
| efad308 | 14:20:20 | New About baselines from the candidate run, after the Skills update |

**Candidate runs in scope**

| Run | Commit | Start to end | Result | Cause of red |
|---|---|---|---|---|
| 38961389889 | 634c779 | 13:19:21 to 13:23:36 | red | About images changed (expected) |
| 38962041483 #1 | f93f4ae | 13:24:44 to ~13:29:30 | red | about-1440 heading wrap, 0.098% |
| 38962041483 #2 | f93f4ae | ~13:30:30 to 13:34:49 | red | Same, pixel-identical |
| 38963382526 | 5cc4112 | 13:35:48 to 13:40:04 | green | |
| 38964751072 | 00e07b7 | 13:47:17 to 13:51:34 | red | About images changed (expected) |
| 38968684253 | efad308 | 14:20:28 to 14:24:51 | green | |

In every red run the link crawl passed, the accessibility check found no new violations, and only About images moved.

**Heading measurement (local Chromium, 1440 px):** font 44.64 px Inter Tight 700; box 918 px; first line needs 912 px; slack 6 px. Identical in the implementation and the prototype.
