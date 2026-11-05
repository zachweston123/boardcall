#!/usr/bin/env python3
"""Bake today's Break of the Day into a static page: card, caption, conditions.

Two readers, one page.

  A person posting it   needs the card image and the caption, on a phone, with
                        no key and no laptop.
  An LLM fetching it    needs the break name in plain text. Browse tools read
                        HTML and come back empty on a JSON endpoint, which is
                        why this exists rather than pointing them at the feed.

So every fact is in the markup as text, and the card is drawn on a canvas on
top of that. A fetcher that runs no JavaScript still sees the whole post.
/ig/ builds itself client-side and a crawler sees only "Loading"; this avoids
that trap deliberately.

Run from the repo root. Writes today/index.html. Exits non-zero and writes
nothing if the feed is unreachable or has no pick, so a bad run leaves
yesterday's page up rather than publishing a blank one.

With --require-today it also exits non-zero when the feed's newest pick is not
today's. That is the quiet failure worth catching: if the upstream job never
wrote a row, the feed deliberately serves yesterday's, this script would rebuild
a byte-identical page, nothing would change, and the run would go green while
the page sat a day behind. Pass the flag on the last run of the morning only --
on the earlier ones the pick may simply not be written yet, and failing then
would cry wolf every day.
"""
import datetime, html, json, pathlib, sys, urllib.request

FEED = "https://erzfcqlnezmufmtyejvv.supabase.co/functions/v1/todays-call"
OUT = pathlib.Path("today/index.html")


