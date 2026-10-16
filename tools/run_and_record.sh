#!/usr/bin/env bash
# Run a check in the background and report it later, under its own step.
#
#   tools/run_and_record.sh PREFIX CMD [ARGS...]    run CMD; write PREFIX.log, then PREFIX.exit
#   tools/run_and_record.sh --wait PREFIX SECONDS   wait for PREFIX.exit, print PREFIX.log,
#                                                   exit with the recorded code
#
# Used by candidate.yml so the accessibility check can run alongside the link
# crawl and the visual check while still failing the job, and still reporting
# its full output, under the step named "Accessibility regression check".
# The exit file is written last and renamed into place, so a waiter never
# reads a half-written code. A check that never finishes fails after SECONDS.
set -u

if [ "${1:-}" = "--wait" ]; then
  prefix="$2"; limit="${3:-900}"
  for _ in $(seq 1 "$limit"); do
    [ -f "$prefix.exit" ] && break
    sleep 1
  done
  cat "$prefix.log" 2>/dev/null || true
  if [ ! -f "$prefix.exit" ]; then
    echo "::error::the background check did not finish within ${limit}s"
    exit 1
  fi
  exit "$(cat "$prefix.exit")"
fi

prefix="$1"; shift
"$@" > "$prefix.log" 2>&1
code=$?
echo "$code" > "$prefix.exit.tmp"
mv "$prefix.exit.tmp" "$prefix.exit"
