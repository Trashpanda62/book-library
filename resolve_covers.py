#!/usr/bin/env python3
"""Resolve a real cover image URL for every book and bake it into books_enriched.json.
Primary source Google Books (broad coverage, reliable thumbnails), fallback Open Library.
Verifies each URL returns a 200 image so the phone never waits on a dead link."""
import json, os, re, time, urllib.parse, urllib.request, concurrent.futures

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "books_enriched.json")
UA = {"User-Agent": "Mozilla/5.0 (library-cover-resolver)"}

def _get(url, timeout=12):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(), r.headers.get("Content-Type", "")

def verify_img(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=12) as r:
            ct = r.headers.get("Content-Type", "")
            if r.status == 200 and ct.startswith("image"):
                data = r.read(2048)
                return len(data) > 500  # OL returns a tiny 1px blank for missing
    except Exception:
        return False
    return False

def clean_title(t):
    t = re.sub(r"\s*\(multiple\).*", "", t, flags=re.I)
    t = re.sub(r"\s*series.*", "", t, flags=re.I)
    t = re.sub(r"\s*collection.*", "", t, flags=re.I)
    t = re.sub(r"\s*novels.*", "", t, flags=re.I)
    t = re.sub(r"\s*mysteries.*", "", t, flags=re.I)
    t = t.split(":")[0]
    return t.strip()

def google(title, author):
    q = 'intitle:"%s"' % clean_title(title)
    if author and "(" not in author:
        q += ' inauthor:"%s"' % author.split(" and ")[0].split("(")[0].strip()
    url = "https://www.googleapis.com/books/v1/volumes?country=US&maxResults=3&q=" + urllib.parse.quote(q)
    for attempt in range(3):
        try:
            st, body, _ = _get(url)
            if st == 429:
                return "", ""  # rate limited: give up on Google, other sources will cover it
            j = json.loads(body)
            for it in j.get("items", []):
                vi = it.get("volumeInfo", {})
                il = vi.get("imageLinks", {})
                thumb = il.get("thumbnail") or il.get("smallThumbnail")
                isbn = ""
                for idf in vi.get("industryIdentifiers", []):
                    if idf.get("type") == "ISBN_13":
                        isbn = idf.get("identifier", "")
                if thumb:
                    thumb = thumb.replace("http://", "https://").replace("&edge=curl", "")
                    thumb = re.sub(r"zoom=\d", "zoom=1", thumb)
                    return thumb, isbn
            return "", ""
        except Exception:
            time.sleep(1)
    return "", ""

def google_loose(title, author):
    # forgiving free-text query, no field operators
    terms = clean_title(title)
    if author and "(" not in author:
        terms += " " + author.split(" and ")[0].split("(")[0].strip()
    url = "https://www.googleapis.com/books/v1/volumes?country=US&maxResults=5&q=" + urllib.parse.quote(terms)
    for attempt in range(3):
        try:
            st, body, _ = _get(url)
            if st == 429:
                return "", ""  # rate limited: give up on Google, other sources will cover it
            j = json.loads(body)
            for it in j.get("items", []):
                il = it.get("volumeInfo", {}).get("imageLinks", {})
                thumb = il.get("thumbnail") or il.get("smallThumbnail")
                if thumb:
                    thumb = thumb.replace("http://", "https://").replace("&edge=curl", "")
                    return re.sub(r"zoom=\d", "zoom=1", thumb), ""
            return "", ""
        except Exception:
            time.sleep(1)
    return "", ""

def itunes(title, author):
    # Apple Books artwork API — generous, no key, good commercial-title coverage
    term = clean_title(title)
    if author and "(" not in author:
        term += " " + author.split(" and ")[0].split("(")[0].strip()
    url = "https://itunes.apple.com/search?media=ebook&limit=1&term=" + urllib.parse.quote(term)
    try:
        st, body, _ = _get(url)
        j = json.loads(body)
        for r in j.get("results", []):
            art = r.get("artworkUrl100") or r.get("artworkUrl60")
            if art:
                return re.sub(r"/\d+x\d+bb\.(jpg|png)", "/400x400bb.jpg", art), ""
    except Exception:
        pass
    return "", ""

def openlib(title, author):
    try:
        url = ("https://openlibrary.org/search.json?limit=1&fields=cover_i,isbn&title="
               + urllib.parse.quote(clean_title(title)) + "&author=" + urllib.parse.quote(author or ""))
        st, body, _ = _get(url)
        d = (json.loads(body).get("docs") or [{}])[0]
        if d.get("cover_i"):
            return "https://covers.openlibrary.org/b/id/%d-M.jpg" % d["cover_i"], (d.get("isbn") or [""])[0]
        if d.get("isbn"):
            return "https://covers.openlibrary.org/b/isbn/%s-M.jpg" % d["isbn"][0], d["isbn"][0]
    except Exception:
        pass
    return "", ""

def resolve(b):
    title, author = b.get("title", ""), b.get("author", "")
    # try Google first
    url, isbn = google(title, author)
    if url and verify_img(url):
        return url, isbn
    # Apple Books artwork (not rate limited like Google)
    urla, _ = itunes(title, author)
    if urla and verify_img(urla):
        return urla, isbn
    # Open Library
    url2, isbn2 = openlib(title, author)
    if url2 and verify_img(url2):
        return url2, isbn2 or isbn
    # last resort: forgiving free-text Google query
    url3, _ = google_loose(title, author)
    if url3 and verify_img(url3):
        return url3, isbn or isbn2
    return "", isbn or isbn2

def main():
    data = json.load(open(SRC, encoding="utf-8"))
    books = data["books"]
    todo = [i for i, b in enumerate(books) if not b.get("cover")]  # only resolve misses on re-run
    print("resolving %d books lacking a cover" % len(todo))
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(resolve, books[i]): i for i in todo}
        for f in concurrent.futures.as_completed(futs):
            i = futs[f]
            try:
                results[i] = f.result()
            except Exception:
                results[i] = ("", "")
    for i in todo:
        url, isbn = results.get(i, ("", ""))
        if url:
            books[i]["cover"] = url
        if isbn and not books[i].get("isbn13"):
            books[i]["isbn13"] = isbn
    json.dump(data, open(SRC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    got = sum(1 for b in books if b.get("cover"))
    print("resolved %d / %d covers" % (got, len(books)))
    misses = [b["title"] for b in books if not b.get("cover")]
    if misses:
        print("no cover:", " | ".join(misses[:40]))

if __name__ == "__main__":
    main()
