#!/usr/bin/env python3
"""Generate the self-contained mobile library web app (index.html)."""
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))

def _load(fname, key):
    # prefer the copy bundled next to this script; fall back to the session scratchpad
    local = os.path.join(HERE, fname)
    scratch = os.path.join(
        r"C:\Users\Steve\AppData\Local\Temp\claude\C--dev-ObsidianVault-ObsidianVault"
        r"\2ef35477-4160-4d6e-9403-b239e2d9c9cd\scratchpad", fname)
    path = local if os.path.exists(local) else scratch
    return json.load(open(path, encoding="utf-8"))[key]

books = _load("books_enriched.json", "books")
series_db_raw = _load("series_db.json", "series")

# ---- map owned books to series by orig_title ----
SERIES_OF = {
    "A Botanist's Guide to Parties and Poisons": "Saffron Everleigh Mysteries",
    "A Botanist's Guide to Flowers and Fatality": "Saffron Everleigh Mysteries",
    "The Silkworm": "Cormoran Strike",
    "Hard Rain": "Annie McIntyre Mysteries",
    "The Book Charmer": "Dove Pond",
    "The House of Secrets": "House of Secrets",
    "Mitch Rapp series (multiple)": "Mitch Rapp",
    "Women's Murder Club series (multiple)": "Women's Murder Club",
    "Code of Conduct": "Scot Harvath",
    "Foreign Agent": "Scot Harvath",
    "Rising Tiger": "Scot Harvath",
    "Op-Center / EndWar (multiple)": "Tom Clancy's Op-Center",
    "Agatha Christie mysteries (multiple)": "Hercule Poirot",
    "Foxfire": "Foxfire",
    "Lost Roses": "Woolsey Family",
}
# books that represent "several volumes, specific titles unknown"
PLACEHOLDER = {
    "Mitch Rapp series (multiple)", "Women's Murder Club series (multiple)",
    "Op-Center / EndWar (multiple)", "Agatha Christie mysteries (multiple)",
    "Foxfire", "Jane Austen collection", "Stephen King novels (multiple)",
    "Jodi Picoult novels (multiple)",
}

catalog = []
for i, b in enumerate(books):
    ot = b.get("orig_title", b.get("title", ""))
    catalog.append({
        "id": i + 1,
        "title": b.get("title", ""),
        "author": b.get("author", ""),
        "genre": b.get("genre", "") or "Uncategorized",
        "year": b.get("first_published", ""),
        "shelf": b.get("shelf", ""),
        "series": SERIES_OF.get(ot, ""),
        "placeholder": ot in PLACEHOLDER,
        "isbn": b.get("isbn13", ""),
        "cover": b.get("cover", ""),
        "confidence": b.get("confidence", ""),
        "notes": b.get("notes", ""),
    })

# ---- build SERIES_DB dict from workflow output ----
series_db = {}
for s in series_db_raw:
    name = s.get("series", "")
    if not name:
        continue
    series_db[name] = {
        "author": s.get("author", ""),
        "total_published": s.get("total_published", ""),
        "note": s.get("note", ""),
        "entries": [
            {
                "index": e.get("index", ""),
                "title": e.get("title", ""),
                "year": e.get("year", ""),
                "status": e.get("status", "published"),
                "release_date": e.get("release_date", ""),
            }
            for e in s.get("entries", [])
        ],
    }

# manual small series not covered by the workflow
if "Woolsey Family" not in series_db:
    series_db["Woolsey Family"] = {
        "author": "Martha Hall Kelly",
        "total_published": "3",
        "note": "Connected Woolsey-family historical novels (read in publication order).",
        "entries": [
            {"index": "1", "title": "Lilac Girls", "year": "2016", "status": "published", "release_date": ""},
            {"index": "2", "title": "Lost Roses", "year": "2019", "status": "published", "release_date": ""},
            {"index": "3", "title": "Sunflower Sisters", "year": "2021", "status": "published", "release_date": ""},
        ],
    }

STORES = {
    "generated": "2026-07-05",
    "local": [
        {"name": "Millard Oakley Public Library", "city": "Livingston, TN", "kind": "Borrow (local library)",
         "url": "https://overtoncountytn.com/library/", "phone": "(931) 823-1888",
         "addr": "107 E. Main St, Livingston, TN 38570", "search": ""},
        {"name": "Plenty Downtown Bookshop", "city": "Cookeville, TN (~20 min)", "kind": "Local indie — new books",
         "url": "https://bookshop.org/shop/plentybookshop", "phone": "(931) 349-2119",
         "addr": "41 W. Broad St, Cookeville, TN 38501", "search": ""},
        {"name": "Books-A-Million", "city": "Cookeville, TN (~20 min)", "kind": "Chain — new books",
         "url": "https://www.booksamillion.com/", "phone": "(931) 528-2500",
         "addr": "401 W Jackson St Ste 290, Cookeville, TN 38501",
         "search": "https://www.booksamillion.com/search?query="},
    ],
    "online": [
        {"name": "Amazon", "search": "https://www.amazon.com/s?k="},
        {"name": "Bookshop.org", "search": "https://bookshop.org/beta-search?keywords="},
        {"name": "ThriftBooks (used)", "search": "https://www.thriftbooks.com/browse/?b.search="},
        {"name": "AbeBooks (used/rare)", "search": "https://www.abebooks.com/servlet/SearchResults?kn="},
    ],
}

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#5b7263">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Library">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" type="image/png" href="favicon.png">
<title>Our Library</title>
<style>
:root{
  --paper:#f5f1e8; --card:#fffdf8; --ink:#2b2b28; --muted:#7d786c;
  --sage:#5b7263; --sage-dark:#425146; --sage-light:#8ca392; --line:#e4ddcd;
  --accent:#b8683f; --up:#8a6d3b; --shadow:0 2px 8px rgba(60,50,30,.10);
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0;overflow-x:hidden}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:var(--paper);color:var(--ink);font-size:15px;line-height:1.4;
  padding-bottom:env(safe-area-inset-bottom)}
button{font-family:inherit;cursor:pointer;border:none;background:none;color:inherit}
a{color:var(--sage);text-decoration:none}
img{display:block}

/* header */
header{position:sticky;top:0;z-index:50;background:var(--sage);color:#fff;
  padding:calc(env(safe-area-inset-top) + 10px) 12px 8px;box-shadow:0 2px 10px rgba(0,0,0,.15)}
.hrow{display:flex;align-items:center;gap:10px}
.brand{font-weight:700;font-size:18px;letter-spacing:.2px;display:flex;align-items:baseline;gap:8px}
.brand .cnt{font-size:12px;font-weight:500;opacity:.85}
.gear{margin-left:auto;font-size:20px;width:36px;height:36px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.14)}
.searchwrap{margin-top:8px;position:relative}
.searchwrap input{width:100%;padding:9px 12px 9px 34px;border-radius:20px;border:none;
  font-size:15px;background:rgba(255,255,255,.95);color:var(--ink)}
