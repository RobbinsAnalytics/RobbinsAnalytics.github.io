#!/usr/bin/env python3
"""Declared behaviour of no_merge_from_code.py, runnable.

    python .claude/hooks/no_merge_from_code_test.py

Exit 0 if every case behaves as declared, 1 otherwise. Beside the hook rather
than inside hook_test_matrix.py because that matrix is a manifested canonical
file (cascadia-standards/governance/hook_manifest.json) and is not edited per
repo. Same shape as the matrix: each row is a command and whether it must be
allowed or refused, so the file reads as the specification and runs as the
check. Negative controls matter as much as refusals: a hook that refused
`git push origin <branch>` would refuse the one thing a session is for.

Branch-dependent cases run against a throwaway repository created in a
temporary directory, checked out on `main` or on a branch, passed to the hook
as the payload's cwd. Nothing outside that directory is touched.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "no_merge_from_code.py")
ALLOW, DENY = "allow", "refuse"


def run_hook(command, cwd):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd})
    r = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True)
    if r.returncode == 0:
        return ALLOW
    try:
        out = json.loads(r.stdout)
        if out["hookSpecificOutput"]["permissionDecision"] == "deny":
            return DENY
    except (ValueError, KeyError):
        pass
    return "error(%s)" % r.returncode


def git(cwd, *args):
    return subprocess.run(("git",) + args, cwd=cwd, capture_output=True, text=True)


# (expected, command, which checkout the payload's cwd points at, note)
CASES = [
    # --- the merge itself ---
    (DENY,  "gh pr merge 1",                                   "branch", "the merge, by gh"),
    (DENY,  "gh pr merge --squash --delete-branch 1",          "branch", "the merge, any flags"),
    (DENY,  "gh api -X PUT repos/o/r/pulls/1/merge",           "branch", "the merge, by REST"),
    (DENY,  "gh api --method PUT repos/o/r/pulls/1/merge",      "branch", "the merge, by REST, long flag"),
    (DENY,  "gh api repos/o/r/pulls/1/merge -f merge_method=squash", "branch", "a field makes gh POST: the merge"),
    (DENY,  "gh pr view 1 && gh pr merge 1",                   "branch", "merge after a separator"),

    # --- pushes whose destination is main ---
    (DENY,  "git push origin main",                            "branch", "explicit main"),
    (DENY,  "git push -u origin main",                         "branch", "upstream flag, main"),
    (DENY,  "git push origin HEAD:main",                       "branch", "HEAD to main"),
    (DENY,  "git push origin build/x:main",                    "branch", "branch to main"),
    (DENY,  "git push origin +HEAD:refs/heads/main",           "branch", "full ref, forced spelling"),
    (DENY,  "git push origin --delete main",                   "branch", "deleting main"),
    (DENY,  "git push --all origin",                           "branch", "--all includes main"),
    (DENY,  "git -C /c/Projects/site push origin main",        "branch", "git's own option first"),
    (DENY,  "git status; git push origin main",                "branch", "semicolon separator"),
    (DENY,  "git push",                                        "main",   "bare push while on main"),
    (DENY,  "git push origin",                                 "main",   "remote only, while on main"),
    (DENY,  "git push",                                        "none",   "bare push, branch unreadable: fails CLOSED"),

    # --- local merges into main ---
    (DENY,  "git merge build/x",                               "main",   "merge while on main"),
    (DENY,  "git merge --ff-only origin/main",                 "main",   "even a fast-forward merge"),
    (DENY,  "git checkout main && git merge build/x",          "main",   "merge after a separator, on main"),

    # --- negative controls: the job itself ---
    (ALLOW, "git push origin build/release-by-pr",             "branch", "control: pushing the branch is the job"),
    (ALLOW, "git push -u origin build/x",                      "branch", "control: first push of a branch"),
    (ALLOW, "git push origin HEAD:build/x",                    "branch", "control: refspec to a branch"),
    (ALLOW, "git push origin main:backup/main-2026",           "branch", "control: main as SOURCE, not destination"),
    (ALLOW, "git push",                                        "branch", "control: bare push on a branch"),
    (ALLOW, "git push origin",                                 "branch", "control: remote only, on a branch"),
    (ALLOW, "git merge main",                                  "branch", "control: bringing main into a branch"),
    (ALLOW, "git merge build/x",                               "none",   "control: merge, branch unreadable: fails OPEN"),
    (ALLOW, "git pull --ff-only origin main",                  "main",   "control: syncing main after Aaron merged"),
    (ALLOW, "git fetch origin main",                           "main",   "control: fetch is not a merge"),
    (ALLOW, "git merge-base main HEAD",                        "main",   "control: merge-base is not merge"),
    (ALLOW, "git log main..HEAD --oneline",                    "main",   "control: the word main in a range"),
    (ALLOW, "git checkout main",                               "branch", "control: checking main out"),
    (ALLOW, "gh pr create --base main --head build/x",         "branch", "control: opening the pull request"),
    (ALLOW, "gh pr view 1 --json mergeStateStatus",            "branch", "control: reading the pull request"),
    (ALLOW, "gh pr checks 1",                                  "branch", "control: reading the checks"),
    (ALLOW, "gh api repos/o/r/pulls/1",                        "branch", "control: reading by REST"),
    (ALLOW, "gh api repos/o/r/pulls/1/merge",                  "branch", "control: GET on the merge state is a read"),
    (ALLOW, "ls -la",                                          "branch", "control: neither git nor gh"),
]


def main():
    root = tempfile.mkdtemp(prefix="cascadia-no-merge-")
    nowhere = tempfile.mkdtemp(prefix="cascadia-not-a-repo-")
    try:
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.email", "t@example.invalid")
        git(root, "config", "user.name", "t")
        git(root, "config", "commit.gpgsign", "false")
        with open(os.path.join(root, "f.txt"), "w") as fh:
            fh.write("x\n")
        git(root, "add", "f.txt")
        git(root, "commit", "-q", "-m", "init")
        branch_root = os.path.join(root, "wt")
        git(root, "worktree", "add", "-q", "-b", "build/x", branch_root)
        where = {"main": root, "branch": branch_root, "none": nowhere}

        failures, rows = [], 0
        print("no_merge_from_code.py   (PreToolUse, repo-local)")
        print("-" * 86)
        for expected, cmd, checkout, note in CASES:
            rows += 1
            actual = run_hook(cmd, where[checkout])
            ok = actual == expected
            print("  %s  %-6s  %-44s  on %-6s  %s"
                  % ("ok  " if ok else "FAIL", expected, cmd, checkout, note))
            if not ok:
                failures.append("%r on %s: expected %s, got %s" % (cmd, checkout, expected, actual))
        print("-" * 86)
        if failures:
            print("%d of %d cases did not behave as declared:" % (len(failures), rows))
            for f in failures:
                print("  - %s" % f)
            return 1
        print("%d of %d cases behaved as declared." % (rows, rows))
        return 0
    finally:
        git(root, "worktree", "remove", "--force", os.path.join(root, "wt"))
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(nowhere, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
