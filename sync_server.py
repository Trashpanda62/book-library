#!/usr/bin/env python3
"""Tiny shared-file sync endpoint for the Our Library app.

Stores the whole library+wishlist as a single JSON file and serves it over HTTP.
Put it on a tailnet host and expose it over HTTPS with `tailscale serve` (see SYNC.md),
then paste that https URL into the app's Settings -> Sync.

  GET  /library  -> returns the stored JSON ({} if none yet)
  PUT  /library  -> replaces the stored JSON with the request body
  GET  /health   -> "ok"

Last-write-wins: the app sends {updated, books, wishlist}; whichever device saved
most recently wins. Fine for a household of a couple devices.

Run:  python sync_server.py [--port 8799] [--file library.json]
"""
import argparse, json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8799)
ap.add_argument("--host", default="0.0.0.0")
ap.add_argument("--file", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.json"))
ARGS = ap.parse_args()

def cors(h):
    h.send_header("Access-Control-Allow-Origin", "*")
    h.send_header("Access-Control-Allow-Methods", "GET, PUT, OPTIONS")
    h.send_header("Access-Control-Allow-Headers", "Content-Type")

class H(BaseHTTPRequestHandler):
    def _send(self, code, body=b"", ctype="application/json"):
        self.send_response(code)
        cors(self)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204)

    def do_GET(self):
        if self.path.rstrip("/") == "/health":
            return self._send(200, b"ok", "text/plain")
        if self.path.rstrip("/") == "/library":
            if os.path.exists(ARGS.file):
                with open(ARGS.file, "rb") as f:
                    return self._send(200, f.read())
            return self._send(200, b"{}")
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
        pass  # quiet

if __name__ == "__main__":
    srv = ThreadingHTTPServer((ARGS.host, ARGS.port), H)
    print(f"Our Library sync on http://{ARGS.host}:{ARGS.port}  (file: {ARGS.file})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
