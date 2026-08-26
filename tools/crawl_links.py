#!/usr/bin/env python3
"""Crawl the live site and check every link it can reach.

    python tools/crawl_links.py [--origin URL] [--cache-bust SHA] [--max-pages N]

Exit 0 if every internal link resolves and no external link is definitively
gone, 1 otherwise. Standard library only, same as the rest of tools/.

WHY A CRAWL AND NOT A LONGER SMOKE LIST

`publish.yml` already asserts a fixed list of URLs, and that list earns its
keep: it names the old Cascadia Finance paths that must return 200 forever and
the two redirects that carry every previously shared link. A fixed list cannot
find a link that a page acquired last week, which is the failure this adds.
Both run. The list is a contract; the crawl is a sweep.

INTERNAL AND EXTERNAL ARE NOT THE SAME PROBLEM, AND ARE NOT TREATED THE SAME

An internal 404 is this repo's fault and always real, so it fails the run.

An external link is checked, but only a definitive 404 or 410 fails. A 403 is
usually a bot filter -- plenty of large sites refuse a bare urllib request and
serve the page fine to a browser. A 429 is rate limiting. A 5xx or a timeout is
someone else's bad afternoon. Failing a deploy of this site because LinkedIn
rate-limited a runner would train everyone to ignore a red run, which costs more
than the dead link it was meant to catch. Those responses are printed with their
status so a human can look, and they do not fail the build.

That is a scoping decision, not a mute: the class of defect that gets caught is
stated, and the class that does not is printed every run rather than suppressed.

WHAT IS NOT COVERED

Links that only appear after JavaScript runs. This fetches HTML and parses it;
it does not execute a page. Every link on this site is in the served HTML, so
the gap is theoretical here and would stop being theoretical the day a page
builds its own navigation. Recorded rather than glossed.
"""

import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from html.parser import HTMLParser

DEFAULT_ORIGIN = "https://www.robbinsanalytics.com"
UA = "robbinsanalytics-link-crawler (+https://www.robbinsanalytics.com)"
TIMEOUT = 25

SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "sms:")

# External hosts answer a definitive 404/410 or they do not. Everything else is
# reported, not failed. See the module docstring.
EXTERNAL_FATAL = {404, 410}


class LinkParser(HTMLParser):
    """Collect every URL-bearing attribute in a page."""

    WANTED = {
        "a": ("href",),
        "area": ("href",),
        "img": ("src", "srcset"),
        "source": ("src", "srcset"),
        "script": ("src",),
        "link": ("href",),
        "iframe": ("src",),
        "video": ("src", "poster"),
        "audio": ("src",),
        "embed": ("src",),
        "object": ("data",),
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.found = []

    # A preconnect or dns-prefetch href is an ORIGIN to warm up, not a document
    # to fetch. https://fonts.googleapis.com answers 404 to a bare GET and is
    # working perfectly; the stylesheet URL under it is the real link. Checking
    # these produced two false positives on the first run of this crawler.
    NOT_DOCUMENTS = {"preconnect", "dns-prefetch"}

    def handle_starttag(self, tag, attrs):
        wanted = self.WANTED.get(tag)
        if not wanted:
            return
        d = dict(attrs)
        if tag == "link":
            rels = (d.get("rel") or "").lower().split()
            if any(r in self.NOT_DOCUMENTS for r in rels):
                return
        for attr in wanted:
            val = d.get(attr)
            if not val:
                continue
            if attr == "srcset":
                # "a.png 1x, b.png 2x" -> the URL is the first token of each part
                for part in val.split(","):
                    part = part.strip().split()
                    if part:
                        self.found.append(part[0])
            else:
                self.found.append(val)


def fetch(url, method="GET"):
    """Return (status, final_url, body_bytes_or_None). Never raises."""
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read() if method == "GET" else b""
            return r.status, r.geturl(), body
    except urllib.error.HTTPError as e:
        return e.code, url, None
    except Exception as e:                        # noqa: BLE001 — reported, not raised
        return 0, url, ("%s: %s" % (type(e).__name__, e)).encode()


def normalise(base, raw):
    raw = raw.strip()
    if not raw or raw.startswith("#") or raw.lower().startswith(SKIP_SCHEMES):
        return None
    absolute = urllib.parse.urljoin(base, raw)
    parsed = urllib.parse.urlsplit(absolute)
    if parsed.scheme not in ("http", "https"):
        return None
    # A fragment is the same document.
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path,
                                    parsed.query, ""))


