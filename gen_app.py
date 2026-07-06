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
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>Our Library</title>
<style>
:root{
  --paper:#f5f1e8; --card:#fffdf8; --ink:#2b2b28; --muted:#7d786c;
  --sage:#5b7263; --sage-dark:#425146; --sage-light:#8ca392; --line:#e4ddcd;
  --accent:#b8683f; --up:#8a6d3b; --shadow:0 2px 8px rgba(60,50,30,.10);
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0}
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
.tabs{display:flex;gap:4px;margin-top:9px;background:rgba(255,255,255,.12);padding:3px;border-radius:12px}
.tabs button{flex:1;padding:7px 2px;border-radius:9px;font-size:11.5px;font-weight:600;color:#fff;opacity:.8;white-space:nowrap}
.tabs button.on{background:var(--card);color:var(--sage-dark);opacity:1;box-shadow:var(--shadow)}
.sortbar{display:flex;align-items:center;gap:8px;margin-top:8px;font-size:12.5px;color:rgba(255,255,255,.9)}
.sortbar select{background:rgba(255,255,255,.95);color:var(--ink);border:none;border-radius:8px;
  padding:5px 8px;font-size:12.5px;font-family:inherit}

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
.ent[onclick]:active{background:rgba(91,114,99,.2)}

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
    <button data-v="covers" class="on">Covers</button>
    <button data-v="list">List</button>
    <button data-v="series">Series</button>
    <button data-v="authors">Authors</button>
    <button data-v="genres">Genres</button>
  </div>
  <div class="sortbar" id="sortbar">
    <span>Sort</span>
    <select id="sort">
      <option value="author">Author A–Z</option>
      <option value="title">Title A–Z</option>
      <option value="year_new">Year (newest)</option>
      <option value="year_old">Year (oldest)</option>
    </select>
    <span id="viewnote" style="margin-left:auto;opacity:.85"></span>
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
let view = "covers", sortBy = "author", query = "";
const norm = s => (s||"").toLowerCase().replace(/^(the|a|an) /,"").replace(/[^a-z0-9]+/g," ").trim();
const enc = s => encodeURIComponent(s);

function load(){
  try{ const s = localStorage.getItem("lib_books"); if(s) return JSON.parse(s); }catch(e){}
  return CATALOG.map(b=>({...b}));
}
function persist(){ try{ localStorage.setItem("lib_books", JSON.stringify(books)); }catch(e){} }

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
  try{ const b=books.find(x=>x.id==el.dataset.id); if(b){ const url=await resolveCover(b); if(url) await setCover(el,url); } }catch(e){}
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
function filtered(){
  const q = norm(query);
  let a = books.filter(b=> !q || norm(b.title).includes(q)||norm(b.author).includes(q)||norm(b.series).includes(q)||norm(b.genre).includes(q));
  const lastName = s => { const p=(s||"").trim().split(" "); return p[p.length-1]||""; };
  a.sort((x,y)=>{
    if(sortBy==="title") return norm(x.title).localeCompare(norm(y.title));
    if(sortBy==="year_new") return (parseInt(y.year)||-9999)-(parseInt(x.year)||-9999);
    if(sortBy==="year_old") return (parseInt(x.year)||9999)-(parseInt(y.year)||9999);
    return norm(lastName(x.author)+" "+x.title).localeCompare(norm(lastName(y.author)+" "+y.title));
  });
  return a;
}

/* ---------- views ---------- */
function render(){
  document.getElementById("count").textContent = books.length+" books";
  document.getElementById("sortbar").style.display = (view==="series")?"none":"flex";
  const m = document.getElementById("main");
  const data = filtered();
  if(!data.length){ m.innerHTML = `<div class="empty">No books match “${esc(query)}”.</div>`; return; }
  if(view==="covers") renderCovers(m,data);
  else if(view==="list") renderList(m,data);
  else if(view==="series") renderSeries(m);
  else renderGroups(m,data, view==="authors"?"author":"genre");
  wireCovers(m);
}

function renderList(m,data){
  document.getElementById("viewnote").textContent = data.length+" shown";
  m.innerHTML = `<div class="group open"><div class="glist">`+data.map(b=>{
    let sTag = "";
    if(b.series){ const s=seriesMatch(b.series); sTag = s.placeholder?` · <span class="lser">${esc(b.series)}</span>`:` · <span class="lser">${esc(b.series)} (${s.haveCount}/${s.total})</span>`; }
    return `<div class="row lg" onclick="openBook(${b.id})">
      <div class="mini" data-id="${b.id}"><div class="mph">${esc(b.title)}</div></div>
      <div class="rmain"><div class="rt">${esc(b.title)}</div><div class="rs">${esc(b.author)}${b.year?" · "+b.year:""}${sTag}</div></div>
    </div>`;
  }).join("")+`</div></div>`;
}

function renderCovers(m,data){
  document.getElementById("viewnote").textContent = data.length+" shown";
  m.innerHTML = `<div class="grid">`+data.map(b=>`
    <button class="bcard" onclick="openBook(${b.id})">
      <div class="cover">${b.placeholder?'<span class="badge multi">series</span>':(b.series?'<span class="badge">series</span>':'')}
        <div class="ph" ${''}></div>
      </div>
      <div class="binfo"><div class="bt">${esc(b.title)}</div><div class="ba">${esc(b.author)}</div></div>
    </button>`).join("")+`</div>`;
  // inject cover placeholders with data-id
  m.querySelectorAll(".bcard").forEach((c,i)=>{ const b=data[i];
    const cv=c.querySelector(".cover"); const ph=cv.querySelector(".ph");
    cv.dataset.id=b.id;
    ph.innerHTML=`<div class="t">${esc(b.title)}</div><div class="a">${esc(b.author)}</div>`;
  });
}

function renderGroups(m,data,key){
  const groups={};
  data.forEach(b=>{ const g=(key==="author"?b.author:b.genre)||"—"; (groups[g]=groups[g]||[]).push(b); });
  const names=Object.keys(groups).sort((a,b)=>{
    if(key==="author"){ const ln=s=>{const p=s.trim().split(" ");return p[p.length-1];}; return norm(ln(a)).localeCompare(norm(ln(b))); }
    return a.localeCompare(b);
  });
  document.getElementById("viewnote").textContent = names.length+" "+(key==="author"?"authors":"genres");
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
  if(!db) return {db:null, owned, entries:[], haveCount:owned.length, total:owned.length, upcoming:[]};
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
  return {db, owned, entries, published, upcoming, haveCount, total, placeholder};
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
  const tag = up?`<span class="tag u">${esc(e.release_date||"upcoming")}</span>`
                :(s.placeholder?"":(e.have?`<span class="check">✓</span>`:`<span class="tag m">missing</span>`));
  const click = (oid!=null && oid!==curId) ? ` onclick="openBook(${oid})" style="cursor:pointer"` : "";
  return `<div class="ent ${cls}${isCur?' cur':''}"${click}><div class="num">${esc(e.index||"•")}</div>
    <div><div class="et">${esc(e.title)}${isCur?' <span class="curtag">this book</span>':''}</div>${e.year||e.release_date?`<div class="ey">${esc(up?("Releases "+(e.release_date||"TBA")):e.year)}</div>`:""}</div>${tag}</div>`;
}
function seriesEntriesHTML(s, curId){
  if(!s.db) return s.owned.map(b=>`<div class="ent have"><div class="num">•</div><div><div class="et">${esc(b.title)}</div></div><span class="check">✓</span></div>`).join("");
  let ents=s.entries, extra=0;
  if(s.placeholder && ents.length>8){ extra=ents.length-8; ents=ents.slice(0,8); }
  let html=ents.map(e=>entryRow(s,e,curId)).join("");
  if(extra) html+=`<div class="ent ref"><div class="num">…</div><div><div class="et" style="color:var(--muted);font-weight:500">+${extra} more in the series</div></div></div>`;
  return html;
}
function renderSeries(m){
  const q=norm(query);
  let names=[...new Set(books.filter(b=>b.series).map(b=>b.series))];
  names=names.filter(n=>!q||norm(n).includes(q)||books.some(b=>b.series===n&&(norm(b.title).includes(q)||norm(b.author).includes(q))));
  names.sort();
  if(!names.length){ m.innerHTML=`<div class="empty">No series found.</div>`; return; }
  m.innerHTML = names.map(n=>{
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
  const online = STORES.online.map(s=>`<a class="buy" href="${s.search}${enc(q)}" target="_blank" rel="noopener"><span class="bn">${esc(s.name)}</span><span class="bk">search &rsaquo;</span></a>`).join("");
  const local = STORES.local.map(s=>{
    const href = s.search? s.search+enc(q) : s.url;
    return `<a class="buy local" href="${href}" target="_blank" rel="noopener"><span class="bn">${esc(s.name)}</span><span class="bk">${esc(s.kind)} · ${esc(s.city)}</span></a>`;
  }).join("");
  return {online, local};
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
  document.getElementById("sheetbody").innerHTML=`
    <div class="dtop">
      <div class="dcover" data-id="${b.id}" id="dcover"><div class="ph mph" style="font-size:11px;padding:8px;text-align:center">${esc(b.title)}</div></div>
      <div class="dmeta">
        <h2>${esc(b.title)}</h2>
        <div class="dau">${esc(b.author)}</div>
        <div>${b.genre?`<span class="pill">${esc(b.genre)}</span>`:""}${b.year?`<span class="pill">${esc(b.year)}</span>`:""}${b.shelf?`<span class="pill">${esc(b.shelf)}</span>`:""}</div>
      </div>
    </div>
    ${b.notes?`<div class="dnotes">${esc(b.notes)}</div>`:""}
    ${seriesBlock}
    <div class="sect"><h4>Local to Livingston, TN</h4><div class="btns">${bl.local}</div></div>
    <div class="sect"><h4>Buy online</h4><div class="btns">${bl.online}</div></div>`;
  // detail cover
  const dc=document.getElementById("dcover");
  resolveCover(b).then(url=>{ if(url){ const img=new Image(); img.onload=()=>{dc.querySelector(".mph").style.display="none";dc.insertBefore(img,dc.firstChild);}; img.src=url; } });
  openSheet();
}
function openSheet(){ document.getElementById("scrim").classList.add("on"); document.getElementById("sheet").classList.add("on"); }
function closeSheet(){ document.getElementById("scrim").classList.remove("on"); document.getElementById("sheet").classList.remove("on"); }

/* ---------- settings / import ---------- */
function openSettings(){
  document.getElementById("sheetbody").innerHTML=`<div class="panel">
    <h3>Library settings</h3>
    <p style="font-size:13px;color:var(--muted);margin:4px 0 0">${books.length} books · ${Object.keys(SERIES_DB).length} series tracked</p>
    <label class="imp" for="csv">Import from Libib (CSV)</label>
    <input id="csv" type="file" accept=".csv,text/csv" style="display:none">
    <button class="imp sec" onclick="resetLib()">Reset to sample library</button>
    <div class="hint"><b>How to export from Libib</b> (on Dani's phone):
      <ol><li>Open the Libib app → <b>Menu</b> (☰)</li>
      <li>Tap your library → <b>Settings / Manage</b></li>
      <li>Choose <b>Export</b> → <b>CSV</b> (email it to yourself or save to Files)</li>
      <li>Come back here → <b>Import from Libib</b> → pick that .csv</li></ol>
      Covers, genres and series update automatically from the ISBNs in the file.</div>
  </div>`;
  document.getElementById("csv").addEventListener("change", handleCSV);
  openSheet();
}
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
          isbn, confidence:"import", notes:"" });
      }
      if(!out.length){ toast("No rows found — is this a Libib CSV?"); return; }
      books=out; persist(); closeSheet(); view="covers"; setTab("covers"); render();
      toast("Imported "+out.length+" books from Libib");
    }catch(err){ toast("Could not read that CSV"); }
  };
  rd.readAsText(f);
}

/* ---------- ui wiring ---------- */
function setTab(v){ view=v; document.querySelectorAll("#tabs button").forEach(b=>b.classList.toggle("on",b.dataset.v===v)); render(); }
document.getElementById("tabs").addEventListener("click",e=>{ const b=e.target.closest("button"); if(b) setTab(b.dataset.v); });
document.getElementById("sort").addEventListener("change",e=>{ sortBy=e.target.value; render(); });
document.getElementById("q").addEventListener("input",e=>{ query=e.target.value; render(); });
document.getElementById("gear").addEventListener("click",openSettings);
document.getElementById("scrim").addEventListener("click",closeSheet);
let toastT; function toast(m){ const t=document.getElementById("toast"); t.textContent=m; t.classList.add("on"); clearTimeout(toastT); toastT=setTimeout(()=>t.classList.remove("on"),2600); }

render();
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
