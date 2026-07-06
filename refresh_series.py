#!/usr/bin/env python3
"""Nightly refresh of the Series "Coming Soon" data.

Reliable pass (no network): any 'upcoming' entry whose release date has passed is
flipped to 'published', so released books drop out of Coming Soon on their own.

Best-effort pass (Google Books): looks for FUTURE-dated (pre-order) volumes by each
tracked series' author and adds them as upcoming — but only when the volume's title/
subtitle actually names the series, to avoid pulling in the author's other work.
Any network/quota error is swallowed; the reliable pass still runs.
"""
import json, os, re, datetime, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "series_db.json")
TODAY = datetime.date.today()

def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def parse_date(s):
    s = (s or "").strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m: return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"(\d{4})-(\d{2})$", s)
    if m: return datetime.date(int(m.group(1)), int(m.group(2)), 28)
    m = re.match(r"^(\d{4})$", s)
    if m: return datetime.date(int(m.group(1)), 12, 31)
    return None  # "TBA", "2026 (TBA)", etc. -> leave as-is

# author + a token that must appear in a volume's title/subtitle to count as this series
SERIES = {
    "Scot Harvath":        ("Brad Thor",         ["harvath"]),
    "Mitch Rapp":          ("Don Bentley",       ["rapp"]),
    "Cormoran Strike":     ("Robert Galbraith",  ["cormoran strike", "strike"]),
    "Women's Murder Club": ("James Patterson",   ["women s murder club", "murder club"]),
}

def google_books(author):
    try:
        u = ("https://www.googleapis.com/books/v1/volumes?country=US&orderBy=newest&maxResults=20&q="
             + urllib.parse.quote('inauthor:"%s"' % author))
        req = urllib.request.Request(u, headers={"User-Agent": "book-library-refresh"})
        with urllib.request.urlopen(req, timeout=25) as r:
            j = json.load(r)
        out = []
        for it in j.get("items", []):
            v = it.get("volumeInfo", {})
            full = (v.get("title", "") + " " + v.get("subtitle", "")).strip()
            out.append((v.get("title", "").strip(), full, v.get("publishedDate", "")))
        return out
    except Exception:
        return []

def main():
    d = json.load(open(P, encoding="utf-8"))
    changed = False

    # 1) reliable: released -> published
    for s in d["series"]:
        for e in s["entries"]:
            if e.get("status") == "upcoming":
                dt = parse_date(e.get("release_date") or e.get("year"))
                if dt and dt < TODAY:
                    e["status"] = "published"
                    e["release_date"] = ""
                    changed = True

    # 2) best-effort: discover future pre-orders that name the series
    for s in d["series"]:
        info = SERIES.get(s["series"])
        if not info:
            continue
        author, tokens = info
        have = {norm(e["title"]) for e in s["entries"]}
        for title, full, pub in google_books(author):
            dt = parse_date(pub)
            fulln = norm(full)
            if (dt and dt > TODAY and title and norm(title) not in have
                    and any(t in fulln for t in tokens)):
                s["entries"].append({"index": "", "title": title, "year": pub[:4],
                                     "status": "upcoming", "release_date": pub})
                have.add(norm(title))
                changed = True
                print("added upcoming:", s["series"], "-", title, pub)

    if changed:
        json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("series_db.json updated")
    else:
        print("no changes")

if __name__ == "__main__":
    main()