def bust(url, token):
    if not token:
        return url
    parts = urllib.parse.urlsplit(url)
    query = "%s&cb=%s" % (parts.query, token) if parts.query else "cb=%s" % token
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origin", default=DEFAULT_ORIGIN)
    ap.add_argument("--cache-bust", default="")
    ap.add_argument("--max-pages", type=int, default=200)
    args = ap.parse_args()

    origin = args.origin.rstrip("/")
    host = urllib.parse.urlsplit(origin).netloc

    queue = deque([origin + "/"])
    seen_pages = set()
    checked = {}          # url -> status
    internal_bad = []
    external_bad = []
    external_noted = []
    referrers = {}
    truncated = False

    while queue:
        if len(seen_pages) >= args.max_pages:
            truncated = True
            break
        page = queue.popleft()
        if page in seen_pages:
            continue
        seen_pages.add(page)

        status, final, body = fetch(bust(page, args.cache_bust))
        checked[page] = status
        if status != 200:
            internal_bad.append((page, status, referrers.get(page, "seed")))
            continue
        if body is None or b"<html" not in body[:4000].lower():
            continue

        parser = LinkParser()
        try:
            parser.feed(body.decode("utf-8", "replace"))
        except Exception:                         # noqa: BLE001
            pass

        for raw in parser.found:
            target = normalise(page, raw)
            if not target:
                continue
            referrers.setdefault(target, page)
            same_origin = urllib.parse.urlsplit(target).netloc == host
            if same_origin:
                if target.endswith((".html", "/")) and target not in seen_pages:
                    queue.append(target)
                elif target not in checked:
                    st, _, _ = fetch(bust(target, args.cache_bust), method="HEAD")
                    if st in (405, 501, 0):        # some hosts dislike HEAD
                        st, _, _ = fetch(bust(target, args.cache_bust))
                    checked[target] = st
                    if st != 200:
                        internal_bad.append((target, st, referrers[target]))
            else:
                if target in checked:
                    continue
                st, _, _ = fetch(target, method="HEAD")
                if st in (405, 501, 0):
                    st, _, _ = fetch(target)
                checked[target] = st
                if st in EXTERNAL_FATAL:
                    external_bad.append((target, st, referrers[target]))
                elif st != 200:
                    external_noted.append((target, st, referrers[target]))

    internal = sum(1 for u in checked if urllib.parse.urlsplit(u).netloc == host)
    external = len(checked) - internal

    print("  crawled   %d pages from %s" % (len(seen_pages), origin))
    print("  checked   %d internal links, %d external" % (internal, external))
    if truncated:
        print("  ::warning::stopped at the --max-pages cap of %d; some pages were "
              "not crawled" % args.max_pages)

    if external_noted:
        print()
        print("  external links that did not return 200 and do NOT fail this run")
        print("  (403 bot filter, 429 rate limit, 5xx or timeout — see the module docstring):")
        for url, st, ref in sorted(external_noted):
            print("    %-4s %s\n         on %s" % (st or "err", url, ref))

    if not internal_bad and not external_bad:
        print()
        print("No broken links.")
        return 0

    sys.stderr.write("\nBROKEN LINKS\n\n")
    for url, st, ref in sorted(internal_bad):
        sys.stderr.write("  ::error::internal %s -> %s\n           linked from %s\n"
                         % (st or "no response", url, ref))
    for url, st, ref in sorted(external_bad):
        sys.stderr.write("  ::error::external %s -> %s\n           linked from %s\n"
                         % (st, url, ref))
    sys.stderr.write("\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
