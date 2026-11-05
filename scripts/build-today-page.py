#!/usr/bin/env python3
"""Bake today's Break of the Day into a static HTML page.

Why this exists: the pick lives in a Supabase edge function that answers with
`content-type: application/json`, and most LLM browse tools only read HTML --
they come back empty on a JSON endpoint, which is what Gemini did. GitHub Pages
serves plain HTML from a host with no bot challenge in front of it, so a page
built here is readable by anything that can fetch a URL.

No JavaScript on the page on purpose: a fetcher that does not run scripts still
has to see the break name. /ig/ builds itself client-side and a crawler sees
only "Loading", which is the bug this avoids.

Run from the repo root. Writes today/index.html. Exits non-zero and writes
nothing if the feed is unreachable or has no pick, so a bad run leaves
yesterday's page up rather than publishing a blank one.
"""
import html, json, pathlib, sys, urllib.request

FEED = "https://erzfcqlnezmufmtyejvv.supabase.co/functions/v1/todays-call"
OUT = pathlib.Path("today/index.html")

def fetch():
    req = urllib.request.Request(FEED, headers={
        "accept": "application/json",
        # A default python user-agent is the kind of thing edge bot-scoring
        # dislikes; say who we are instead of pretending to be a browser.
        "user-agent": "boardcall-site-builder (+https://boardcall.app)",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def main():
    try:
        call = fetch().get("call") or {}
    except Exception as e:                      # noqa: BLE001 - any failure is the same failure
        print(f"feed unreachable: {e}", file=sys.stderr)
        return 1

    name = (call.get("name") or "").strip()
    if not name:
        print("no pick in feed; leaving the existing page alone", file=sys.stderr)
        return 1

    e = lambda v: html.escape(str(v)) if v not in (None, "") else ""
    region, verdict = e(call.get("region")), e(call.get("verdict")).upper()
    day, read = e(call.get("day")), e(call.get("read"))
    face, period = call.get("faceFt"), call.get("periodS")
    size = e(call.get("sizeWords")); wind = e(call.get("windWords"))
    swell, hour = e(call.get("swellDir")), e(call.get("hourLabel"))

    facts = []
    if face:   facts.append(f"<li>Face height: {face} ft{f' ({size})' if size else ''}</li>")
    if period: facts.append(f"<li>Swell: {period} s from the {swell}</li>" if swell
                            else f"<li>Swell period: {period} s</li>")
    if wind:   facts.append(f"<li>Wind: {wind}</li>")
    if hour:   facts.append(f"<li>{hour}</li>")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Break of the Day: {e(name)} &middot; Boardcall</title>
<meta name="description" content="Boardcall's Break of the Day for {day}: {e(name)}, {region}. Verdict {verdict}.">
<style>
:root{{color-scheme:light dark}}
body{{font:17px/1.6 system-ui,-apple-system,sans-serif;max-width:40rem;margin:0 auto;padding:2.5rem 1.25rem}}
h1{{font-size:1.6rem;margin:.2rem 0 .3rem}}
p.region{{margin:0 0 1.2rem;opacity:.75}}
.verdict{{font-weight:700;letter-spacing:.06em}}
ul{{padding-left:1.1rem}}
footer{{margin-top:2rem;font-size:.85rem;opacity:.7}}
</style>
</head>
<body>
<p>Boardcall &middot; Break of the Day &middot; {day}</p>
<h1>{e(name)}</h1>
<p class="region">{region}</p>
<p>Verdict: <span class="verdict">{verdict}</span>. {read}</p>
<ul>
{chr(10).join(facts)}
</ul>
<footer>
<p>This page names one break, the one Boardcall ranked best across its whole catalogue
this morning. It is rebuilt daily and carries no other content.</p>
<p>Wave and wind data: Open-Meteo (CC BY 4.0).</p>
</footer>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page)
    print(f"wrote {OUT} -- {name} ({verdict}) for {day}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
