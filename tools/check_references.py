#!/usr/bin/env python3
"""Assert that this repo's prose still matches the files it describes.

Run it:

    python tools/check_references.py

Exit 0 if every stated fact matches its machine-readable source, 1 otherwise,
with each mismatch named. No network, no imports outside the standard library,
deterministic. It reads; it never writes.

WHY THIS EXISTS

A fact stated in a config file and restated in prose drifts, and the prose is
what the next person reads. That defect class has now recurred four times across
this estate. In this repo it was already live when this check was written:
`CLAUDE.md` said `tools/build_thumbs.py` produces "eight OG cards" while
`MODULES` held ten and ten `thumb-*.png` sat in `assets/`. Two modules were
added and the sentence describing them was not. Nothing caught it because
nothing was looking.

WHAT THIS DELIBERATELY DOES NOT CHECK, AND WHY

The obvious check — "no document tells you to run `quarto publish gh-pages` by
hand, because CLAUDE.md forbids it" — is not here. Nine tracked files contain
that string. `CLAUDE.md` and `.claude/skills/publish/SKILL.md` contain it to
forbid it; `.github/workflows/publish.yml` and `_quarto.yml` describe what CI
does with it; three files under `_notes/` are dated planning documents from
2026-06-29 that recorded it as the plan at the time. Only `README.md` actually
instructed it, and that was corrected by hand rather than by pattern.

The distinction between instructing a command and recording that it was once
the plan is not greppable. A check that cannot draw it is either useless or
permanently red, and a permanently red check is switched off in week two. So
it is stated here instead of enforced badly.

Historical statements are not drift. `_quarto.yml`'s "Six of eight thumbnails
404'd ... 2026-08-02" is a dated account of a past event and stays correct
however many thumbnails exist now. Only undated present-tense claims are
checked.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CANONICAL_DOMAIN = "www.robbinsanalytics.com"

# CLAUDE.md spells its counts. Only the range a module list could plausibly
# reach — a bare digit would be caught by the same regex and is handled too.
WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
}

failures = []
notes = []


def fail(check, detail):
    failures.append("%s\n      %s" % (check, detail))


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def as_count(token):
    token = token.lower()
    if token.isdigit():
        return int(token)
    return WORDS.get(token)


# ---------------------------------------------------------------------------
# 1 · The canonical domain, restated in four places.
#
# The highest-consequence fact in the repo. `quarto publish gh-pages`
# force-pushes the gh-pages branch, so a CNAME that does not ship in _site
# silently clears the custom domain and the site falls back to github.io. Four
# files state this domain and all four have to agree, or one of them is lying
# about what the deploy will do.
# ---------------------------------------------------------------------------
def check_domain():
    cname = read("CNAME").strip()
    if cname != CANONICAL_DOMAIN:
        fail("CNAME", "holds %r, expected %r" % (cname, CANONICAL_DOMAIN))

    m = re.search(r'^\s*site-url:\s*"([^"]+)"', read("_quarto.yml"), re.M)
    if not m:
        fail("_quarto.yml", "no site-url found")
    elif m.group(1) != "https://%s" % CANONICAL_DOMAIN:
        fail("_quarto.yml site-url", "is %r, expected https://%s" % (m.group(1), CANONICAL_DOMAIN))

    wf = read(".github/workflows/publish.yml")
    if '"$cname" != "%s"' % CANONICAL_DOMAIN not in wf:
        fail(
            "publish.yml cname assertion",
            "does not assert %r — the step that catches a cleared custom domain "
            "is checking for something else" % CANONICAL_DOMAIN,
        )

    if "**Canonical domain is `https://%s`.**" % CANONICAL_DOMAIN not in read("CLAUDE.md"):
        fail("CLAUDE.md", "does not name %r as the canonical domain" % CANONICAL_DOMAIN)

    notes.append(
        "canonical domain: CNAME, _quarto.yml, publish.yml and CLAUDE.md all say %s"
        % CANONICAL_DOMAIN
    )


# ---------------------------------------------------------------------------
# 2 · The OG-card count CLAUDE.md states vs the two sources of truth.
#
# This is the check that was already red when it was written.
# ---------------------------------------------------------------------------
def check_thumb_count():
    src = read("tools/build_thumbs.py")
    block = re.search(r"^MODULES\s*=\s*\[(.*?)^\]", src, re.S | re.M)
    if not block:
        fail("tools/build_thumbs.py", "MODULES list not found")
        return
    declared = len(re.findall(r"\bslug\s*=\s*[\"']", block.group(1)))

    on_disk = len(list((ROOT / "assets").glob("thumb-*.png")))

    m = re.search(
        r"`tools/build_thumbs\.py` produces all\s+(\w+)\s+OG cards", read("CLAUDE.md")
    )
    if not m:
        fail("CLAUDE.md", "the sentence stating the OG-card count was not found")
        return
    stated = as_count(m.group(1))
    if stated is None:
        fail("CLAUDE.md", "OG-card count %r is not a number this check understands" % m.group(1))
        return

    if not (stated == declared == on_disk):
        fail(
            "OG-card count",
            "CLAUDE.md says %d, MODULES declares %d, assets/ holds %d thumb-*.png"
            % (stated, declared, on_disk),
        )
    else:
        notes.append("OG cards: CLAUDE.md, MODULES and assets/ all agree on %d" % stated)


# ---------------------------------------------------------------------------
# 3 · The five chronically noisy files CLAUDE.md names must still exist.
#
# The note tells a session to check those paths before staging. A renamed or
# deleted file turns that instruction into a quiet no-op.
# ---------------------------------------------------------------------------
def check_noisy_files():
    doc = read("CLAUDE.md")
    m = re.search(
        r"\*\*(\w+) files chronically show line-ending-only diffs\*\*:(.+?)They are not real",
        doc,
        re.S,
    )
    if not m:
        fail("CLAUDE.md", "the line-ending-noise paragraph was not found")
        return
    stated = as_count(m.group(1))
    named = re.findall(r"`([^`]+)`", m.group(2))
    if stated != len(named):
        fail(
            "CLAUDE.md noisy-file count",
            "says %s but names %d paths" % (m.group(1), len(named)),
        )
    missing = [p for p in named if not (ROOT / p).exists()]
    if missing:
        fail(
            "CLAUDE.md names paths that do not exist",
            ", ".join(missing),
        )
    else:
        notes.append("line-ending noise list: %d named, all present" % len(named))


# ---------------------------------------------------------------------------
# 4 · GitHub Action versions.
#
# Two properties. First, every `uses:` is pinned to a bare major — a floating
# branch is not a pin and a full semver stops receiving security patches.
# Second, any prose that restates one of those versions has to match the
# workflow. Nothing restates them today; this is the guard for the moment
# something does, which is exactly when a version bump lands. PL6 bumped
# checkout v4 -> v7 and setup-python v5 -> v7 on 2026-08-25, and a sentence
# naming the old numbers would have survived that bump silently.
# ---------------------------------------------------------------------------
def check_action_versions():
    wf = read(".github/workflows/publish.yml")
    uses = dict(re.findall(r"uses:\s*([\w.-]+/[\w./-]+)@([\w.-]+)", wf))
    if not uses:
        fail(".github/workflows/publish.yml", "no `uses:` refs found")
        return

    for action, ref in sorted(uses.items()):
        if not re.fullmatch(r"v\d+", ref):
            fail(
                "publish.yml pins %s@%s" % (action, ref),
                "expected a bare major such as v4 — a branch is not a pin, and a "
                "full semver stops receiving patch releases",
            )

    # Prose that restates a version has to agree with the workflow. Live
    # documents only: _notes/ is dated planning material from 2026-06-29 and is
    # a record of what was true then, not a claim about now.
    for doc in ("CLAUDE.md", "README.md"):
        text = read(doc)
        for action, ref in sorted(uses.items()):
            for found in re.findall(re.escape(action) + r"@(v[\w.]+)", text):
                if found != ref:
                    fail(
                        "%s restates %s@%s" % (doc, action, found),
                        "publish.yml uses @%s" % ref,
                    )
    notes.append(
        "action pins: %s" % ", ".join("%s@%s" % (a, r) for a, r in sorted(uses.items()))
    )


# ---------------------------------------------------------------------------
# 5 · The github.io address must not appear as a URL in rendered source.
#
# CLAUDE.md states this rule and nothing enforced it. The address still
# resolves and redirects, which is why a stray one is invisible in testing: the
# page loads, the canonical URL is simply wrong, and every share and every
# crawler follows the redirect instead of the real address. Comments *about*
# the fallback are fine and are why this matches a URL rather than the bare
# hostname. The workflow legitimately carries one, in the 301 assertion.
# ---------------------------------------------------------------------------
def check_no_github_io_urls():
    pattern = re.compile(r"//(?:www\.)?robbinsanalytics\.github\.io")
    offenders = []
    targets = sorted(ROOT.glob("*.qmd")) + sorted(ROOT.glob("projects/*.qmd"))
    targets.append(ROOT / "_quarto.yml")
    targets.append(ROOT / "styles.scss")
    for path in targets:
        if not path.exists():
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                offenders.append("%s:%d" % (path.relative_to(ROOT).as_posix(), i))
    if offenders:
        fail(
            "github.io used as a URL in rendered source",
            "%s — use https://%s" % (", ".join(offenders), CANONICAL_DOMAIN),
        )
    else:
        notes.append("no github.io URLs in rendered source (%d files scanned)" % len(targets))


def main():
    for check in (
        check_domain,
        check_thumb_count,
        check_noisy_files,
        check_action_versions,
        check_no_github_io_urls,
    ):
        try:
            check()
        except Exception as exc:                  # noqa: BLE001 — fail closed
            fail(check.__name__, "raised %s: %s" % (type(exc).__name__, exc))

    for note in notes:
        print("  ok    %s" % note)

    if failures:
        sys.stderr.write("\nSTALE REFERENCE — prose no longer matches the file it describes.\n\n")
        for f in failures:
            sys.stderr.write("  FAIL  %s\n\n" % f)
        sys.stderr.write(
            "Each of these is a sentence that was true when it was written. Correct\n"
            "the prose, or correct the file it describes — but do not silence this.\n\n"
        )
        return 1

    print("\n%d reference checks passed." % (len(notes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
