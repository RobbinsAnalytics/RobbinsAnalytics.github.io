#!/usr/bin/env python3
"""PreToolUse hook — the merge to main is Aaron's, in the GitHub interface.

    REPO-LOCAL. Not a cascadia-standards template. Do not propagate.

WHY THIS IS NOT IN THE TEMPLATE

`no_blanket_add_or_force_push.py` carries estate-wide invariants. This rule is
a property of one repository: the site publishes from `main`, and under ADR
0003 (Accepted 2026-10-13) the one approval that puts a change in front of the
public is a pull-request merge that Aaron clicks after seeing the candidate's
checks. A Code session opens and updates the pull request; it does not merge
it. Other repositories in the estate merge their own branches as a matter of
course, so a template that refused it would fight every one of them.

WHY A HOOK AND NOT A PERMISSION RULE

`.claude/settings.json` lists `git push*` under "ask". The desktop Code surface
runs in bypassPermissions, which skips the permission layer, so that entry is
documentation and not a mechanism (SESSION-RULES 3). PreToolUse hooks are run
by Claude Code itself and bind regardless of mode. The ruleset on `main` is the
other half: it refuses a direct push server-side with no bypass actor, so even
a session that evaded this file would be refused by GitHub. Two controls, one
on each side of the wire.

WHY THE RULESET ALONE IS NOT ENOUGH

The identity a Code session pushes with is the repository owner's, the same
identity Aaron merges with. GitHub cannot tell the merge button from
`gh pr merge` run by an agent holding that token; both are the owner merging.
The ruleset makes direct pushes impossible for everyone, but a pull request
that is green on the candidate check is mergeable by that token, and this file
is the only thing that says the token in a Code session may not do it.

WHAT IS REFUSED

  gh pr merge ...                        the merge itself, any flags
  gh api -X PUT ... /pulls/<n>/merge     the same merge by REST; a GET on that
                                         path is a read and passes
  git push ... main                      any push whose destination is main:
                                         `origin main`, `HEAD:main`,
                                         `x:refs/heads/main`, `--delete main`,
                                         `--all`, `--mirror`, or a bare
                                         `git push` while main is checked out
  git merge ...   while on main          a local merge into main; there is
                                         nothing it can lead to but a push
                                         the ruleset refuses, and it leaves a
                                         local main that no longer matches
                                         the published one

WHAT IS NOT REFUSED, AND WHY

  git push origin <branch>               that is how a pull request is opened
                                         and updated; the whole point
  git pull / git fetch on main           syncing local main to what Aaron
                                         merged is not a merge decision
  git merge on a branch                  bringing main into a branch is normal
  gh pr create / view / checks / diff    reading and opening are the job
  git merge-base, git push origin main:x the word, not the act

FAIL DIRECTIONS

  A push whose destination cannot be determined without the current branch
  (bare `git push`) fails CLOSED when the branch cannot be read: a push is
  outward-facing, and refusing costs one command with an explicit refspec.
  A `git merge` whose branch cannot be read fails OPEN: it is local and
  revocable, and refusing every merge in a session where detection merely
  broke would be the worse failure.

THERE IS NO ESCAPE HATCH

The sibling hook in cascadia-early-warning has one (`-c
cascadia.deliberate=true`) because a human pushing that repo interactively is
normal work. Here the deliberate act is the click in the GitHub interface, by
Aaron, after reading the candidate run. A hatch that let a session merge
"deliberately" would be the approval moving back to the session, which is the
thing ADR 0003 moved.

KNOWN COARSENESS: the command string is inspected, so a command that quotes one
of these patterns is refused too. Same tradeoff as the sibling hooks; use the
Write tool for such content. Tested by `no_merge_from_code_test.py` beside this
file, because `hook_test_matrix.py` is a manifested canonical file and is not
edited per repo.
"""

import json
import os
import re
import shlex
import subprocess
import sys

# A leading `git` may carry its own options (-C <path>, -c k=v) before the
# subcommand. Same shape as the sibling hooks, for the same reason.
_GIT = r"\bgit\s+(?:-[cC]\s+\S+\s+|--\S+\s+)*"

