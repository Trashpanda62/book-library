#!/usr/bin/env python3
"""Shared-file sync endpoint for the Our Library app + ebook proxy.

  GET  /library      -> stored library JSON ({} if none)
  PUT  /library      -> replace stored library JSON
  GET  /health       -> "ok"
  GET  /ebooks       -> manifest of readable ebooks in the Calibre library:
                        [{id,title,author,slug}]  (only books that have an .epub)
  GET  /ebook/<id>   -> streams that book's .epub bytes (CORS) for in-app epub.js

The ebook endpoints read the Calibre-Web-Automated library mounted read-only at
/calibre-library (metadata.db + <author>/<title> (id)/<file>.epub). Same public
HTTPS origin as sync (books.retrogaming.win) so the HTTPS PWA can fetch with no
mixed-content and no cross-origin block.
"""
import argparse, json, os, re, sqlite3, glob, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8799)
ap.add_argument("--host", default="0.0.0.0")
ap.add_argument("--file", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.json"))
ap.add_argument("--calibre", default="/calibre-library")
ARGS = ap.parse_args()

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")

def cors(h):
    h.send_header("Access-Control-Allow-Origin", "*")
    h.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
    h.send_header("Access-Control-Allow-Headers", "Content-Type")

def _db():
    # open read-only; tolerate WAL
    return sqlite3.connect(f"file:{ARGS.calibre}/metadata.db?mode=ro", uri=True, timeout=5)

def _epub_path(rel_path):
    d = os.path.join(ARGS.calibre, rel_path)
    hits = sorted(glob.glob(os.path.join(d, "*.epub")))
    return hits[0] if hits else None

def list_ebooks():
    out = []
    try:
        c = _db()
        for bid, title, author, path in c.execute("SELECT id,title,author_sort,path FROM books"):
            if _epub_path(path):
                # author_sort is "Last, First" -> flip to "First Last" for display/match
                disp = author
                if author and "," in author:
                    a, b = author.split(",", 1); disp = f"{b.strip()} {a.strip()}"
                out.append({"id": bid, "title": title, "author": disp, "slug": slugify(title)})
        c.close()
    except Exception as e:
        sys.stderr.write(f"list_ebooks error: {e}\n")
    return out

class H(BaseHTTPRequestHandler):
    def _send(self, code, body=b"", ctype="application/json", extra=None):
        self.send_response(code)
        cors(self)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204)

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if self.path in ("/", "") or self.path.startswith("/?"):
            self.send_response(302); cors(self)
            self.send_header("Location", "https://trashpanda62.github.io/book-library/")
            self.end_headers(); return
        if path == "/health":
            return self._send(200, b"ok", "text/plain")
        if path == "/library":
            if os.path.exists(ARGS.file):
                with open(ARGS.file, "rb") as f:
                    return self._send(200, f.read())
            return self._send(200, b"{}")
        if path == "/ebooks":
            body = json.dumps(list_ebooks()).encode("utf-8")
            return self._send(200, body, extra={"Cache-Control": "no-cache"})
        m = re.match(r"^/ebook/(\d+)$", path)
        if m:
            bid = int(m.group(1))
            try:
                c = _db()
                row = c.execute("SELECT path,title FROM books WHERE id=?", (bid,)).fetchone()
                c.close()
            except Exception:
                row = None
            if not row:
                return self._send(404, b'{"error":"no such book"}')
            fp = _epub_path(row[0])
            if not fp or not os.path.exists(fp):
                return self._send(404, b'{"error":"no epub for book"}')
            with open(fp, "rb") as f:
                data = f.read()
            fn = slugify(row[1])[:60] or "book"
            return self._send(200, data, "application/epub+zip",
                              extra={"Content-Disposition": f'inline; filename="{fn}.epub"',
                                     "Cache-Control": "public, max-age=86400"})
        self._send(404, b'{"error":"not found"}')

    def do_PUT(self):
        if self.path.rstrip("/") != "/library":
            return self._send(404, b'{"error":"not found"}')
        n = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            data = json.loads(raw.decode("utf-8"))
            assert isinstance(data, dict) and isinstance(data.get("books"), list)
        except Exception:
            return self._send(400, b'{"error":"expected {books:[...]}"}')
        tmp = ARGS.file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, ARGS.file)
        self._send(200, b'{"ok":true}')

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    srv = ThreadingHTTPServer((ARGS.host, ARGS.port), H)
    print(f"Our Library sync+ebooks on http://{ARGS.host}:{ARGS.port} (file={ARGS.file} calibre={ARGS.calibre})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