.searchwrap svg{position:absolute;left:11px;top:9px;width:16px;height:16px;opacity:.5}
.tabs{display:flex;gap:4px;margin-top:9px;background:rgba(255,255,255,.12);padding:3px;border-radius:12px;overflow-x:auto;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tabs button{flex:1 0 auto;min-width:52px;padding:7px 6px;border-radius:9px;font-size:11.5px;font-weight:600;color:#fff;opacity:.8;white-space:nowrap}
.tabs button.on{background:var(--card);color:var(--sage-dark);opacity:1;box-shadow:var(--shadow)}
.sortbar{display:flex;align-items:center;gap:8px;margin-top:8px;font-size:12.5px;color:rgba(255,255,255,.9)}
.sortbar select{background:rgba(255,255,255,.95);color:var(--ink);border:none;border-radius:8px;
  padding:5px 8px;font-size:12.5px;font-family:inherit}
.libbar{display:flex;align-items:center;gap:7px;margin-top:8px;font-size:12.5px}
.lbsel{background:rgba(255,255,255,.95);color:var(--ink);border:none;border-radius:8px;padding:6px 8px;
  font-size:12.5px;font-family:inherit;max-width:34vw}
.layout{display:flex;gap:0;background:rgba(255,255,255,.14);border-radius:8px;padding:2px;flex:none}
.layout button{width:30px;height:26px;border-radius:6px;color:#fff;opacity:.75;font-size:14px;line-height:1}
.layout button.on{background:var(--card);color:var(--sage-dark);opacity:1}
.libbar #viewnote{margin-left:auto;color:rgba(255,255,255,.85);white-space:nowrap}

main{padding:12px 12px 40px;max-width:820px;margin:0 auto}

/* covers grid */
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
@media(min-width:520px){.grid{grid-template-columns:repeat(4,1fr)}}
@media(min-width:700px){.grid{grid-template-columns:repeat(5,1fr)}}
.bcard{background:var(--card);border-radius:10px;overflow:hidden;box-shadow:var(--shadow);
  display:flex;flex-direction:column;border:1px solid var(--line)}
.cover{position:relative;width:100%;aspect-ratio:2/3;background:linear-gradient(135deg,var(--sage-light),var(--sage));
  overflow:hidden}
.cover img{width:100%;height:100%;object-fit:cover}
.cover .ph{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;
  padding:8px;color:#fff;text-align:center}
.cover .ph .t{font-size:11px;font-weight:700;line-height:1.25;overflow:hidden;
  display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical}
.cover .ph .a{font-size:9px;opacity:.85;margin-top:6px}
.badge{position:absolute;top:6px;left:6px;background:var(--sage-dark);color:#fff;font-size:9.5px;
  font-weight:700;padding:2px 6px;border-radius:20px}
.badge.multi{background:var(--accent)}
.binfo{padding:6px 7px 8px}
.binfo .bt{font-size:11.5px;font-weight:600;line-height:1.2;overflow:hidden;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.binfo .ba{font-size:10px;color:var(--muted);margin-top:2px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}

/* grouped list (authors/genres) */
.group{margin-bottom:8px;background:var(--card);border-radius:12px;border:1px solid var(--line);
  overflow:hidden;box-shadow:var(--shadow)}
.ghead{display:flex;align-items:center;gap:8px;padding:11px 13px;font-weight:700;cursor:pointer}
.ghead .gc{margin-left:auto;font-size:12px;color:var(--muted);font-weight:600}
.ghead .chev{transition:transform .2s;color:var(--sage);font-size:13px}
.group.open .chev{transform:rotate(90deg)}
.glist{display:none;padding:0 6px 8px}
.group.open .glist{display:block}
.row{display:flex;gap:10px;padding:8px 8px;border-top:1px solid var(--line);align-items:center}
.row .mini{width:34px;height:51px;border-radius:4px;flex:none;background:var(--sage-light);
  overflow:hidden;position:relative}
.row .mini img{width:100%;height:100%;object-fit:cover}
.row .mini .mph{position:absolute;inset:0;font-size:8px;color:#fff;padding:3px;font-weight:700;
  overflow:hidden;line-height:1.1}
.row .rt{font-size:13.5px;font-weight:600;line-height:1.25}
.row .rs{font-size:11.5px;color:var(--muted);margin-top:2px}
.row.lg .mini{width:42px;height:63px;border-radius:5px}
.row .rmain{min-width:0}
.row .rmain .rt{overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.row .rmain .rs{overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.lser{color:var(--sage);font-weight:600}

/* series view */
.scard{background:var(--card);border-radius:14px;border:1px solid var(--line);box-shadow:var(--shadow);
  padding:13px 14px 14px;margin-bottom:12px}
.scard.coming{border:1px solid var(--up);background:linear-gradient(180deg,rgba(138,109,59,.10),var(--card))}
.scard.coming h3{color:var(--up)}
.scard h3{margin:0;font-size:16px}
.scard .sauth{font-size:12px;color:var(--muted);margin-top:1px}
.prog{display:flex;align-items:center;gap:9px;margin:10px 0 4px}
.bar{flex:1;height:8px;background:var(--line);border-radius:8px;overflow:hidden}
.bar > i{display:block;height:100%;background:var(--sage);border-radius:8px}
.prog .pl{font-size:12px;font-weight:700;color:var(--sage-dark);white-space:nowrap}
.snote{font-size:11.5px;color:var(--muted);margin-top:2px;font-style:italic}
.entries{margin-top:11px;display:flex;flex-direction:column;gap:2px}
.ent{display:flex;align-items:center;gap:9px;padding:6px 4px;border-radius:8px}
.ent .num{width:22px;height:22px;border-radius:6px;background:var(--line);color:var(--muted);
  font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}
.ent.have{background:rgba(91,114,99,.09)}
.ent.have .num{background:var(--sage);color:#fff}
.ent.up .num{background:var(--up);color:#fff}
.ent .et{font-size:13px;font-weight:600;line-height:1.2}
.ent.miss .et{color:var(--muted);font-weight:500}
.ent .ey{font-size:11px;color:var(--muted)}
.ent .tag{margin-left:auto;font-size:10px;font-weight:700;padding:2px 7px;border-radius:20px;flex:none}
.tag.h{background:var(--sage);color:#fff}
.tag.m{background:#efe7d6;color:var(--muted)}
.tag.u{background:var(--up);color:#fff}
.check{margin-left:auto;flex:none;color:var(--sage);font-size:15px}
.ent.cur{outline:2px solid var(--sage);outline-offset:-2px;background:rgba(91,114,99,.14)}
.curtag{color:var(--sage);font-size:10px;font-weight:700;margin-left:4px}
.subnote{margin-top:8px;font-size:12px;color:var(--muted)}
.ent[onclick]:active,.ent[data-wishadd]:active{background:rgba(91,114,99,.2)}
.wish{margin-left:auto;flex:none;font-size:18px;line-height:1;color:var(--muted);padding-left:8px}
.wish.on{color:var(--accent)}
.ent .tag.u + .wish{margin-left:8px}
.wremove{margin-left:auto;flex:none;font-size:20px;color:var(--accent);width:36px;height:36px}
.wishrow{align-items:center}
.winput{width:100%;padding:12px;border:1px solid var(--line);border-radius:11px;font-size:15px;margin-bottom:10px;background:var(--card);font-family:inherit}
.winput:focus{outline:2px solid var(--sage-light);border-color:var(--sage)}

/* detail sheet */
.scrim{position:fixed;inset:0;background:rgba(30,26,18,.5);z-index:100;opacity:0;
  pointer-events:none;transition:opacity .2s}
.scrim.on{opacity:1;pointer-events:auto}
.sheet{position:fixed;left:0;right:0;bottom:0;z-index:101;background:var(--paper);
  border-radius:18px 18px 0 0;max-height:92vh;overflow-y:auto;transform:translateY(102%);
  transition:transform .28s cubic-bezier(.2,.8,.2,1);padding-bottom:calc(env(safe-area-inset-bottom) + 20px)}
.sheet.on{transform:translateY(0)}
.grab{width:40px;height:5px;border-radius:5px;background:var(--line);margin:9px auto 4px}
.dtop{display:flex;gap:14px;padding:8px 16px 4px}
.dcover{width:104px;flex:none;aspect-ratio:2/3;border-radius:9px;overflow:hidden;box-shadow:var(--shadow);
  background:var(--sage-light);position:relative}
.dcover img{width:100%;height:100%;object-fit:cover}
.dmeta h2{margin:2px 0 3px;font-size:19px;line-height:1.2}
.dmeta .dau{font-size:14px;color:var(--sage-dark);font-weight:600}
.dmeta .drow{font-size:12.5px;color:var(--muted);margin-top:6px}
.dmeta .pill{display:inline-block;background:#efe7d6;color:var(--muted);font-size:11px;font-weight:600;
  padding:3px 9px;border-radius:20px;margin:6px 6px 0 0}
.dmeta .pill.coll{background:var(--sage);color:#fff}
.dnotes{padding:8px 16px 0;font-size:12.5px;color:var(--muted);font-style:italic}
.sect{padding:14px 16px 0}
.sect h4{margin:0 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--sage-dark)}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.buy{display:flex;flex-direction:column;padding:10px 12px;background:var(--card);border:1px solid var(--line);
  border-radius:11px;box-shadow:var(--shadow)}
.buy .bn{font-weight:700;font-size:13.5px}
.buy .bk{font-size:11px;color:var(--muted);margin-top:2px}
.buy.local{border-color:var(--sage-light);background:rgba(91,114,99,.06)}
.miniprog{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:11px 13px;margin-top:4px}

/* settings */
.panel{padding:16px}
.panel h3{margin:0 0 4px}
.imp{display:block;width:100%;text-align:center;padding:13px;background:var(--sage);color:#fff;
  font-weight:700;border-radius:12px;margin-top:12px;font-size:15px}
.imp.sec{background:var(--card);color:var(--sage-dark);border:1px solid var(--line)}
.hint{font-size:12.5px;color:var(--muted);margin-top:12px;line-height:1.5;background:var(--card);
  border:1px solid var(--line);border-radius:12px;padding:12px}
.hint b{color:var(--ink)}
.hint ol{margin:6px 0 0;padding-left:18px}
.empty{text-align:center;color:var(--muted);padding:50px 20px;font-size:14px}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(80px);z-index:200;
  background:var(--sage-dark);color:#fff;padding:11px 18px;border-radius:24px;font-size:13.5px;
  box-shadow:0 6px 20px rgba(0,0,0,.25);transition:transform .25s;max-width:90vw}
.toast.on{transform:translateX(-50%) translateY(0)}

/* dark mode */
html[data-theme="dark"]{
  --paper:#1c1e1b; --card:#26302a; --ink:#ece7dc; --muted:#9aa39a;
  --sage:#6f8a78; --sage-dark:#9db6a5; --sage-light:#42514a; --line:#33403a;
  --accent:#d98a5c; --up:#c8a765; --shadow:0 2px 8px rgba(0,0,0,.35);
}
html[data-theme="dark"] .tag.m{background:#33403a;color:var(--muted)}
html[data-theme="dark"] .cover .ph, html[data-theme="dark"] .row .mini .mph{color:#e8e2d5}

/* filter + status chips */
.filterbar{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;padding:2px 0 0}
.filterbar::-webkit-scrollbar{display:none}
.chip{flex:0 0 auto;font-size:12px;font-weight:600;padding:5px 11px;border-radius:20px;
  background:rgba(255,255,255,.14);color:#fff;white-space:nowrap;border:none}
.chip.on{background:var(--card);color:var(--sage-dark)}
.statusdot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px;vertical-align:middle}
.sd-read{background:var(--sage)} .sd-reading{background:var(--accent)} .sd-toread{background:var(--up)}
.covtag{position:absolute;bottom:6px;left:6px;background:rgba(43,43,40,.82);color:#fff;font-size:9px;
  font-weight:700;padding:2px 6px;border-radius:20px}
.covtag.reading{background:var(--accent)} .covtag.read{background:var(--sage)}

/* stars */
.stars{display:flex;gap:3px;font-size:24px;line-height:1;color:var(--line)}
.stars span{cursor:pointer;color:var(--line)}
.stars span.lit{color:var(--up)}
.ministars{color:var(--up);font-size:12px;letter-spacing:1px}

/* status segmented in detail */
.seg{display:flex;gap:0;border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-top:6px}
.seg button{flex:1;padding:9px 4px;font-size:12.5px;font-weight:600;color:var(--muted);background:var(--card)}
.seg button.on{background:var(--sage);color:#fff}

/* stats */
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.statcard{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:13px 14px;box-shadow:var(--shadow)}
.statcard .num{font-size:26px;font-weight:800;color:var(--sage-dark)}
.statcard .lab{font-size:12px;color:var(--muted);margin-top:2px}
.statsect{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:14px;margin-bottom:12px;box-shadow:var(--shadow)}
.statsect h4{margin:0 0 10px;font-size:13px;text-transform:uppercase;letter-spacing:.5px;color:var(--sage-dark)}
.brow{display:flex;align-items:center;gap:8px;margin-bottom:7px;font-size:12.5px}
.brow .bl{width:38%;flex:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.brow .bt{flex:1;height:9px;background:var(--line);border-radius:6px;overflow:hidden}
.brow .bt i{display:block;height:100%;background:var(--sage);border-radius:6px}
.brow .bn{flex:none;color:var(--muted);width:26px;text-align:right;font-weight:600}

/* edit form */
.efield{margin-bottom:10px}
.efield label{display:block;font-size:11px;font-weight:700;color:var(--sage-dark);text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}
.efield input,.efield textarea,.efield select{width:100%;padding:10px;border:1px solid var(--line);border-radius:10px;
  font-size:14px;background:var(--card);color:var(--ink);font-family:inherit}
.efield textarea{min-height:64px;resize:vertical}
.danger{background:#fff;color:#b5433a;border:1px solid #e3b7b2}
html[data-theme="dark"] .danger{background:var(--card)}
.editbtn{position:absolute;top:10px;right:14px;font-size:13px;font-weight:700;color:var(--sage);background:var(--card);
  border:1px solid var(--line);border-radius:20px;padding:5px 12px}
.scanwrap{position:relative;background:#000;border-radius:12px;overflow:hidden;aspect-ratio:4/3;margin:10px 0}
.scanwrap video{width:100%;height:100%;object-fit:cover}
.scanline{position:absolute;left:8%;right:8%;top:50%;height:2px;background:var(--accent);box-shadow:0 0 8px var(--accent)}
.setgrp{margin-top:16px}
.setlab{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);margin-bottom:2px}
.setgrp .imp{margin-top:8px}
/* shelf / bookcase visualization — real cover art standing on wooden shelves */
.shelfwrap{margin-bottom:16px}
.shelfhdr{font-size:12px;font-weight:700;color:var(--sage-dark);text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}
.shelfhdr span{color:var(--muted);font-weight:600}
.shelf{display:flex;flex-wrap:wrap;align-items:flex-end;gap:7px 6px;padding:16px 12px 0;
  background:linear-gradient(180deg,rgba(120,86,52,.10),transparent 60%);
  border-bottom:11px solid #6b4e34;border-radius:4px;
  box-shadow:inset 0 -16px 18px -14px rgba(0,0,0,.45), 0 3px 0 #543c28}
.shelfbook{width:48px;height:72px;flex:none;border-radius:2px 3px 3px 2px;overflow:hidden;cursor:pointer;
  position:relative;background:var(--sage-light);
  box-shadow:1px 3px 5px rgba(0,0,0,.35), inset 2px 0 3px -1px rgba(255,255,255,.25), inset -2px 0 3px -1px rgba(0,0,0,.3)}
.shelfbook img{width:100%;height:100%;object-fit:cover;display:block}
.shelfbook .ph{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:2px;color:#fff}
.shelfbook .ph span{writing-mode:vertical-rl;text-orientation:mixed;font-size:8px;font-weight:700;line-height:1.05;
  max-height:100%;overflow:hidden;text-align:center}
.shelfbook:active{transform:translateY(-3px)}
</style>
</head>
<body>
<header>
  <div class="hrow">
    <div class="brand">Our Library <span class="cnt" id="count"></span></div>
    <button class="gear" id="gear" aria-label="Settings">&#9881;</button>
  </div>
  <div class="searchwrap">
    <svg viewBox="0 0 24 24" fill="none" stroke="#333" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
    <input id="q" type="search" placeholder="Search title, author, series..." autocomplete="off">
  </div>
  <div class="tabs" id="tabs">
    <button data-v="library" class="on">Library</button>
    <button data-v="series">Series</button>
    <button data-v="wishlist">Wishlist</button>
    <button data-v="stats">Stats</button>
  </div>
  <div class="libbar" id="libbar">
    <div class="layout" id="layout">
      <button data-l="covers" class="on" aria-label="Cover grid">▦</button>
      <button data-l="list" aria-label="List">☰</button>
      <button data-l="shelf" aria-label="Shelf view">📚</button>
    </div>
    <select id="groupby" class="lbsel" aria-label="Group by">
      <option value="none">All books</option>
      <option value="author">By author</option>
      <option value="genre">By genre</option>
      <option value="collection">By collection</option>
      <option value="shelf">By shelf</option>
      <option value="type">By type</option>
    </select>
    <select id="sort" class="lbsel" aria-label="Sort">
      <option value="author">Author A–Z</option>
      <option value="title">Title A–Z</option>
      <option value="year_new">Year ↓</option>
      <option value="year_old">Year ↑</option>
      <option value="added">Added</option>
      <option value="rating">Rating</option>
    </select>
    <span id="viewnote"></span>
  </div>
  <div class="filterbar" id="filterbar">
    <button class="chip on" data-f="">All</button>
    <button class="chip" data-f="toread">To-read</button>
    <button class="chip" data-f="reading">Reading</button>
    <button class="chip" data-f="read">Read</button>
    <button class="chip" data-f="rated">Rated ★</button>
  </div>
</header>

<main id="main"></main>

<div class="scrim" id="scrim"></div>
<div class="sheet" id="sheet"><div class="grab"></div><div id="sheetbody"></div></div>
<div class="toast" id="toast"></div>

<!-- hidden settings sheet reuses .sheet via id -->
<script>
const CATALOG = /*CATALOG*/;
const SERIES_DB = /*SERIESDB*/;
const STORES = /*STORES*/;

/* ---------- state ---------- */
let books = load();
const pref = (k,d)=>{ try{ const v=localStorage.getItem(k); return v==null?d:v; }catch(e){ return d; } };
let view = pref("lib_view","library"), layout = pref("lib_layout","covers"), groupBy = pref("lib_group","none");
let sortBy = pref("lib_sort","author"), query = "", statusFilter = "", READONLY = false;
const norm = s => (s||"").toLowerCase().replace(/^(the|a|an) /,"").replace(/[^a-z0-9]+/g," ").trim();
const enc = s => encodeURIComponent(s);
const nextId = () => (books.reduce((m,b)=>Math.max(m, +b.id||0), 0) + 1);

function load(){
  try{ const s = localStorage.getItem("lib_books"); if(s) return JSON.parse(s); }catch(e){}
  return CATALOG.map(b=>({...b}));
}
function persist(){ if(READONLY) return; try{ localStorage.setItem("lib_books", JSON.stringify(books)); }catch(e){} scheduleSync(); }

/* ---------- theme ---------- */
function applyTheme(t){ if(t==="dark"){ document.documentElement.setAttribute("data-theme","dark"); document.querySelector('meta[name=theme-color]').setAttribute("content","#26302a"); } else { document.documentElement.removeAttribute("data-theme"); document.querySelector('meta[name=theme-color]').setAttribute("content","#5b7263"); } }
function toggleTheme(){ const cur=localStorage.getItem("lib_theme")==="dark"?"":"dark"; localStorage.setItem("lib_theme",cur); applyTheme(cur); closeSheet(); }
applyTheme(localStorage.getItem("lib_theme"));

/* ---------- sync (shared file over tailnet HTTPS; last-write-wins) ---------- */
const DEFAULT_SYNC = "https://books.retrogaming.win";  // public sync (Cloudflare tunnel -> home TrueNAS)
const syncURL = () => { let v=localStorage.getItem("lib_sync_url"); if(v===null) v=DEFAULT_SYNC; return (v||"").trim().replace(/\/+$/,""); };
let _syncT=null, _syncing=false;
function scheduleSync(){ if(!syncURL()) return; clearTimeout(_syncT); _syncT=setTimeout(pushSync, 1500); }
async function pushSync(silent){
  if(READONLY) return;
  const url=syncURL(); if(!url) return;
  const payload={ updated:Date.now(), books, wishlist };
  try{
    await fetch(url+"/library", {method:"PUT", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
    localStorage.setItem("lib_sync_at", String(payload.updated));
    if(!silent) toast("Synced ↑");
  }catch(e){ if(!silent) toast("Sync failed — endpoint offline"); }
}
async function pullSync(silent){
  const url=syncURL(); if(!url){ if(!silent) toast("Set a sync endpoint first"); return; }
  try{
    const r=await fetch(url+"/library",{cache:"no-store"}); if(!r.ok) throw 0;
    const d=await r.json();
    const localAt=+(localStorage.getItem("lib_sync_at")||0);
    if(d && d.updated && d.updated>localAt && Array.isArray(d.books)){
      books=d.books; wishlist=d.wishlist||[];
      localStorage.setItem("lib_books",JSON.stringify(books));
      localStorage.setItem("lib_wishlist",JSON.stringify(wishlist));
      localStorage.setItem("lib_sync_at",String(d.updated));
      render(); if(!silent) toast("Pulled latest ↓");
    } else if(!silent) toast("Already up to date");
  }catch(e){ if(!silent) toast("Sync failed — endpoint offline"); }
}

/* ---------- wishlist ---------- */
let wishlist = (()=>{ try{ return JSON.parse(localStorage.getItem("lib_wishlist")||"[]"); }catch(e){ return []; } })();
function saveWish(){ try{ localStorage.setItem("lib_wishlist", JSON.stringify(wishlist)); }catch(e){} scheduleSync(); }
function gotIt(key){ const w=wishlist.find(x=>x.key===key); if(!w) return;
  books.push({ id:nextId(), title:w.title, author:w.author, genre:w.genre||"Uncategorized", year:w.year||"", shelf:"Added", series:w.series||"", placeholder:false, isbn:w.isbn||"", cover:w.cover||"", status:"toread", rating:0, notes:"", added:Date.now() });
  removeWish(key); persist(); }
function toggleWishPriority(key){ const w=wishlist.find(x=>x.key===key); if(w){ w.priority=!w.priority; saveWish(); render(); } }
const wkey = (title,author)=> norm(title)+"|"+norm(author||"");
function isWished(title,author){ return wishlist.some(w=>w.key===wkey(title,author)); }
function ownedAlready(title){ return books.some(b=>!b.placeholder && norm(b.title)===norm(title)); }
function addWish(item){
  const key = wkey(item.title, item.author);
  if(wishlist.some(w=>w.key===key)) return false;
  const w = {key, id:"w"+key, title:item.title, author:item.author||"", series:item.series||"",
    index:item.index||"", year:item.year||"", release_date:item.release_date||"", status:item.status||"", isbn:item.isbn||"", cover:item.cover||""};
  wishlist.push(w); saveWish();
  if(!w.cover) resolveCover(w).then(u=>{ if(u){ w.cover=u; saveWish(); } });
  return true;
}
function removeWish(key){ wishlist = wishlist.filter(w=>w.key!==key); saveWish(); }
function toggleWishEntry(seriesName, title){
  const db = SERIES_DB[seriesName];
  const e = db ? db.entries.find(x=>norm(x.title)===norm(title)) : null;
  const author = db?db.author:"";
  const key = wkey(title, author);
  if(wishlist.some(w=>w.key===key)){ removeWish(key); toast("Removed from wishlist"); }
  else { addWish({title, author, series:seriesName, index:e?e.index:"", year:e?e.year:"", release_date:e?(e.release_date||""):"", status:e?e.status:""}); toast("Added to wishlist ♥"); }
  render();
}

/* ---------- cover fetching (Open Library) ---------- */
const coverCache = JSON.parse(localStorage.getItem("lib_covers")||"{}");
function saveCovers(){ try{ localStorage.setItem("lib_covers", JSON.stringify(coverCache)); }catch(e){} }
const ckey = b => b.isbn ? "i:"+b.isbn : "t:"+norm(b.title)+"|"+norm(b.author);
async function gbThumb(q){
  try{
    const r = await fetch("https://www.googleapis.com/books/v1/volumes?country=US&maxResults=3&q="+enc(q));
    const j = await r.json();
    for(const it of (j.items||[])){
      const il = (it.volumeInfo||{}).imageLinks||{};
      const t = il.thumbnail||il.smallThumbnail;
      if(t) return t.replace("http://","https://").replace("&edge=curl","").replace(/zoom=\d/,"zoom=1");
    }
  }catch(e){}
  return "";
}
async function resolveCover(b){
  if(b.cover) return b.cover;                 // pre-resolved & baked in — instant, no network
  const k = ckey(b);
  if(coverCache[k]!==undefined) return coverCache[k];
  let url = "";
  try{
    const t = b.title.replace(/\s*\(multiple\).*/i,"").replace(/\s*series.*/i,"").replace(/ collection/i,"").split(":")[0];
    if(b.isbn){
      url = await gbThumb("isbn:"+b.isbn);                                   // Google Books by ISBN (canonical)
      if(!url) url = "https://covers.openlibrary.org/b/isbn/"+encodeURIComponent(b.isbn)+"-L.jpg?default=false";
    } else {
      const r = await fetch("https://openlibrary.org/search.json?limit=1&fields=cover_i,isbn&title="+enc(t)+"&author="+enc(b.author));
      const j = await r.json();
      const d = (j.docs&&j.docs[0])||{};
      if(d.cover_i) url = "https://covers.openlibrary.org/b/id/"+d.cover_i+"-M.jpg";
      if(!url) url = await gbThumb("intitle:"+t+(b.author?(" inauthor:"+b.author.split(" and ")[0]):""));   // Google Books fallback
      else if(d.isbn&&d.isbn[0]) url = "https://covers.openlibrary.org/b/isbn/"+d.isbn[0]+"-M.jpg?default=false";
    }
  }catch(e){ url=""; }
  coverCache[k]=url; saveCovers(); return url;
}
function setCover(el,url){ return new Promise(res=>{ const img=new Image();
  img.onload=()=>{ el.querySelector("img")?.remove(); const ph=el.querySelector(".ph,.mph"); if(ph) ph.style.display="none"; el.insertBefore(img, el.firstChild); res(true); };
  img.onerror=()=>res(false); img.src=url; img.alt=""; }); }

let pendingCovers=[], coverBusy=0;
function inView(el){ const r=el.getBoundingClientRect(); return r.bottom > -500 && r.top < (window.innerHeight||812)+500; }
async function pumpCovers(){
  if(coverBusy>=12) return;
  const idx = pendingCovers.findIndex(inView);
  if(idx<0) return;
  const el = pendingCovers.splice(idx,1)[0];
  coverBusy++;
  try{ const b=books.find(x=>x.id==el.dataset.id)||wishlist.find(w=>w.id==el.dataset.id); if(b){ const url=await resolveCover(b); if(url) await setCover(el,url); } }catch(e){}
  coverBusy--; pumpCovers();
}
function wireCovers(root){
  pendingCovers = [...root.querySelectorAll("[data-id]")].filter(el=>el.querySelector(".ph,.mph"));
  for(let i=0;i<12;i++) pumpCovers();
}
let _scrollT;
addEventListener("scroll", ()=>{ clearTimeout(_scrollT); _scrollT=setTimeout(()=>{ for(let i=0;i<6;i++) pumpCovers(); },120); }, {passive:true});
addEventListener("resize", ()=>{ for(let i=0;i<6;i++) pumpCovers(); });

/* ---------- helpers ---------- */
const esc = s => (s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
// collapse the fine-grained genre into one of 10 fixed shelves (also handles arbitrary imported genres)
function topGenre(g){
  const s=(g||"").toLowerCase();
  if(/child|young adult|juvenile|picture book|\bya\b/.test(s)) return "Children's & YA";
  if(/histor/.test(s) && /\bfiction\b/.test(s)) return "Historical Fiction";
  if(/fantasy|science fiction|sci-?fi|dystop/.test(s)) return "Sci-Fi & Fantasy";
  if(/thriller|mystery|crime|suspense|detective|horror/.test(s)) return "Mystery & Thriller";
  if(/classic/.test(s)) return "Classics";
  if(/\bfiction\b|literary|novel|romance|poetry/.test(s)) return "Fiction & Literature";
  if(/relig|christ|spiritual|theolog|occult|philosoph/.test(s)) return "Religion & Philosophy";
  if(/health|medic|wellness|self.?help|psycholog|business|diet|fitness/.test(s)) return "Health & Self-Help";
  if(/politic|histor|memoir|biograph|government|current affairs|strateg|nonfiction/.test(s)) return "History & Politics";
  if(/cook|homestead|garden|veterin|blacksmith|science|nature|reference|craft|survival|preserv/.test(s)) return "Home & Reference";
  return "Fiction & Literature";
}
function matchesFilter(b){
  if(!statusFilter) return true;
  if(statusFilter==="rated") return (b.rating||0)>0;
  return (b.status||"")===statusFilter;
}
function filtered(){
  const q = norm(query);
  let a = books.filter(b=> matchesFilter(b) && (!q || norm(b.title).includes(q)||norm(b.author).includes(q)||norm(b.series).includes(q)||norm(b.genre).includes(q)||(b.isbn&&b.isbn.includes(query.trim()))));
  const lastName = s => { const p=(s||"").trim().split(" "); return p[p.length-1]||""; };
  a.sort((x,y)=>{
    if(sortBy==="title") return norm(x.title).localeCompare(norm(y.title));
    if(sortBy==="year_new") return (parseInt(y.year)||-9999)-(parseInt(x.year)||-9999);
    if(sortBy==="year_old") return (parseInt(x.year)||9999)-(parseInt(y.year)||9999);
    if(sortBy==="added") return (y.added||0)-(x.added||0);
    if(sortBy==="rating") return (y.rating||0)-(x.rating||0) || norm(x.title).localeCompare(norm(y.title));
    return norm(lastName(x.author)+" "+x.title).localeCompare(norm(lastName(y.author)+" "+y.title));
  });
  return a;
}
const TYPE_LABEL={book:"Book",movie:"Movie",music:"Music",game:"Video game",boardgame:"Board game",other:"Other"};
const TYPE_ICON={movie:"🎬",music:"🎵",game:"🎮",boardgame:"🎲",other:"📦"};
const typeTag = b => (b.type&&b.type!=="book"&&TYPE_ICON[b.type]) ? `<span class="covtag" style="background:var(--sage-dark)">${TYPE_ICON[b.type]} ${esc(TYPE_LABEL[b.type])}</span>` : "";
const STATUS_LABEL={toread:"To-read",reading:"Reading",read:"Read"};
function statusBadge(b){ const s=b.status; if(!s||!STATUS_LABEL[s]) return ""; return `<span class="covtag ${s}">${s==="reading"?"Reading":s==="read"?"Read":"To-read"}</span>`; }
function ministars(n){ n=n||0; return n?`<span class="ministars">${"★".repeat(n)}${"☆".repeat(5-n)}</span>`:""; }

/* ---------- views ---------- */
function render(){
  document.getElementById("count").textContent = books.length+" books";
  const inLib = (view==="library");
  document.getElementById("libbar").style.display = inLib?"flex":"none";
  document.getElementById("filterbar").style.display = inLib?"flex":"none";
  const m = document.getElementById("main");
  if(view==="wishlist"){ renderWishlist(m); wireCovers(m); return; }
  if(view==="stats"){ renderStats(m); return; }
  if(view==="series"){ renderSeries(m); return; }
  // library
  const data = filtered();
  if(!data.length){ m.innerHTML = `<div class="empty">No books ${statusFilter?"on this shelf":"match"}${query?` “${esc(query)}”`:""}.</div>`; return; }
  if(groupBy!=="none") renderGroups(m,data,groupBy);
  else if(layout==="shelf") renderShelf(m,data);
  else if(layout==="list") renderList(m,data);
  else renderCovers(m,data);
  wireCovers(m);
}

function renderWishlist(m){
  document.getElementById("viewnote").textContent = wishlist.length+" to get";
  const q=norm(query);
  const items = wishlist.filter(w=>!q||norm(w.title).includes(q)||norm(w.author).includes(q)||norm(w.series).includes(q))
    .sort((a,b)=> (b.priority?1:0)-(a.priority?1:0) || (a.status==="upcoming"?1:0)-(b.status==="upcoming"?1:0) || norm(a.title).localeCompare(norm(b.title)));
  const addBar = `<div style="display:flex;gap:8px;margin:0 0 12px">
    <button class="imp" style="margin:0;flex:1 1 auto;width:auto;min-width:0" onclick="openAddWish()">＋ Add a book</button>
    <button class="imp sec" style="margin:0;flex:0 0 auto;width:auto;padding:13px 18px" onclick="shareWishlist()">🔗 Share</button></div>`;
  if(!wishlist.length){
    m.innerHTML = addBar + `<div id="suggestbox"></div>` + `<div class="empty">Your wishlist is empty.<br><span style="font-size:12.5px">Open the <b>Series</b> tab and tap any book you're missing or an upcoming release to add it here — or use the button above.</span></div>`;
    loadSuggestions(); return;
  }
  const rows = items.map(w=>{
    const up = w.status==="upcoming";
    const owned = ownedAlready(w.title);
    const sub = [w.author, up?("Releases "+(w.release_date||"TBA")):w.year, w.series?(esc(w.series)+(w.index?(" #"+w.index):"")):""].filter(Boolean).join(" · ");
    return `<div class="row lg wishrow" onclick="openWish('${esc(w.key)}')">
      <div class="mini" data-id="${esc(w.id)}"><div class="mph">${esc(w.title)}</div></div>
      <div class="rmain"><div class="rt">${w.priority?'★ ':''}${esc(w.title)}${up?' <span class="curtag" style="color:var(--up)">upcoming</span>':""}${owned?' <span class="curtag">✓ own it now</span>':""}</div><div class="rs">${sub}</div></div>
      <button class="wremove" onclick="event.stopPropagation();removeWish('${esc(w.key)}');render();" aria-label="Remove">♥</button>
    </div>`;
  }).join("");
  m.innerHTML = addBar + `<div class="group open"><div class="glist">${rows}</div></div>` + `<div id="suggestbox"></div>`;
  loadSuggestions();
}

/* ---------- suggestions: more from your authors (Open Library) ---------- */
let _suggestHTML=null, _suggList=[];
async function olAuthorWorks(author){
  const key="olw:"+norm(author);
  try{ const c=JSON.parse(localStorage.getItem(key)||"null"); if(c && (Date.now()-c.t < 7*864e5)) return c.w; }catch(e){}
  let w=[];
  try{
    const r=await fetch("https://openlibrary.org/search.json?limit=14&sort=new&fields=title,first_publish_year,cover_i&author="+enc(author));
    const j=await r.json();
    w=(j.docs||[]).filter(d=>d.cover_i && d.title).map(d=>({title:d.title, year:d.first_publish_year||"", cover:"https://covers.openlibrary.org/b/id/"+d.cover_i+"-M.jpg"}));
  }catch(e){}
  try{ localStorage.setItem(key, JSON.stringify({t:Date.now(), w})); }catch(e){}
  return w;
}
const baseNorm = t => norm((t||"").split(":")[0].split("(")[0]);
const isJunkTitle = t => /box set|boxed|collection|\b\d+\s*books?\b|bestsell|omnibus|complete series/i.test(t||"");
async function loadSuggestions(){
  const box=document.getElementById("suggestbox"); if(!box) return;
  if(_suggestHTML!==null){ box.innerHTML=_suggestHTML; wireSuggest(box); return; }
  const ac={}; books.forEach(b=>{ if(b.author&&!b.placeholder&&b.author!=="Unknown") ac[b.author]=(ac[b.author]||0)+1; });
  const top=Object.entries(ac).filter(([a,n])=>n>=2).sort((a,b)=>b[1]-a[1]).slice(0,6).map(x=>x[0]);
  if(!top.length){ _suggestHTML=""; return; }
  const owned=new Set(books.map(b=>baseNorm(b.title)));
  const wished=new Set(wishlist.map(w=>baseNorm(w.title)));
  const fetched=await Promise.all(top.map(a=>olAuthorWorks(a).then(w=>[a,w])));   // parallel
  const sugg=[]; const seen=new Set();
  for(const [author,works] of fetched){
    let per=0;
    for(const w of works){
      const t=baseNorm(w.title);
      if(!t||owned.has(t)||wished.has(t)||seen.has(t)||isJunkTitle(w.title)) continue;
      seen.add(t); sugg.push({title:w.title, author, year:w.year, cover:w.cover}); per++;
      if(per>=2) break;
    }
    if(sugg.length>=10) break;
  }
  if(!sugg.length){ _suggestHTML=""; return; }
  _suggList=sugg;
  _suggestHTML=`<div class="scard"><h3>✨ More from your authors</h3>
    <div class="sauth">Books by authors you own — tap to add to the wishlist</div>
    <div class="group open" style="margin-top:8px"><div class="glist">`
    + sugg.map((s,i)=>`<div class="row lg" data-sugg="${i}" style="cursor:pointer">
        <div class="mini"><img src="${esc(s.cover)}" loading="lazy" onerror="this.style.display='none'"></div>
        <div class="rmain"><div class="rt">${esc(s.title)}</div><div class="rs">${esc(s.author)}${s.year?" · "+s.year:""}</div></div>
        <span class="wish">＋</span></div>`).join("")
    + `</div></div></div>`;
  box.innerHTML=_suggestHTML; wireSuggest(box);
}
function wireSuggest(box){ box.querySelectorAll("[data-sugg]").forEach(el=>{ el.addEventListener("click",()=>{ const s=_suggList[+el.dataset.sugg]; if(s){ addWish({title:s.title,author:s.author,year:s.year,cover:s.cover}); _suggestHTML=null; render(); toast("Added to wishlist ♥"); } }); }); }

function renderList(m,data){
  document.getElementById("viewnote").textContent = data.length+" shown";
  m.innerHTML = `<div class="group open"><div class="glist">`+data.map(b=>{
    let sTag = "";
    if(b.series){ const s=seriesMatch(b.series); sTag = s.placeholder?` · <span class="lser">${esc(b.series)}</span>`:` · <span class="lser">${esc(b.series)} (${s.haveCount}/${s.total})</span>`; }
    const st = b.status&&STATUS_LABEL[b.status]?`<span class="statusdot sd-${b.status}"></span>`:"";
    return `<div class="row lg" onclick="openBook(${b.id})">
      <div class="mini" data-id="${b.id}"><div class="mph">${esc(b.title)}</div></div>
      <div class="rmain"><div class="rt">${esc(b.title)} ${ministars(b.rating)}</div><div class="rs">${st}${esc(b.author)}${b.year?" · "+b.year:""}${sTag}</div></div>
    </div>`;
  }).join("")+`</div></div>`;
}

function renderCovers(m,data){
  document.getElementById("viewnote").textContent = data.length+" shown";
  m.innerHTML = `<div class="grid">`+data.map(b=>`
    <button class="bcard" onclick="openBook(${b.id})">
      <div class="cover">${b.placeholder?'<span class="badge multi">series</span>':(b.series?'<span class="badge">series</span>':'')}${typeTag(b)||statusBadge(b)}
        <div class="ph" ${''}></div>
      </div>
      <div class="binfo"><div class="bt">${esc(b.title)}</div><div class="ba">${esc(b.author)}${b.rating?` ${ministars(b.rating)}`:""}</div></div>
    </button>`).join("")+`</div>`;
  // inject cover placeholders with data-id
  m.querySelectorAll(".bcard").forEach((c,i)=>{ const b=data[i];
    const cv=c.querySelector(".cover"); const ph=cv.querySelector(".ph");
    cv.dataset.id=b.id;
    ph.innerHTML=`<div class="t">${esc(b.title)}</div><div class="a">${esc(b.author)}</div>`;
  });
}

const GENRE_COLOR={ "Mystery & Thriller":"#7c4a3a","Historical Fiction":"#4d6455","Children's & YA":"#c07b2e",
  "Fiction & Literature":"#41527a","Sci-Fi & Fantasy":"#4a3a6b","Classics":"#6b4a2a","Religion & Philosophy":"#7a6338",
  "Health & Self-Help":"#2f7161","History & Politics":"#5a3a3a","Home & Reference":"#356048" };
const genreColor = g => GENRE_COLOR[topGenre(g)] || "#5b7263";
function renderShelf(m,data){
  document.getElementById("viewnote").textContent = data.length+" books";
  const groups={}; data.forEach(b=>{ const s=b.shelf||"Unshelved"; (groups[s]=groups[s]||[]).push(b); });
  const names=Object.keys(groups).sort((a,b)=>groups[b].length-groups[a].length||a.localeCompare(b));
  m.innerHTML = names.map(n=>`<div class="shelfwrap">
    <div class="shelfhdr">${esc(n)} <span>${groups[n].length}</span></div>
    <div class="shelf">${groups[n].map(b=>`
      <div class="shelfbook" data-id="${b.id}" onclick="openBook(${b.id})" title="${esc(b.title)} — ${esc(b.author)}">
        <div class="ph" style="background:${genreColor(b.genre)}"><span>${esc(b.title)}</span></div>
      </div>`).join("")}</div></div>`).join("");
}

function renderGroups(m,data,key){
  const groups={};
  data.forEach(b=>{
    if(key==="collection"){ const cs=(b.collections&&b.collections.length)?b.collections:["Unfiled"]; cs.forEach(c=>{(groups[c]=groups[c]||[]).push(b);}); }
    else { const g = key==="author"?(b.author||"—") : key==="shelf"?(b.shelf||"Unshelved") : key==="type"?(TYPE_LABEL[b.type||"book"]||"Book") : topGenre(b.genre); (groups[g]=groups[g]||[]).push(b); }
  });
  const names=Object.keys(groups).sort((a,b)=>{
    if(key==="author"){ const ln=s=>{const p=s.trim().split(" ");return p[p.length-1];}; return norm(ln(a)).localeCompare(norm(ln(b))); }
    return groups[b].length - groups[a].length || a.localeCompare(b);  // biggest shelves first
  });
  const label={author:"authors",genre:"genres",collection:"collections",shelf:"shelves",type:"types"}[key]||"groups";
  document.getElementById("viewnote").textContent = names.length+" "+label;
  m.innerHTML = names.map(n=>`
    <div class="group">
      <div class="ghead" onclick="this.parentNode.classList.toggle('open')">
        <span class="chev">▸</span><span>${esc(n)}</span><span class="gc">${groups[n].length}</span>
      </div>
      <div class="glist">${groups[n].sort((x,y)=>norm(x.title).localeCompare(norm(y.title))).map(b=>`
        <div class="row" onclick="openBook(${b.id})">
          <div class="mini" data-id="${b.id}"><div class="mph">${esc(b.title)}</div></div>
          <div><div class="rt">${esc(b.title)}</div><div class="rs">${key==="author"?esc(b.genre):esc(b.author)}${b.year?" · "+b.year:""}${b.series?" · "+esc(b.series):""}</div></div>
        </div>`).join("")}</div>
    </div>`).join("");
}

function seriesMatch(seriesName){
  // returns {db, owned:[{book}], entries:[{...,have,book}], haveCount, total, upcoming:[]}
  const db = SERIES_DB[seriesName];
  const owned = books.filter(b=>b.series===seriesName);
  if(!db) return {name:seriesName, db:null, owned, entries:[], haveCount:owned.length, total:owned.length, upcoming:[]};
  const ownedNorm = owned.map(b=>norm(b.title));
  const placeholder = owned.some(b=>b.placeholder);
  const entries = db.entries.map(e=>{
    const have = !placeholder && ownedNorm.some(t=> t===norm(e.title) || (t.length>4&&norm(e.title).includes(t)) );
    return {...e, have};
  });
  const published = entries.filter(e=>e.status!=="upcoming");
  const upcoming = entries.filter(e=>e.status==="upcoming");
  const haveCount = placeholder ? owned.length : published.filter(e=>e.have).length;
  const total = published.length;
  return {name:seriesName, db, owned, entries, published, upcoming, haveCount, total, placeholder};
}

function ownedIdForEntry(s, e){
  const m = s.owned.find(b=> norm(b.title)===norm(e.title) || (norm(b.title).length>4 && norm(e.title).includes(norm(b.title))));
  return m ? m.id : null;
}
function entryRow(s, e, curId){
  const up = e.status==="upcoming";
  const cls = up?"up":(s.placeholder?"ref":(e.have?"have":"miss"));
  const oid = (e.have && !s.placeholder) ? ownedIdForEntry(s,e) : null;
  const isCur = curId!=null && oid===curId;
  const canWish = !e.have && !s.placeholder;                 // missing or upcoming -> wishlistable
  const wished = canWish && isWished(e.title, s.db?s.db.author:"");
  let right;
  if(up) right = `<span class="tag u">${esc(e.release_date||"upcoming")}</span>`+(canWish?`<span class="wish ${wished?'on':''}">${wished?'♥':'♡'}</span>`:"");
  else if(e.have) right = `<span class="check">✓</span>`;
  else if(s.placeholder) right = "";
  else right = `<span class="wish ${wished?'on':''}">${wished?'♥':'♡'}</span>`;
  let attrs = "";
  if(oid!=null && oid!==curId) attrs = ` onclick="openBook(${oid})" style="cursor:pointer"`;
  else if(canWish) attrs = ` data-wishadd data-series="${esc(s.name)}" data-title="${esc(e.title)}" style="cursor:pointer"`;
  return `<div class="ent ${cls}${isCur?' cur':''}"${attrs}><div class="num">${esc(e.index||"•")}</div>
    <div><div class="et">${esc(e.title)}${isCur?' <span class="curtag">this book</span>':''}</div>${e.year||e.release_date?`<div class="ey">${esc(up?("Releases "+(e.release_date||"TBA")):e.year)}</div>`:""}</div>${right}</div>`;
}
function seriesEntriesHTML(s, curId){
  if(!s.db) return s.owned.map(b=>`<div class="ent have"><div class="num">•</div><div><div class="et">${esc(b.title)}</div></div><span class="check">✓</span></div>`).join("");
  let ents=s.entries, extra=0;
  if(s.placeholder && ents.length>8){ extra=ents.length-8; ents=ents.slice(0,8); }
  let html=ents.map(e=>entryRow(s,e,curId)).join("");
  if(extra) html+=`<div class="ent ref"><div class="num">…</div><div><div class="et" style="color:var(--muted);font-weight:500">+${extra} more in the series</div></div></div>`;
  return html;
}
function comingSoonHTML(allNames){
  // gather every unreleased entry across the tracked series, soonest first
  const up=[];
  allNames.forEach(n=>{ const s=seriesMatch(n); (s.upcoming||[]).forEach(e=> up.push({series:n, author:(s.db?s.db.author:""), ...e})); });
  if(!up.length) return "";
  const dkey=e=>{ const m=(e.release_date||"").match(/(\d{4})-(\d{2})-(\d{2})/); if(m) return m[1]+m[2]+m[3];
    const y=(e.release_date||e.year||"").match(/(\d{4})/); return (y?y[1]:"9999")+"99"; };
  up.sort((a,b)=>dkey(a).localeCompare(dkey(b)));
  const rows=up.map(e=>{
    const wished=isWished(e.title, e.author);
    return `<div class="ent up" data-wishadd data-series="${esc(e.series)}" data-title="${esc(e.title)}" style="cursor:pointer">
      <div class="num">${esc(e.index||"•")}</div>
      <div><div class="et">${esc(e.title)}</div><div class="ey">${esc(e.series)} · ${esc(e.author)}</div></div>
      <span class="tag u">${esc(e.release_date||"TBA")}</span><span class="wish ${wished?'on':''}">${wished?'♥':'♡'}</span></div>`;
  }).join("");
  return `<div class="scard coming"><h3>📅 Coming Soon</h3>
    <div class="sauth">Unreleased books in your series — tap to add to the wishlist</div>
    <div class="entries" style="margin-top:10px">${rows}</div></div>`;
}
function readNextHTML(allNames){
  // for series you're partway through, the next book you don't own yet
  const recs=[];
  allNames.forEach(n=>{ const s=seriesMatch(n);
    if(!s.db || s.placeholder || s.haveCount<1 || s.haveCount>=s.total) return;
    const miss=(s.published||[]).find(e=>!e.have);
    if(miss) recs.push({series:n, author:s.db.author, ...miss, have:s.haveCount, total:s.total});
  });
  if(!recs.length) return "";
  const rows=recs.map(e=>{
    const wished=isWished(e.title, e.author);
    return `<div class="ent" data-wishadd data-series="${esc(e.series)}" data-title="${esc(e.title)}" style="cursor:pointer">
      <div class="num">${esc(e.index||"•")}</div>
      <div><div class="et">${esc(e.title)}</div><div class="ey">${esc(e.series)} · you have ${e.have} of ${e.total}</div></div>
      <span class="wish ${wished?'on':''}">${wished?'♥':'♡'}</span></div>`;
  }).join("");
  return `<div class="scard"><h3>📖 Read Next</h3>
    <div class="sauth">The next book in series you've started — tap to add to the wishlist</div>
    <div class="entries" style="margin-top:10px">${rows}</div></div>`;
}
function renderSeries(m){
  const q=norm(query);
  let names=[...new Set(books.filter(b=>b.series).map(b=>b.series))];
  names=names.filter(n=>!q||norm(n).includes(q)||books.some(b=>b.series===n&&(norm(b.title).includes(q)||norm(b.author).includes(q))));
  names.sort();
  if(!names.length){ m.innerHTML=`<div class="empty">No series found.</div>`; return; }
  const coming = q ? "" : comingSoonHTML(names) + readNextHTML(names);
  m.innerHTML = coming + names.map(n=>{
    const s=seriesMatch(n);
    const auth=s.db?s.db.author:(s.owned[0]?s.owned[0].author:"");
    const pct= s.total? Math.round(100*s.haveCount/s.total):100;
    const entriesHTML=seriesEntriesHTML(s, null);
    const upCount = s.upcoming? s.upcoming.length:0;
    const progHTML = s.placeholder
      ? `<div class="prog"><div class="pl" style="background:#efe7d6;color:var(--muted);padding:3px 10px;border-radius:20px">several volumes owned</div></div>`
      : `<div class="prog"><div class="bar"><i style="width:${pct}%"></i></div><div class="pl">${s.haveCount} of ${s.total}</div></div>`;
    return `<div class="scard">
      <h3>${esc(n)}</h3><div class="sauth">${esc(auth)}${s.total&&!s.placeholder?" · "+s.total+" books":""}${upCount?` · <span style="color:var(--up)">${upCount} upcoming</span>`:""}</div>
      ${progHTML}
      ${s.placeholder?`<div class="snote">You own several — import your Libib list to mark exactly which ones. Full reading order below.</div>`:(s.db&&s.db.note?`<div class="snote">${esc(s.db.note)}</div>`:"")}
      <div class="entries">${entriesHTML}</div>
    </div>`;
  }).join("");
}

/* ---------- detail sheet ---------- */
function buyLinks(b){
  const q = b.isbn ? b.isbn : (b.title.replace(/\s*\(multiple\).*/i,"")+" "+b.author);
  const priceHref = b.isbn ? ("https://bookscouter.com/book/"+enc(b.isbn)) : ("https://www.google.com/search?tbm=shop&q="+enc(q));
  const online = STORES.online.map(s=>`<a class="buy" href="${s.search}${enc(q)}" target="_blank" rel="noopener"><span class="bn">${esc(s.name)}</span><span class="bk">search &rsaquo;</span></a>`).join("")
    + `<a class="buy" href="${priceHref}" target="_blank" rel="noopener"><span class="bn">Compare prices 💲</span><span class="bk">${b.isbn?"used & new by ISBN":"shopping search"}</span></a>`;
  const stores = STORES.local.filter(s=>!/library|borrow/i.test(s.kind));
  const local = stores.map(s=>{
    const href = s.search? s.search+enc(q) : s.url;
    return `<a class="buy local" href="${href}" target="_blank" rel="noopener"><span class="bn">${esc(s.name)}</span><span class="bk">${esc(s.kind)} · ${esc(s.city)}</span></a>`;
  }).join("");
  const lib = STORES.local.find(s=>/library|borrow/i.test(s.kind));
  const borrow = `<a class="buy local" href="https://search.worldcat.org/search?q=${enc(q)}" target="_blank" rel="noopener"><span class="bn">Find at a library 🔎</span><span class="bk">WorldCat · nearby holdings</span></a>`
    + (lib?`<a class="buy local" href="${lib.url}" target="_blank" rel="noopener"><span class="bn">${esc(lib.name)}</span><span class="bk">Borrow · ${esc(lib.city)}</span></a>`:"");
  return {online, local, borrow};
}
function openBook(id){
  const b=books.find(x=>x.id==id); if(!b) return;
  const bl=buyLinks(b);
  let seriesBlock="";
  if(b.series){
    const s=seriesMatch(b.series);
    const head = s.placeholder
      ? `<div class="miniprog"><b>${esc(b.series)}</b> · several volumes owned<div class="subnote">Import your Libib list to mark exactly which ones you have.</div></div>`
      : `<div class="miniprog"><b>${esc(b.series)}</b> — ${s.haveCount} of ${s.total} owned
          <div class="bar" style="margin-top:8px"><i style="width:${Math.round(100*s.haveCount/Math.max(1,s.total))}%"></i></div>
          ${s.upcoming&&s.upcoming.length?`<div class="subnote" style="color:var(--up)"><b>Coming:</b> ${s.upcoming.map(e=>esc(e.title)+(e.release_date?" ("+esc(e.release_date)+")":"")).join(", ")}</div>`:""}</div>`;
    seriesBlock=`<div class="sect"><h4>In this series ${s.db&&!s.placeholder?`· tap a title you own to open it`:""}</h4>
      ${head}
      <div class="entries" style="margin-top:10px">${seriesEntriesHTML(s, b.id)}</div></div>`;
  }
  const st=b.status||"";
  const statusSeg=`<div class="seg">
    <button class="${st==='toread'?'on':''}" onclick="setStatus(${b.id},'toread')">To-read</button>
    <button class="${st==='reading'?'on':''}" onclick="setStatus(${b.id},'reading')">Reading</button>
    <button class="${st==='read'?'on':''}" onclick="setStatus(${b.id},'read')">Read</button>
  </div>`;
  const stars=`<div class="stars" id="dstars">${[1,2,3,4,5].map(n=>`<span class="${(b.rating||0)>=n?'lit':''}" onclick="setRating(${b.id},${n})">★</span>`).join("")}</div>`;
  document.getElementById("sheetbody").innerHTML=`
    <button class="editbtn" onclick="openEdit(${b.id})">Edit</button>
    <div class="dtop">
      <div class="dcover" data-id="${b.id}" id="dcover"><div class="ph mph" style="font-size:11px;padding:8px;text-align:center">${esc(b.title)}</div></div>
      <div class="dmeta">
        <h2>${esc(b.title)}</h2>
        <div class="dau">${esc(b.author)}</div>
        <div>${b.type&&b.type!=="book"?`<span class="pill" style="background:var(--sage);color:#fff">${TYPE_ICON[b.type]||""} ${esc(TYPE_LABEL[b.type])}</span>`:""}${b.genre?`<span class="pill">${esc(b.genre)}</span>`:""}${b.year?`<span class="pill">${esc(b.year)}</span>`:""}${b.shelf?`<span class="pill">${esc(b.shelf)}</span>`:""}${(b.collections||[]).map(c=>`<span class="pill coll">${esc(c)}</span>`).join("")}</div>
      </div>
    </div>
    ${b.notes?`<div class="dnotes">${esc(b.notes)}</div>`:""}
    <div class="sect"><h4>Reading status${b.finished?` · finished ${esc(b.finished)}`:""}</h4>${statusSeg}<div style="margin-top:12px">${stars}</div></div>
    ${seriesBlock}
    <div class="sect"><h4>Borrow — free</h4><div class="btns">${bl.borrow}</div></div>
    <div class="sect"><h4>Local to Livingston, TN</h4><div class="btns">${bl.local}</div></div>
    <div class="sect"><h4>Buy online</h4><div class="btns">${bl.online}</div></div>`;
  // detail cover
  const dc=document.getElementById("dcover");
  resolveCover(b).then(url=>{ if(url){ const img=new Image(); img.onload=()=>{dc.querySelector(".mph").style.display="none";dc.insertBefore(img,dc.firstChild);}; img.src=url; } });
  openSheet();
}
let sheetOpen=false, navTarget=null;
function openSheet(){ document.getElementById("scrim").classList.add("on"); document.getElementById("sheet").classList.add("on");
  if(!sheetOpen){ sheetOpen=true; try{ history.pushState({modal:1}, ""); }catch(e){} } }
function hideSheetUI(){ document.getElementById("scrim").classList.remove("on"); document.getElementById("sheet").classList.remove("on"); stopScanner(); sheetOpen=false; }
function closeSheet(){ if(sheetOpen){ hideSheetUI(); if(history.state && history.state.modal){ history.back(); } } else hideSheetUI(); }
function closeSheetTo(v){ navTarget=v; if(sheetOpen){ hideSheetUI(); if(history.state && history.state.modal){ history.back(); } else { applyView(v); } } else { applyView(v); } }

function openWish(key){
  const w = wishlist.find(x=>x.key===key); if(!w) return;
  const bl = buyLinks(w);
  const owned = ownedAlready(w.title);
  const up = w.status==="upcoming";
  document.getElementById("sheetbody").innerHTML=`
    <div class="dtop">
      <div class="dcover" data-id="${esc(w.id)}" id="dcover"><div class="ph mph" style="font-size:11px;padding:8px;text-align:center">${esc(w.title)}</div></div>
      <div class="dmeta">
        <h2>${esc(w.title)}</h2>
        <div class="dau">${esc(w.author)}</div>
        <div>${w.series?`<span class="pill">${esc(w.series)}${w.index?(" #"+esc(w.index)):""}</span>`:""}${up?`<span class="pill" style="background:var(--up);color:#fff">Releases ${esc(w.release_date||"TBA")}</span>`:(w.year?`<span class="pill">${esc(w.year)}</span>`:"")}</div>
        ${owned?`<div class="subnote" style="color:var(--sage)">✓ This is already in your library.</div>`:""}
      </div>
    </div>
    <div class="sect"><h4>Borrow — free</h4><div class="btns">${bl.borrow}</div></div>
    <div class="sect"><h4>Local to Livingston, TN</h4><div class="btns">${bl.local}</div></div>
    <div class="sect"><h4>Buy online</h4><div class="btns">${bl.online}</div></div>
    <div class="sect">
      ${owned?"":`<button class="imp" onclick="gotIt('${esc(w.key)}');closeSheetTo('library');toast('Moved to your library ✓');">✓ I got this — move to Library</button>`}
      <button class="imp sec" onclick="toggleWishPriority('${esc(w.key)}')">${w.priority?"★ Priority (tap to unstar)":"☆ Mark as priority"}</button>
      <button class="imp sec danger" onclick="removeWish('${esc(w.key)}');closeSheet();render();toast('Removed from wishlist');">Remove from wishlist</button>
    </div>`;
  const dc=document.getElementById("dcover");
  resolveCover(w).then(url=>{ if(url){ const img=new Image(); img.onload=()=>{dc.querySelector(".mph").style.display="none";dc.insertBefore(img,dc.firstChild);}; img.src=url; } });
  openSheet();
}

/* ---------- reading status / rating / edit / add / delete ---------- */
const todayISO = () => new Date().toISOString().slice(0,10);
function setStatus(id,val){ const b=books.find(x=>x.id==id); if(!b) return; b.status=(b.status===val?"":val); if(!b.added)b.added=Date.now();
  if(b.status==="read" && !b.finished) b.finished=todayISO(); persist(); render(); openBook(id); }
function setRating(id,n){ const b=books.find(x=>x.id==id); if(!b) return; b.rating=(b.rating===n?0:n); persist(); render(); openBook(id); }
function openEdit(id){
  const b=books.find(x=>x.id==id); if(!b) return;
  document.getElementById("sheetbody").innerHTML=`<div class="panel">
    <h3>Edit book</h3>
    <div class="efield"><label>Title</label><input id="e_title" value="${esc(b.title)}"></div>
    <div class="efield"><label>Author</label><input id="e_author" value="${esc(b.author)}"></div>
    <div class="efield"><label>Genre</label><input id="e_genre" value="${esc(b.genre)}"></div>
    <div class="efield"><label>Year</label><input id="e_year" value="${esc(b.year)}"></div>
    <div class="efield"><label>Series (optional)</label><input id="e_series" value="${esc(b.series||"")}"></div>
    <div class="efield"><label>Shelf / location (e.g. Bookcase 1, cube B3)</label><input id="e_shelf" value="${esc(b.shelf||"")}"></div>
    <div class="efield"><label>Collections (comma-separated — e.g. Dani, Kids, Book club)</label><input id="e_collections" value="${esc((b.collections||[]).join(", "))}" placeholder="Dani, Kids"></div>
    <div class="efield"><label>Type</label><select id="e_type">${Object.keys(TYPE_LABEL).map(k=>`<option value="${k}"${(b.type||"book")===k?" selected":""}>${TYPE_LABEL[k]}</option>`).join("")}</select></div>
    <div class="efield"><label>Cover image URL (paste to override)</label><input id="e_cover" value="${esc(b.cover||"")}" placeholder="https://..."></div>
    <div class="efield"><label>Notes</label><textarea id="e_notes">${esc(b.notes||"")}</textarea></div>
    <button class="imp" onclick="saveEdit(${id})">Save changes</button>
    <button class="imp sec danger" onclick="deleteBook(${id})">Delete this book</button>
  </div>`;
  openSheet();
}
function saveEdit(id){
  const b=books.find(x=>x.id==id); if(!b) return;
  const g=v=>document.getElementById(v).value.trim();
  b.title=g("e_title")||b.title; b.author=g("e_author"); b.genre=g("e_genre")||"Uncategorized";
  b.year=g("e_year"); b.series=g("e_series"); b.shelf=g("e_shelf"); b.notes=g("e_notes");
  b.collections=g("e_collections").split(",").map(x=>x.trim()).filter(Boolean);
  b.type=document.getElementById("e_type").value||"book";
  const cov=g("e_cover"); if(cov!==(b.cover||"")){ b.cover=cov; delete coverCache[ckey(b)]; }
  b.placeholder=false; persist(); closeSheet(); render(); toast("Saved");
}
function deleteBook(id){
  const b=books.find(x=>x.id==id); if(!b) return;
  if(!confirm("Delete “"+b.title+"” from your library?")) return;
  books=books.filter(x=>x.id!=id); persist(); closeSheet(); render(); toast("Deleted");
}
function openAddBook(){
  document.getElementById("sheetbody").innerHTML=`<div class="panel">
    <h3>Add a book to your library</h3>
    <p style="font-size:12.5px;color:var(--muted);margin:4px 0 10px">Cover fills in automatically. To add by barcode, use “Scan a book”.</p>
    <div class="efield"><label>Title</label><input id="a_title" placeholder="Title"></div>
    <div class="efield"><label>Author</label><input id="a_author" placeholder="Author"></div>
    <div class="efield"><label>Genre (optional)</label><input id="a_genre" placeholder="e.g. Historical Fiction"></div>
    <div class="efield"><label>Year (optional)</label><input id="a_year" placeholder="e.g. 2021"></div>
    <div class="efield"><label>Type</label><select id="a_type">${Object.keys(TYPE_LABEL).map(k=>`<option value="${k}">${TYPE_LABEL[k]}</option>`).join("")}</select></div>
    <button class="imp" onclick="submitAddBook()">Add to library</button>
  </div>`;
  openSheet(); setTimeout(()=>document.getElementById("a_title")&&document.getElementById("a_title").focus(),220);
}
function submitAddBook(){
  const g=v=>document.getElementById(v).value.trim();
  const t=g("a_title"); if(!t){ toast("Enter a title"); return; }
  books.push({ id:nextId(), title:t, author:g("a_author"), genre:g("a_genre")||"Uncategorized", year:g("a_year"), shelf:"Added", series:"", placeholder:false, isbn:"", cover:"", status:"toread", rating:0, notes:"", added:Date.now(), type:document.getElementById("a_type").value||"book" });
  persist(); closeSheetTo("library"); toast("Added to library");
}

/* ---------- add-by-ISBN / barcode scan ---------- */
async function isbnLookup(isbn){
  isbn=(isbn||"").replace(/[^0-9Xx]/g,"");
  if(isbn.length<10){ return null; }
  try{
    const r=await fetch("https://www.googleapis.com/books/v1/volumes?country=US&q=isbn:"+isbn);
    const j=await r.json(); const vi=(j.items&&j.items[0]&&j.items[0].volumeInfo)||null;
    if(vi){ const il=vi.imageLinks||{}; let cov=(il.thumbnail||il.smallThumbnail||"");
      cov=cov.replace("http://","https://").replace("&edge=curl","").replace(/zoom=\d/,"zoom=1");
      return { title:vi.title||"", author:(vi.authors||[]).join(", "), year:(vi.publishedDate||"").slice(0,4),
        genre:(vi.categories||["Uncategorized"])[0], isbn, cover:cov }; }
  }catch(e){}
  // fallback Open Library
  try{
    const r=await fetch("https://openlibrary.org/api/books?format=json&jscmd=data&bibkeys=ISBN:"+isbn);
    const j=await r.json(); const d=j["ISBN:"+isbn];
    if(d) return { title:d.title||"", author:(d.authors||[]).map(a=>a.name).join(", "), year:(d.publish_date||"").match(/\d{4}/)?.[0]||"", genre:"Uncategorized", isbn, cover:(d.cover&&(d.cover.medium||d.cover.large))||"" };
  }catch(e){}
  return null;
}
async function addByIsbn(isbn, toWishlist){
  toast("Looking up…");
  const info=await isbnLookup(isbn);
  if(!info||!info.title){ toast("No match for that ISBN"); return; }
  if(toWishlist){ addWish({title:info.title, author:info.author, isbn:info.isbn, cover:info.cover, year:info.year}); toast("Added to wishlist ♥"); }
  else { books.push({ id:nextId(), ...info, shelf:"Scanned", series:"", placeholder:false, status:"toread", rating:0, notes:"", added:Date.now() }); persist(); toast("Added: "+info.title); }
}
let _scanStream=null, _scanRun=false;
async function openScan(){
  const hasDetector = ("BarcodeDetector" in window);
  document.getElementById("sheetbody").innerHTML=`<div class="panel">
    <h3>Scan or enter an ISBN</h3>
    ${hasDetector?`<p style="font-size:12.5px;color:var(--muted);margin:4px 0 0">Point the camera at the barcode on the back of the book.</p>
      <div class="scanwrap"><video id="scanvid" playsinline muted></video><div class="scanline"></div></div>`:
      `<p style="font-size:12.5px;color:var(--muted);margin:4px 0 6px">Live scanning isn't supported in this browser (common on iPhone). Type the 13-digit ISBN from the barcode instead.</p>`}
    <div class="efield"><label>ISBN</label><input id="isbn_in" inputmode="numeric" placeholder="9780316206877"></div>
    <button class="imp" onclick="submitIsbn(false)">Add to library</button>
    <button class="imp sec" onclick="submitIsbn(true)">Add to wishlist instead</button>
  </div>`;
  openSheet();
  if(hasDetector) startScanner();
}
async function startScanner(){
  try{
    const det=new BarcodeDetector({formats:["ean_13","ean_8","upc_a"]});
    _scanStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"}});
    const v=document.getElementById("scanvid"); if(!v){ stopScanner(); return; }
    v.srcObject=_scanStream; await v.play(); _scanRun=true;
    const loop=async()=>{
      if(!_scanRun||!document.getElementById("scanvid")) return;
      try{ const codes=await det.detect(v); const hit=codes.find(c=>/^(978|979|97)/.test(c.rawValue)||c.rawValue.length>=12);
        if(hit){ const isbn=hit.rawValue; stopScanner(); closeSheet(); addByIsbn(isbn,false); return; } }catch(e){}
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }catch(e){ /* permission denied -> manual entry still works */ }
}
function stopScanner(){ _scanRun=false; if(_scanStream){ _scanStream.getTracks().forEach(t=>t.stop()); _scanStream=null; } }
function submitIsbn(toWish){ const v=(document.getElementById("isbn_in").value||"").trim(); if(!v){ toast("Enter an ISBN"); return; } stopScanner(); closeSheet(); addByIsbn(v,toWish); }

/* ---------- backup / export ---------- */
function download(name, text, type){ const b=new Blob([text],{type:type||"application/json"}); const u=URL.createObjectURL(b);
  const a=document.createElement("a"); a.href=u; a.download=name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(u),1000); }
function stamp(){ const d=new Date(); return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0"); }
function backupJSON(){ download("our-library-backup-"+stamp()+".json", JSON.stringify({version:2, exported:Date.now(), books, wishlist}, null, 1)); toast("Backup downloaded"); }
function restoreJSON(e){ const f=e.target.files[0]; if(!f) return; const rd=new FileReader();
  rd.onload=()=>{ try{ const d=JSON.parse(rd.result); if(!Array.isArray(d.books)) throw 0;
    books=d.books; wishlist=d.wishlist||[]; persist(); saveWish(); closeSheetTo("library"); toast("Restored "+books.length+" books"); }
    catch(_){ toast("That isn't a valid backup file"); } };
  rd.readAsText(f); }
function csvCell(s){ s=(s==null?"":String(s)); return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s; }
function exportCSV(){
  const cols=["title","author","genre","year","series","shelf","isbn","status","rating","notes"];
  const rows=[cols.join(",")].concat(books.map(b=>cols.map(c=>csvCell(b[c])).join(",")));
  download("our-library-"+stamp()+".csv", rows.join("\n"), "text/csv"); toast("CSV exported");
}

/* ---------- reading goal + duplicates ---------- */
function saveGoal(){ const v=(document.getElementById("goal_in").value||"").replace(/[^0-9]/g,""); if(v) localStorage.setItem("lib_goal",v); else localStorage.removeItem("lib_goal"); toast(v?("Goal set: "+v+" books"):"Goal cleared"); }
function dupeGroups(){
  const map={};
  books.forEach(b=>{ if(b.placeholder) return; const k=norm(b.title)+"|"+norm(b.author); (map[k]=map[k]||[]).push(b); });
  return Object.values(map).filter(g=>g.length>1);
}
function openDupes(){
  const groups=dupeGroups();
  const body= groups.length ? groups.map(g=>`<div class="statsect" style="padding:11px 13px">
      <div style="font-weight:700;font-size:13.5px">${esc(g[0].title)}</div>
      <div style="font-size:12px;color:var(--muted);margin-bottom:6px">${esc(g[0].author)} · ${g.length} copies</div>
      ${g.map((b,i)=>`<div class="row" style="padding:6px 0;border-top:1px solid var(--line)"><div class="rmain"><div class="rt" style="font-size:12.5px">${esc(b.shelf||"—")}${b.year?" · "+esc(b.year):""}</div></div>${i===0?'<span class="curtag">keep</span>':`<button class="imp sec danger" style="width:auto;margin:0;padding:6px 12px" onclick="removeDupe(${b.id})">Remove</button>`}</div>`).join("")}
    </div>`).join("")
    : `<div class="empty">No duplicates found. 🎉</div>`;
  document.getElementById("sheetbody").innerHTML=`<div class="panel"><h3>Duplicate books</h3>
    <p style="font-size:12.5px;color:var(--muted);margin:4px 0 10px">Books with the same title + author. The first copy is kept; remove the extras.</p>${body}</div>`;
  openSheet();
}
function removeDupe(id){ books=books.filter(x=>x.id!=id); persist(); render(); openDupes(); toast("Removed duplicate"); }

/* ---------- stats ---------- */
function renderStats(m){
  document.getElementById("viewnote").textContent="";
  const owned=books.length;
  const read=books.filter(b=>b.status==="read").length;
  const reading=books.filter(b=>b.status==="reading").length;
  const toread=books.filter(b=>b.status==="toread").length;
  const rated=books.filter(b=>b.rating>0);
  const avg=rated.length?(rated.reduce((s,b)=>s+b.rating,0)/rated.length).toFixed(1):"—";
  const years=books.map(b=>parseInt(b.year)).filter(y=>y>0);
  const gcount={}; books.forEach(b=>{ const g=topGenre(b.genre); gcount[g]=(gcount[g]||0)+1; });
  const gtop=Object.entries(gcount).sort((a,b)=>b[1]-a[1]);
  const gmax=Math.max(1,...gtop.map(x=>x[1]));
  const acount={}; books.forEach(b=>{ if(b.author&&!b.placeholder){ acount[b.author]=(acount[b.author]||0)+1; } });
  const atop=Object.entries(acount).sort((a,b)=>b[1]-a[1]).slice(0,8);
  const amax=Math.max(1,...atop.map(x=>x[1]));
  const seriesNames=[...new Set(books.filter(b=>b.series).map(b=>b.series))];
  let sOwned=0,sTotal=0; seriesNames.forEach(n=>{ const s=seriesMatch(n); if(s.db&&!s.placeholder){ sOwned+=s.haveCount; sTotal+=s.total; } });
  const bar=(label,val,max)=>`<div class="brow"><span class="bl">${esc(label)}</span><span class="bt"><i style="width:${Math.round(100*val/Math.max(1,max))}%"></i></span><span class="bn">${val}</span></div>`;
  const yr=new Date().getFullYear();
  const goal=parseInt(localStorage.getItem("lib_goal")||"0")||0;
  const finishedYr=books.filter(b=>b.finished&&b.finished.slice(0,4)==String(yr)).length;
  const ccount={}; books.forEach(b=>(b.collections||[]).forEach(c=>ccount[c]=(ccount[c]||0)+1));
  const ctop=Object.entries(ccount).sort((a,b)=>b[1]-a[1]);
  const cmax=Math.max(1,...ctop.map(x=>x[1]));
  m.innerHTML=`
    <div class="stat-grid">
      <div class="statcard"><div class="num">${owned}</div><div class="lab">books in library</div></div>
      <div class="statcard"><div class="num">${wishlist.length}</div><div class="lab">on the wishlist</div></div>
      <div class="statcard"><div class="num">${read}</div><div class="lab">read</div></div>
      <div class="statcard"><div class="num">${reading||toread}</div><div class="lab">${reading?"currently reading":"to read"}</div></div>
      <div class="statcard"><div class="num">${avg}</div><div class="lab">avg rating (${rated.length} rated)</div></div>
      <div class="statcard"><div class="num">${years.length?Math.min(...years)+"–"+Math.max(...years):"—"}</div><div class="lab">year range</div></div>
    </div>
    ${goal?`<div class="statsect"><h4>${yr} reading goal</h4>${bar(finishedYr+" of "+goal+" books read", finishedYr, goal)}<div style="font-size:12px;color:var(--muted);margin-top:2px">${finishedYr>=goal?"Goal reached! 🎉":(goal-finishedYr)+" to go"}</div></div>`:`<div class="statsect"><h4>${yr} reading goal</h4><div style="font-size:12.5px;color:var(--muted)">Set a yearly goal in ⚙ Settings to track it here.</div></div>`}
    ${sTotal?`<div class="statsect"><h4>Series completion</h4>${bar(sOwned+" of "+sTotal+" across "+seriesNames.length+" series", sOwned, sTotal)}</div>`:""}
    <div class="statsect"><h4>By genre</h4>${gtop.map(([g,n])=>bar(g,n,gmax)).join("")}</div>
    ${ctop.length?`<div class="statsect"><h4>Collections</h4>${ctop.map(([c,n])=>bar(c,n,cmax)).join("")}</div>`:""}
    <div class="statsect"><h4>Top authors</h4>${atop.map(([a,n])=>bar(a,n,amax)).join("")}</div>`;
}
function openAddWish(){
  document.getElementById("sheetbody").innerHTML=`<div class="panel">
    <h3>Add to wishlist</h3>
    <p style="font-size:12.5px;color:var(--muted);margin:4px 0 10px">A book you'd like to buy or read. The cover and buy links fill in automatically.</p>
    <input id="wtitle" class="winput" placeholder="Title" autocomplete="off">
    <input id="wauthor" class="winput" placeholder="Author (optional)" autocomplete="off">
    <button class="imp" onclick="submitAddWish()">Add to wishlist</button>
  </div>`;
  openSheet();
  setTimeout(()=>document.getElementById("wtitle") && document.getElementById("wtitle").focus(), 220);
}
function submitAddWish(){
  const t=(document.getElementById("wtitle").value||"").trim();
  const a=(document.getElementById("wauthor").value||"").trim();
  if(!t){ toast("Enter a title"); return; }
  const added = addWish({title:t, author:a});
  closeSheetTo("wishlist");
  toast(added?"Added to wishlist ♥":"Already on the wishlist");
}

/* ---------- settings / import ---------- */
function openSettings(){
  const dark=localStorage.getItem("lib_theme")==="dark";
  const surl=localStorage.getItem("lib_sync_url")||"";
  document.getElementById("sheetbody").innerHTML=`<div class="panel">
    <h3>Library settings</h3>
    <p style="font-size:13px;color:var(--muted);margin:4px 0 0">${books.length} books · ${wishlist.length} wishlist · ${Object.keys(SERIES_DB).length} series tracked</p>

    <div class="setgrp"><div class="setlab">Add books</div>
      <button class="imp" onclick="openScan()">📷 Scan a book (ISBN)</button>
      <button class="imp sec" onclick="openAddBook()">Add a book by title</button>
      <label class="imp sec" for="csv">Import from Libib (CSV)</label>
      <input id="csv" type="file" accept=".csv,text/csv" style="display:none">
    </div>

    <div class="setgrp"><div class="setlab">Reading & cleanup</div>
      <div class="efield"><label>${new Date().getFullYear()} reading goal (books)</label><input id="goal_in" inputmode="numeric" value="${esc(localStorage.getItem("lib_goal")||"")}" placeholder="e.g. 24"></div>
      <button class="imp sec" onclick="saveGoal()">Save goal</button>
      <button class="imp sec" onclick="openDupes()">Find duplicate books</button>
    </div>

    <div class="setgrp"><div class="setlab">Backup & data</div>
      <button class="imp sec" onclick="backupJSON()">⬇ Download backup (.json)</button>
      <label class="imp sec" for="restore">⬆ Restore from backup</label>
      <input id="restore" type="file" accept=".json,application/json" style="display:none">
      <button class="imp sec" onclick="exportCSV()">Export library as CSV</button>
    </div>

    <div class="setgrp"><div class="setlab">Sync across devices (tailnet)</div>
      <div class="efield"><input id="sync_url" value="${esc(syncURL())}" placeholder="https://your-host.ts.net" inputmode="url"></div>
      <button class="imp sec" onclick="saveSyncUrl()">Save endpoint</button>
      <button class="imp sec" onclick="pullSync()">Sync now ↓</button>
      <div class="hint" style="margin-top:8px">Pre-set to the shared library on your home server — every device that opens the app shares one library (last edit wins). Changes push automatically; it pulls on launch. No VPN or app needed. Clear the box + Save to turn it off.</div>
    </div>

    <div class="setgrp"><div class="setlab">App</div>
      <button class="imp sec" onclick="toggleTheme()">${dark?"☀ Light mode":"🌙 Dark mode"}</button>
      <button class="imp sec" onclick="installApp()">Install app on this device</button>
      <button class="imp sec danger" onclick="resetLib()">Reset to sample library</button>
    </div>

    <div class="hint"><b>Export from Libib</b> is website-only (not the phone app): <b>libib.com</b> → sign in → account menu → <b>Settings</b> → <b>Libraries</b> tab → <b>Export Library (.csv)</b>. Then come back here → <b>Import from Libib</b>.</div>
  </div>`;
  document.getElementById("csv").addEventListener("change", handleCSV);
  document.getElementById("restore").addEventListener("change", restoreJSON);
  openSheet();
}
function saveSyncUrl(){ const v=(document.getElementById("sync_url").value||"").trim(); localStorage.setItem("lib_sync_url",v); toast(v?"Sync endpoint saved":"Sync turned off"); if(v) pullSync(true); }
function resetLib(){ localStorage.removeItem("lib_books"); books=CATALOG.map(b=>({...b})); persist(); closeSheet(); render(); toast("Reset to sample library"); }

function parseCSV(text){
  const rows=[]; let row=[], cur="", q=false;
  text=text.replace(/\r\n/g,"\n").replace(/\r/g,"\n");
  for(let i=0;i<text.length;i++){ const c=text[i];
    if(q){ if(c==='"'){ if(text[i+1]==='"'){cur+='"';i++;} else q=false; } else cur+=c; }
    else { if(c==='"') q=true; else if(c===","){row.push(cur);cur="";} else if(c==="\n"){row.push(cur);rows.push(row);row=[];cur="";} else cur+=c; }
  }
  if(cur.length||row.length){ row.push(cur); rows.push(row); }
  return rows.filter(r=>r.length>1||(r[0]||"").trim());
}
function handleCSV(e){
  const f=e.target.files[0]; if(!f) return;
  const rd=new FileReader();
  rd.onload=()=>{
    try{
      const rows=parseCSV(rd.result); if(rows.length<2){ toast("Empty CSV"); return; }
      const head=rows[0].map(h=>h.trim().toLowerCase());
      const find=(...names)=>{ for(const n of names){ const i=head.findIndex(h=>h===n); if(i>=0)return i; } for(const n of names){ const i=head.findIndex(h=>h.includes(n)); if(i>=0)return i; } return -1; };
      const iT=find("title"), iA=find("creators","authors","author","creator"),
        iFn=find("first_name","first name"), iLn=find("last_name","last name"),
        iIsbn=find("ean_isbn13","isbn13","isbn_13","isbn"), iIsbn10=find("upc_isbn10","isbn10"),
        iGen=find("genres","genre"), iYr=find("publish_date","published","publish date","year"),
        iSer=find("series"), iGrp=find("group","collection","shelf","tags");
      let impType="book";
      if(find("platform")>=0) impType="game";
      else if(find("director")>=0) impType="movie";
      else if(find("artist")>=0 && iIsbn<0 && iT>=0) impType="music";
      const out=[];
      for(let r=1;r<rows.length;r++){ const c=rows[r]; if(!c||!(c[iT]||"").trim()) continue;
        let author = iA>=0?c[iA]:"";
        if(!author && iLn>=0) author = ((iFn>=0?c[iFn]:"")+" "+c[iLn]).trim();
        let isbn = (iIsbn>=0?c[iIsbn]:"")||"" ; isbn=isbn.replace(/[^0-9Xx]/g,"");
        if(!isbn && iIsbn10>=0) isbn=(c[iIsbn10]||"").replace(/[^0-9Xx]/g,"");
        let year=(iYr>=0?c[iYr]:"")||""; const ym=year.match(/(1[5-9]\d\d|20\d\d)/); year=ym?ym[1]:"";
        let genre=(iGen>=0?c[iGen]:"")||""; genre=genre.split(/[;,|]/)[0].trim()||"Uncategorized";
        let series=(iSer>=0?c[iSer]:"")||"";
        if(!series && iGrp>=0){ const g=c[iGrp]||""; const mm=g.match(/([\w' .]+?)\s*#?\d/); if(/series|#\d/i.test(g)&&mm) series=mm[1].trim(); }
        // match against known series DB by title
        if(!series){ for(const sn in SERIES_DB){ if(SERIES_DB[sn].entries.some(en=>norm(en.title)===norm(c[iT]))){ series=sn; break; } } }
        out.push({ id:out.length+1, title:(c[iT]||"").trim(), author:author.trim()||"Unknown",
          genre, year, shelf:(iGrp>=0?(c[iGrp]||"").trim():"")||"Libib import", series, placeholder:false,
          isbn, confidence:"import", notes:"", type:impType });
      }
      if(!out.length){ toast("No rows found — is this a Libib CSV?"); return; }
      promptImport(out);
    }catch(err){ toast("Could not read that CSV"); }
  };
  rd.readAsText(f);
}
function hasUserData(){ return books.some(b=>b.status||b.rating||(b.collections&&b.collections.length)||b.finished||(b.notes&&b.confidence!=="import")); }
function promptImport(rows){
  const merge=hasUserData();
  document.getElementById("sheetbody").innerHTML=`<div class="panel">
    <h3>Import ${rows.length} books from Libib</h3>
    ${merge?`<p style="font-size:12.5px;color:var(--muted);margin:4px 0 12px">You have reading status / ratings / collections on some books. <b>Merge</b> keeps those and updates the details from Libib; <b>Replace</b> starts fresh.</p>
      <button class="imp" onclick="applyImport(true)">Merge — keep my reading data</button>
      <button class="imp sec" onclick="applyImport(false)">Replace everything</button>`
    :`<p style="font-size:12.5px;color:var(--muted);margin:4px 0 12px">This will load your Libib library into the app.</p>
      <button class="imp" onclick="applyImport(false)">Import</button>`}
  </div>`;
  window._pendingImport=rows; openSheet();
}
function applyImport(merge){
  const rows=window._pendingImport||[]; window._pendingImport=null;
  if(merge){
    const byIsbn={}, byTA={};
    books.forEach(b=>{ if(b.isbn) byIsbn[b.isbn]=b; byTA[norm(b.title)+"|"+norm(b.author)]=b; });
    let added=0, updated=0;
    rows.forEach(r=>{
      const m = (r.isbn&&byIsbn[r.isbn]) || byTA[norm(r.title)+"|"+norm(r.author)];
      if(m){ // update biblio fields, keep the user's reading data + collections
        m.title=r.title; m.author=r.author; m.genre=r.genre; if(r.year)m.year=r.year;
        if(r.series)m.series=r.series; if(r.isbn)m.isbn=r.isbn; m.placeholder=false; updated++;
      } else { r.id=nextId(); r.status=""; r.rating=0; r.collections=[]; r.added=Date.now(); books.push(r); byTA[norm(r.title)+"|"+norm(r.author)]=r; added++; }
    });
    persist(); closeSheetTo("library"); toast("Merged: "+added+" added, "+updated+" updated");
  } else {
    books=rows; persist(); closeSheetTo("library"); toast("Imported "+rows.length+" books from Libib");
  }
}

/* ---------- ui wiring + history (back button) ---------- */
function applyView(v){ view=v; try{localStorage.setItem("lib_view",v);}catch(e){} document.querySelectorAll("#tabs button").forEach(b=>b.classList.toggle("on",b.dataset.v===v)); render(); }
function setTab(v){ if(v!==view){ try{ history.pushState({view:v}, ""); }catch(e){} } applyView(v); }
addEventListener("popstate",(e)=>{
  // 1) an open sheet: back closes it (not the app)
  if(document.getElementById("sheet").classList.contains("on")){ hideSheetUI(); return; }
  // 2) tab-level back: return to the previous view; only exits from here if history is exhausted
  const v = navTarget || (e.state && e.state.view) || "library"; navTarget=null; applyView(v);
});
document.getElementById("tabs").addEventListener("click",e=>{ const b=e.target.closest("button"); if(b) setTab(b.dataset.v); });
document.getElementById("sort").addEventListener("change",e=>{ sortBy=e.target.value; try{localStorage.setItem("lib_sort",sortBy);}catch(e){} render(); });
document.getElementById("groupby").addEventListener("change",e=>{ groupBy=e.target.value; try{localStorage.setItem("lib_group",groupBy);}catch(e){} updateLayoutVis(); render(); });
document.getElementById("layout").addEventListener("click",e=>{ const b=e.target.closest("button"); if(!b) return; layout=b.dataset.l; try{localStorage.setItem("lib_layout",layout);}catch(e){}
  document.querySelectorAll("#layout button").forEach(x=>x.classList.toggle("on",x===b)); render(); });
function updateLayoutVis(){ document.getElementById("layout").style.display = (groupBy==="none")?"flex":"none"; }
document.getElementById("q").addEventListener("input",e=>{ query=e.target.value; render(); });
document.getElementById("filterbar").addEventListener("click",e=>{ const b=e.target.closest(".chip"); if(!b) return;
  statusFilter=b.dataset.f; document.querySelectorAll("#filterbar .chip").forEach(c=>c.classList.toggle("on",c===b)); render(); });
document.getElementById("gear").addEventListener("click",openSettings);
document.getElementById("scrim").addEventListener("click",()=>{ closeSheet(); });
document.addEventListener("click",e=>{ const w=e.target.closest("[data-wishadd]"); if(w){ e.stopPropagation(); toggleWishEntry(w.dataset.series, w.dataset.title); } });
let toastT; function toast(m){ const t=document.getElementById("toast"); t.textContent=m; t.classList.add("on"); clearTimeout(toastT); toastT=setTimeout(()=>t.classList.remove("on"),2600); }

/* ---------- installable PWA ---------- */
let deferredInstall=null;
addEventListener("beforeinstallprompt",e=>{ e.preventDefault(); deferredInstall=e; });
async function installApp(){
  if(deferredInstall){ deferredInstall.prompt(); const r=await deferredInstall.userChoice; deferredInstall=null; toast(r.outcome==="accepted"?"Installing…":"Maybe later"); }
  else { toast("Use your browser's Share → Add to Home Screen"); }
}
if("serviceWorker" in navigator){ addEventListener("load",()=>navigator.serviceWorker.register("sw.js").catch(()=>{})); }

/* ---------- read-only shared wishlist (?wishlist) ---------- */
const isShare = () => /[?&](wishlist|share)\b/.test(location.search);
function shareWishlist(){
  const url=location.origin+location.pathname+"?wishlist";
  if(navigator.share){ navigator.share({title:"Our Wishlist", text:"Books on our wishlist", url}).catch(()=>{}); }
  else if(navigator.clipboard){ navigator.clipboard.writeText(url).then(()=>toast("Share link copied")); }
  else { prompt("Share this link:", url); }
}
function openBuySheet(key){
  const w=wishlist.find(x=>x.key===key); if(!w) return;
  const bl=buyLinks(w);
  document.getElementById("sheetbody").innerHTML=`
    <div class="dtop"><div class="dcover" data-id="${esc(w.id)}" id="dcover"><div class="ph mph" style="font-size:11px;padding:8px;text-align:center">${esc(w.title)}</div></div>
      <div class="dmeta"><h2>${esc(w.title)}</h2><div class="dau">${esc(w.author)}</div>
      <div>${w.series?`<span class="pill">${esc(w.series)}</span>`:""}${w.status==="upcoming"?`<span class="pill" style="background:var(--up);color:#fff">Releases ${esc(w.release_date||"TBA")}</span>`:""}</div></div></div>
    <div class="sect"><h4>Borrow — free</h4><div class="btns">${bl.borrow}</div></div>
    <div class="sect"><h4>Local to Livingston, TN</h4><div class="btns">${bl.local}</div></div>
    <div class="sect"><h4>Buy online</h4><div class="btns">${bl.online}</div></div>`;
  const dc=document.getElementById("dcover"); resolveCover(w).then(u=>{ if(u){ const i=new Image(); i.onload=()=>{dc.querySelector(".mph").style.display="none";dc.insertBefore(i,dc.firstChild);}; i.src=u; } });
  openSheet();
}
async function renderShareMode(){
  READONLY=true;
  ["tabs","libbar","filterbar","gear"].forEach(id=>{ const el=document.getElementById(id); if(el) el.style.display="none"; });
  const sw=document.querySelector(".searchwrap"); if(sw) sw.style.display="none";
  const brand=document.querySelector(".brand"); if(brand) brand.innerHTML="📚 Our Wishlist";
  const m=document.getElementById("main");
  m.innerHTML=`<div class="empty">Loading wishlist…</div>`;
  try{ const r=await fetch(syncURL()+"/library",{cache:"no-store"}); const d=await r.json(); wishlist=d.wishlist||[]; }catch(e){ wishlist=[]; }
  if(!wishlist.length){ m.innerHTML=`<div class="empty">This wishlist is empty right now.</div>`; return; }
  const wl=wishlist.slice().sort((a,b)=>(b.priority?1:0)-(a.priority?1:0)||norm(a.title).localeCompare(norm(b.title)));
  m.innerHTML=`<div style="font-size:12.5px;color:var(--muted);margin-bottom:10px">Tap a book to buy it — local Livingston stores and online.</div>
    <div class="group open"><div class="glist">`+wl.map(w=>`
    <div class="row lg" onclick="openBuySheet('${esc(w.key)}')">
      <div class="mini" data-id="${esc(w.id)}"><div class="mph">${esc(w.title)}</div></div>
      <div class="rmain"><div class="rt">${w.priority?"★ ":""}${esc(w.title)}</div><div class="rs">${esc(w.author)}${w.series?" · "+esc(w.series):""}${w.status==="upcoming"?` · <span style="color:var(--up)">Releases ${esc(w.release_date||"TBA")}</span>`:""}</div></div>
    </div>`).join("")+`</div></div>`;
  wireCovers(m);
}

/* ---------- restore saved view prefs ---------- */
if(isShare()){
  renderShareMode();
} else {
  (function initPrefs(){
    document.querySelectorAll("#tabs button").forEach(b=>b.classList.toggle("on",b.dataset.v===view));
    const gb=document.getElementById("groupby"); if(gb) gb.value=groupBy;
    const so=document.getElementById("sort"); if(so) so.value=sortBy;
    document.querySelectorAll("#layout button").forEach(x=>x.classList.toggle("on",x.dataset.l===layout));
    updateLayoutVis();
    try{ history.replaceState({view:view}, ""); }catch(e){}   // seed history so back is well-defined
  })();
  if(syncURL()) pullSync(true);   // auto-pull latest on launch if sync is configured
  render();
}
</script>
</body>
</html>
"""

out = TEMPLATE
out = out.replace("/*CATALOG*/", json.dumps(catalog, ensure_ascii=False))
out = out.replace("/*SERIESDB*/", json.dumps(series_db, ensure_ascii=False))
out = out.replace("/*STORES*/", json.dumps(STORES, ensure_ascii=False))

with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
    f.write(out)

print("books:", len(catalog), "series:", len(series_db))
print("wrote:", os.path.join(HERE, "index.html"))