GIT_PUSH = re.compile(_GIT + r"push(?![-\w])")
GIT_MERGE = re.compile(_GIT + r"merge(?![-\w])")
GH_PR_MERGE = re.compile(r"\bgh\s+pr\s+merge(?![-\w])")
GH_API_MERGE = re.compile(r"\bgh\s+api\b[^\n]*?/pulls/[^/\s]+/merge\b")
# `gh api` without a method is a GET, and a GET on that path only asks whether
# the pull request merged. A method that writes, or a field or body (which make
# gh POST by default), is the merge.
GH_API_WRITES = re.compile(r"(?:^|\s)(?:-X|--method)[\s=]+(?:PUT|POST|PATCH)\b"
                           r"|(?:^|\s)(?:-f|-F|--field|--raw-field|--input)\b")

MAIN_REFS = {"main", "refs/heads/main"}

# Shell separators. Splitting on these keeps each command independent.
SEGMENT = re.compile(r"&&|\|\||;|\||\n")

MESSAGE = (
    "The merge to main is Aaron's, in the GitHub interface.\n\n"
    "    {segment}\n\n"
    "Refused by rule: {rule}\n\n"
    "ADR 0003: a Code session opens or updates the pull request and stops.\n"
    "Push the branch (`git push origin <branch>`), make sure the pull request\n"
    "exists (`gh pr create` or `gh pr view`), and report. Aaron merges after\n"
    "reading the candidate run; that merge is the release.\n\n"
    "This is a PreToolUse hook, not a permission rule, so it binds under\n"
    "bypassPermissions. The ruleset on main refuses a direct push server-side\n"
    "as well, with no bypass actor."
)


def deny(segment, rule):
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": MESSAGE.format(segment=segment.strip(), rule=rule),
        }
    }, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(2)


def current_branch(cwd):
    """The checked-out branch in cwd, or None if it cannot be read."""
    try:
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                           cwd=cwd or None, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.strip() or None


def tokens(segment):
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def push_targets_main(segment, cwd):
    """True if this push segment would move main.

    Positional arguments after `push` are <remote> then <refspec>...; a refspec's
    destination is the part after the colon, or the whole thing. Flags are
    skipped; `--all` and `--mirror` include main by definition; `--delete` makes
    every following positional a destination. With a remote but no refspec, or
    nothing at all, git pushes the current branch, so that is what is judged.
    """
    toks = tokens(segment)
    try:
        i = next(k for k, t in enumerate(toks) if t == "push")
    except StopIteration:
        return False
    rest = toks[i + 1:]
    positional, delete = [], False
    for t in rest:
        if t in ("--all", "--mirror", "--branches"):
            return True
        if t in ("--delete", "-d"):
            delete = True
            continue
        if t.startswith("-"):
            continue
        positional.append(t)
    if not positional:
        # bare `git push`: the current branch is the destination
        return (current_branch(cwd) or "") in MAIN_REFS or current_branch(cwd) is None
    refspecs = positional if delete else positional[1:]
    if not refspecs:
        b = current_branch(cwd)
        return b is None or b in MAIN_REFS
    for spec in refspecs:
        dst = spec.split(":", 1)[1] if ":" in spec else spec
        dst = dst.lstrip("+")
        if dst in MAIN_REFS:
            return True
    return False


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    cmd = (payload.get("tool_input") or {}).get("command", "")
    if "git" not in cmd and "gh" not in cmd:
        return 0
    cwd = payload.get("cwd") or os.getcwd()

    for segment in SEGMENT.split(cmd):
        if GH_PR_MERGE.search(segment):
            deny(segment, "gh pr merge")
        if GH_API_MERGE.search(segment) and GH_API_WRITES.search(segment):
            deny(segment, "gh api -X PUT .../pulls/<n>/merge")
        if GIT_PUSH.search(segment) and push_targets_main(segment, cwd):
            deny(segment, "git push to main")
        if GIT_MERGE.search(segment):
            b = current_branch(cwd)
            if b in MAIN_REFS:
                deny(segment, "git merge while on main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