def fetch():
    req = urllib.request.Request(FEED, headers={
        "accept": "application/json",
        # Say who we are rather than impersonating a browser.
        "user-agent": "boardcall-site-builder (+https://boardcall.app)",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def hour_label(local_iso):
    """`2026-11-05T17:00` -> `5pm`. The feed stamps the break's own local time."""
    try:
        hh = int(str(local_iso).split("T")[1].split(":")[0])
    except (IndexError, ValueError, AttributeError):
        return ""
    suffix = "am" if hh < 12 else "pm"
    h = hh % 12 or 12
    return f"{h}{suffix}"


def alternates_block(call, e):
    """The runners-up, for the morning the day's break has no usable footage.

    Rendered as text in the markup like every other fact on this page, so the
    research prompt reads the names with no JavaScript. Absent entirely when
    the feed sends none -- an empty heading would read as a broken section, and
    on a day when nothing else is fun-or-better there is genuinely nowhere to
    send anyone.
    """
    alts = call.get("alternates")
    if not isinstance(alts, list) or not alts:
        return ""
    rows = []
    for a in alts:
        name = e(a.get("name"))
        if not name:
            continue
        bits = []
        if a.get("faceFt") is not None:
            bits.append(f"{a['faceFt']} ft")
        if a.get("verdict"):
            bits.append(e(a["verdict"]))
        hour = hour_label(a.get("hour"))
        if hour:
            bits.append(f"best {hour}")
        rows.append(
            f'    <div class="row"><dt>{name}</dt>'
            f'<dd>{e(a.get("region"))}{" &middot; " if a.get("region") and bits else ""}'
            f'{" &middot; ".join(bits)}</dd></div>'
        )
    if not rows:
        return ""
    return (
        '\n<h2>If this one is thin</h2>\n'
        '<p style="margin:0 0 .9rem">No footage worth reposting from the break above? '
        'These were next on this morning\u2019s list, so they are the same call, not a guess. '
        'Run the research prompt again on whichever one you pick.</p>\n'
        '<dl>\n' + "\n".join(rows) + "\n</dl>\n"
    )


def main():
    try:
        call = (fetch() or {}).get("call") or {}
    except Exception as exc:                     # noqa: BLE001 - any failure is the same failure
        print(f"feed unreachable: {exc}", file=sys.stderr)
        return 1

    name = (call.get("name") or "").strip()
    if not name:
        print("no pick in feed; leaving the existing page alone", file=sys.stderr)
        return 1

    # The feed stamps its day in America/Los_Angeles, so compare against that
    # rather than UTC. At the times this runs the two agree anyway; being explicit
    # keeps it correct if the schedule ever moves.
    try:
        import zoneinfo
        today = datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).date().isoformat()
    except Exception:                            # noqa: BLE001 - no tzdata: UTC is right at 14:05
        today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

    feed_day = (call.get("day") or "").strip()
    if "--require-today" in sys.argv and feed_day != today:
        print(f"feed's newest pick is {feed_day or 'missing'}, not {today} -- "
              "the upstream job has not written today's row", file=sys.stderr)
        return 1

    e = lambda v: html.escape(str(v)) if v not in (None, "") else ""

    # Below about 4 knots the direction stops meaning anything, and the app's own
    # wind row prints "glassy" alone. The feed still sometimes pairs a direction
    # with it ("offshore, glassy"), which reads as a contradiction on a card. Drop
    # the direction rather than publish the contradiction. The underlying fix is
    # one line in break-of-day/index.ts and is still outstanding.
    raw_wind = (call.get("windWords") or "").strip()
    if "glassy" in raw_wind.lower():
        call["windWords"] = "glassy"

    # sizeWords is often null in the feed. card.js derives it from faceFt; do the
    # same here so the page's text and the card agree. Bands are §7.3.
    if not call.get("sizeWords") and isinstance(call.get("faceFt"), (int, float)):
        f = call["faceFt"]
        call["sizeWords"] = (
            "flat" if f < 1 else "ankle to knee high" if f < 2 else
            "knee to waist high" if f < 3 else "waist to chest high" if f < 4 else
            "chest to shoulder high" if f < 5 else "shoulder to head high" if f < 7 else
            "overhead" if f < 9 else "well overhead" if f < 12 else "double overhead plus"
        )
    day, region = e(call.get("day")), e(call.get("region"))
    verdict = (call.get("verdict") or "fun").lower()
    read, caption = e(call.get("read")), call.get("caption") or ""
    face, period, windkt = call.get("faceFt"), call.get("periodS"), call.get("windKt")
    size, wind = e(call.get("sizeWords")), e(call.get("windWords"))
    swell, hour = e(call.get("swellDir")), e(call.get("hourLabel"))

    rows = []
    if face is not None:
        rows.append(("Size", f"{face} ft" + (f" &middot; {size}" if size else "")))
    if period is not None:
        rows.append(("Swell", f"{round(period)} s" + (f" from the {swell}" if swell else "")))
    if windkt is not None:
        rows.append(("Wind", f"{round(windkt)} kt" + (f" &middot; {wind}" if wind else "")))
    elif wind:
        rows.append(("Wind", wind))
    if hour:
        rows.append(("Best window", hour))

    facts = "\n".join(
        f'    <div class="row"><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows
    )

    # The caption goes in the markup as text so a fetcher reads it without
    # running anything, and into the clipboard button from that same element --
    # one copy on the page, so the two can never disagree.
    caption_block = (
        f'<pre id="caption">{html.escape(caption)}</pre>'
        if caption.strip() else
        '<p class="warn">No caption was written for today. Post the card with your own words, '
        'or skip the day.</p>'
    )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Break of the Day: {e(name)} &middot; Boardcall</title>
<meta name="description" content="Boardcall's Break of the Day for {day}: {e(name)}, {region}. Verdict {verdict.upper()}.">
<style>
:root{{color-scheme:light dark;--fire:#E8734A;--fun:#1F6F78;--marginal:#8A74BF;--skip:#6B7280}}
*{{box-sizing:border-box}}
body{{font:17px/1.6 ui-rounded,system-ui,-apple-system,sans-serif;max-width:40rem;
 margin:0 auto;padding:2rem 1.15rem 4rem}}
.eyebrow{{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;opacity:.6;margin:0 0 .5rem}}
h1{{font-size:1.75rem;line-height:1.15;margin:0 0 .2rem;text-wrap:balance}}
p.region{{margin:0 0 1rem;opacity:.75}}
.verdict{{display:inline-block;color:#fff;font-weight:700;font-size:.78rem;letter-spacing:.09em;
 text-transform:uppercase;padding:.3rem .7rem;border-radius:999px;background:var(--{verdict})}}
.read{{font-size:1.1rem;margin:.9rem 0 1.4rem}}
dl{{margin:0 0 1.6rem;border-top:1px solid rgba(128,128,128,.3)}}
.row{{display:flex;gap:1rem;padding:.5rem 0;border-bottom:1px solid rgba(128,128,128,.3)}}
dt{{flex:0 0 7.5rem;opacity:.65;margin:0}}
dd{{margin:0}}
h2{{font-size:1rem;letter-spacing:.04em;text-transform:uppercase;opacity:.6;margin:2rem 0 .6rem}}
canvas{{width:100%;height:auto;border-radius:12px;display:block}}
pre{{white-space:pre-wrap;word-wrap:break-word;font:15px/1.55 ui-monospace,Menlo,monospace;
 background:rgba(128,128,128,.12);border-radius:12px;padding:1rem;margin:0 0 .75rem}}
button,a.btn{{font:600 16px/1 ui-rounded,system-ui,sans-serif;border:0;border-radius:10px;
 padding:.85rem 1.2rem;background:#1F6F78;color:#fff;cursor:pointer;display:inline-block;
 text-decoration:none;margin:0 .5rem .5rem 0}}
button:focus-visible,a.btn:focus-visible{{outline:3px solid #1F6F78;outline-offset:2px}}
.warn{{background:rgba(232,115,74,.15);border-radius:10px;padding:.9rem 1rem}}
.stale{{background:rgba(232,115,74,.2);border:2px solid var(--fire);border-radius:10px;
 padding:1rem;margin:0 0 1.5rem}}
.stale strong{{display:block;margin-bottom:.35rem}}
footer{{margin-top:2.5rem;padding-top:1rem;border-top:1px solid rgba(128,128,128,.3);
 font-size:.85rem;opacity:.7}}
</style>
</head>
<body>

<p class="eyebrow">Boardcall &middot; Break of the Day &middot; {day}</p>
<h1>{e(name)}</h1>
<p class="region">{region}</p>
<p><span class="verdict">{verdict}</span></p>
<p class="read">{read}</p>

<dl>
{facts}
</dl>

<h2>The card</h2>
<canvas id="card" width="1080" height="1350" aria-label="Break of the Day card for {e(name)}"></canvas>
<p style="margin:.8rem 0 0">
  <a class="btn" id="save" download="boardcall-{day}.png" href="#">Save the card</a>
</p>
<p style="font-size:.85rem;opacity:.7;margin:.4rem 0 0">
  On an iPhone you can also press and hold the card and choose Save to Photos.
</p>

<h2>The caption</h2>
{caption_block}
<button id="copy">Copy the caption</button>
{alternates_block(call, e)}

<footer>
<p>One break, the one Boardcall ranked best across its whole catalogue this morning.
Rebuilt daily; this page carries no other content.</p>
<p>Wave and wind data: Open-Meteo (CC BY 4.0).</p>
</footer>

<script src="card.js"></script>
<script>
var BAKED_DAY = {json.dumps(call.get("day") or "")};
var DATA = {json.dumps({
    "name": name, "region": call.get("region"), "verdict": verdict,
    "faceFt": face, "sizeWords": call.get("sizeWords"), "periodS": period,
    "swellDir": call.get("swellDir"), "windKt": windkt,
    "windWords": call.get("windWords"), "hourLabel": call.get("hourLabel"),
    "read": call.get("read"),
})};
(function () {{
  var cv = document.getElementById("card");
  var save = document.getElementById("save");
  function paint() {{
    try {{
      drawCard(cv, DATA);
      save.href = cv.toDataURL("image/png");
    }} catch (err) {{
      save.textContent = "Card could not be drawn";
      save.removeAttribute("href");
    }}
  }}
  paint();
  // The footer logo is an Image(); redraw once it decodes.
  if (typeof ICON_IMG !== "undefined" && !ICON_IMG.complete) ICON_IMG.onload = paint;

  var pre = document.getElementById("caption");
  var copy = document.getElementById("copy");
  if (pre && copy) {{
    copy.addEventListener("click", function () {{
      navigator.clipboard.writeText(pre.textContent).then(function () {{
        copy.textContent = "Copied";
        setTimeout(function () {{ copy.textContent = "Copy the caption"; }}, 1800);
      }}, function () {{
        copy.textContent = "Select it and copy by hand";
      }});
    }});
  }} else if (copy) {{
    copy.remove();
  }}
}})();

// Freshness check. This page is baked once a morning by a scheduled job, and if
// that job stops running -- a dropped schedule, a disabled workflow, an upstream
// miss -- nothing else here would say so: the page would quietly keep showing an
// older break, and whoever is posting would post the wrong one in good faith.
// So the page checks itself against the feed and says plainly when it is behind.
//
// It deliberately does NOT rewrite the post. The markup stays the single source
// of truth for anything fetching this page, so a mismatch gets surfaced rather
// than papered over -- and the two would otherwise disagree with nobody knowing,
// since a fetcher reading the HTML runs none of this.
(function () {{
  if (!window.fetch || !BAKED_DAY) return;
  var ctl = ("AbortController" in window) ? new AbortController() : null;
  if (ctl) setTimeout(function () {{ ctl.abort(); }}, 6000);
  fetch({json.dumps(FEED)}, ctl ? {{signal: ctl.signal}} : undefined)
    .then(function (r) {{ return r.ok ? r.json() : null; }})
    .then(function (j) {{
      var c = j && j.call;
      // ISO dates compare correctly as strings. Only a strictly newer pick counts:
      // an equal or older one means this page is current, or the feed is behind,
      // and neither is cause to alarm anyone.
      if (!c || !c.day || !c.name || !(c.day > BAKED_DAY)) return;
      var n = document.createElement("div");
      n.className = "stale";
      var head = document.createElement("strong");
      head.textContent = "Do not post this — the page is a day behind.";
      var rest = document.createElement("span");
      rest.textContent = "It was built for " + BAKED_DAY + " and today's pick is " +
        c.name + (c.region ? " (" + c.region + ")" : "") + ". The card, caption " +
        "and conditions below are still yesterday's, so the research prompt will " +
        "name the wrong break too. Tell Zach the rebuild stopped.";
      n.appendChild(head);
      n.appendChild(rest);
      document.body.insertBefore(n, document.body.firstChild);
      document.title = "Out of date · " + document.title;
    }})
    .catch(function () {{}});   // a failed check changes nothing on the page
}})();
</script>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page)
    print(f"wrote {OUT} -- {name} ({verdict.upper()}) for {day}, "
          f"caption {len(caption)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
