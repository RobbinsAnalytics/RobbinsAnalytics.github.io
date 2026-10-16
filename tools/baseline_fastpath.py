#!/usr/bin/env python3
"""Accept a baseline-only follow-up commit without a second full candidate run.

    python tools/baseline_fastpath.py --repo OWNER/NAME --before SHA --head SHA \
        --base SHA [--github-output FILE]

Run by `.github/workflows/candidate.yml` as its first real step on every push
to a pull request. Prints its reasoning and writes `accepted=true` or
`accepted=false` to $GITHUB_OUTPUT. It never fails the job: when anything is
off it says why and the full candidate run goes ahead, which is always safe.

THE PROBLEM IT REMOVES

A pull request that changes a compared page on purpose fails its first
candidate run: the page's screenshot no longer matches its baseline. The new
baseline must be the runner's own image (CLAUDE.md), so the images are copied
from that run's `candidate-screenshots` artifact and committed. Until this
existed, that commit started a second full run -- render, crawl, axe, 28
screenshots -- to re-check a tree that had just been checked, and on
2026-10-16 the re-check itself flaked on a heading that wraps on the edge of
its box. Each intended visual change cost two runs.

WHAT IT PROVES BEFORE ACCEPTING, ALL OF IT, OR NOTHING

1. The new commit is the only commit since the previous run: its one parent is
   the commit that run tested.
2. It changes nothing but images in .github/visual-baselines/, added or
   modified, named <page>-<width>.png.
3. The previous candidate run on that parent completed, and its fact check,
   render, serve, link crawl and accessibility check all succeeded. Only the
   visual check may have failed.
4. That run tested the same base commit of `main` as this one (recorded in its
   artifact as candidate-meta.json), so the merge it rendered is this merge
   minus the images.
5. The pages it failed on are exactly the images this commit changes.
6. Each changed image is byte-identical to the screenshot that run took.

If all six hold, the full run would render the same source and compare it
with the very images it produced last time. Running it again adds nothing but
another chance to flake, so the job passes here.

WHAT IT DOES NOT DO

It does not decide that a visual change is intended. That judgment is made
before the images are committed -- by the session that inspected the diffs,
and by Aaron at merge -- and the PR's screenshots stay downloadable for that
review. It does not chain: a run accepted here uploads no screenshots, so the
next commit always gets a full run. Standard library plus the `gh` CLI that
GitHub's runners carry.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

BASELINE = re.compile(r"^\.github/visual-baselines/([a-z0-9-]+-(?:390|414|768|1440))\.png$")
WORKFLOW = "candidate.yml"
JOB = "candidate"
MUST_SUCCEED = (
    "Check stated facts against their sources",
    "Render",
    "Serve the candidate",
    "Crawl every link on the candidate",
    "Accessibility regression check",
)
VISUAL = "Visual regression check"


class NotEligible(Exception):
    pass


def run(*cmd, check=True):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise NotEligible("%s failed: %s" % (" ".join(cmd[:3]), (p.stderr or p.stdout).strip()[:300]))
    return p.stdout


def git(*args, check=True):
    return run("git", *args, check=check)


def gh_api(path):
    return json.loads(run("gh", "api", path))


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def decide(repo, before, head, base, skip_base_check=False, workdir=None):
    """Return (accepted pages, previous run id). Raise NotEligible otherwise."""
    if not before or set(before) == {"0"}:
        raise NotEligible("no previous head on this event (the PR was opened or reopened)")

    # 1. One commit, one parent, and that parent is the previous head.
    parents = git("rev-list", "--parents", "-n", "1", head).split()
    if len(parents) != 2:
        raise NotEligible("the new head is a merge or a root commit")
    if parents[1] != before:
        raise NotEligible("more than one commit since the previous run (parent %s, previous head %s)"
                          % (parents[1][:7], before[:7]))

    # 2. Only baseline images, added or modified.
    changed = {}
    for line in git("diff", "--name-status", "--no-renames", before, head).splitlines():
        status, path = line.split("\t", 1)
        m = BASELINE.match(path)
        if status not in ("A", "M") or not m:
            raise NotEligible("the commit changes more than baseline images (%s %s)" % (status, path))
        changed[m.group(1)] = path
    if not changed:
        raise NotEligible("the commit changes nothing")

    # 3. The previous run on that parent: completed, everything but visual green.
    runs = gh_api("repos/%s/actions/workflows/%s/runs?head_sha=%s&event=pull_request&per_page=20"
                  % (repo, WORKFLOW, before)).get("workflow_runs", [])
    runs = [r for r in runs if r.get("status") == "completed"]
    if not runs:
        raise NotEligible("no completed candidate run on %s" % before[:7])
    prev = max(runs, key=lambda r: (r["run_attempt"], r["updated_at"]))
    jobs = gh_api("repos/%s/actions/runs/%d/jobs?filter=latest" % (repo, prev["id"])).get("jobs", [])
    job = next((j for j in jobs if j.get("name") == JOB), None)
    if job is None:
        raise NotEligible("run %d has no '%s' job" % (prev["id"], JOB))
    steps = {s["name"]: s.get("conclusion") for s in job.get("steps", [])}
    for name in MUST_SUCCEED:
        if steps.get(name) != "success":
            raise NotEligible("run %d: '%s' was %s, not success" % (prev["id"], name, steps.get(name)))
    if steps.get(VISUAL) not in ("success", "failure"):
        raise NotEligible("run %d: the visual check did not run (%s)" % (prev["id"], steps.get(VISUAL)))

    # Its artifacts: every screenshot it took, and a diff for every page it failed.
    tmp = Path(workdir or tempfile.mkdtemp(prefix="fastpath-"))
    shots, diffs = tmp / "shots", tmp / "diffs"
    run("gh", "run", "download", str(prev["id"]), "--repo", repo,
        "--name", "candidate-screenshots-%s" % before, "--dir", str(shots))
    got_diffs = subprocess.run(["gh", "run", "download", str(prev["id"]), "--repo", repo,
                                "--name", "visual-diffs-%s" % before, "--dir", str(diffs)],
                               capture_output=True, text=True).returncode == 0

    # 4. Same base commit of main.
    if not skip_base_check:
        meta_file = shots / "candidate-meta.json"
        if not meta_file.exists():
            raise NotEligible("run %d recorded no candidate-meta.json (it predates the fast path)" % prev["id"])
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        if meta.get("head_sha") != before:
            raise NotEligible("run %d's meta names head %s, not %s" % (prev["id"], meta.get("head_sha"), before))
        if meta.get("base_sha") != base:
            raise NotEligible("main has moved since run %d (it tested base %s, this is %s)"
                              % (prev["id"], str(meta.get("base_sha"))[:7], base[:7]))

    # 5. Failed pages == changed images.
    failed = {p.stem for p in diffs.glob("*.png")} if got_diffs else set()
    if not failed:
        raise NotEligible("run %d failed no visual comparison, so there is nothing to accept" % prev["id"])
    if failed != set(changed):
        raise NotEligible("run %d failed %s but the commit changes %s"
                          % (prev["id"], sorted(failed), sorted(changed)))

    # 6. Byte-identical to that run's screenshots.
    for page, path in sorted(changed.items()):
        shot = shots / ("%s.png" % page)
        if not shot.exists():
            raise NotEligible("run %d took no screenshot named %s.png" % (prev["id"], page))
        committed = subprocess.run(["git", "show", "%s:%s" % (head, path)], capture_output=True).stdout
        if sha256(committed) != sha256(shot.read_bytes()):
            raise NotEligible("%s is not the image run %d took" % (path, prev["id"]))

    return sorted(changed), prev["id"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--before", default="")
    ap.add_argument("--head", required=True)
    ap.add_argument("--base", default="")
    ap.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT", ""))
    ap.add_argument("--skip-base-check", action="store_true",
                    help="testing only: allow runs that predate candidate-meta.json")
    args = ap.parse_args()

    try:
        pages, prev = decide(args.repo, args.before, args.head, args.base, args.skip_base_check)
        accepted = True
        print("ACCEPTED without a second full run.")
        print("  Candidate run %d tested %s and passed every check except the visual"
              % (prev, args.before[:7]))
        print("  comparison, which failed on exactly these pages:")
        for p in pages:
            print("    %s" % p)
        print("  This commit replaces those baselines with that run's own screenshots,")
        print("  byte for byte, and changes nothing else. Rendering the same source again")
        print("  would compare it with the images it produced last time.")
        print("  https://github.com/%s/actions/runs/%d" % (args.repo, prev))
    except NotEligible as e:
        accepted = False
        print("Full candidate run: %s." % e)
    except Exception as e:                       # noqa: BLE001 -- fall back, never fail
        accepted = False
        print("Full candidate run: the fast-path check raised %s: %s" % (type(e).__name__, e))

    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as f:
            f.write("accepted=%s\n" % ("true" if accepted else "false"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
