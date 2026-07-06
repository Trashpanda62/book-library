# Cross-device sync (tailnet, shared file)

The app normally stores your library in each device's browser. To make **your phone,
Dani's phone, and the PC all show the same library**, run one tiny sync endpoint on a
box that's always on (e.g. the TrueNAS server) and point every device at it.

The app is served from HTTPS (GitHub Pages), so the sync endpoint **must be HTTPS** too —
`tailscale serve` gives you that for free on your tailnet.

## 1. Run the sync server on a tailnet host

```bash
python sync_server.py --port 8799 --file /mnt/Truenas/Network-Drive/claude-share/library.json
```

Keep it running (systemd service, a Task Scheduler job on Windows, or `nohup`/tmux on Linux).
It stores everything in that one JSON file — that file *is* the shared library, so it's
also your backup.

## 2. Expose it over HTTPS on the tailnet

```bash
tailscale serve --bg --https=443 http://localhost:8799
```

Tailscale prints the URL, e.g. `https://truenas.tail1234.ts.net`. That host is only
reachable by your own tailnet devices — it is **not** public.

Check it: open `https://truenas.tail1234.ts.net/health` on a device that's on the tailnet;
it should say `ok`.

## 3. Point the app at it

On each device: open the app → ⚙ **Settings → Sync across devices** → paste
`https://truenas.tail1234.ts.net` → **Save endpoint**. Tap **Sync now ↓** once to pull.

From then on, every change pushes automatically, and **Sync now** pulls the latest.
Last edit wins. Devices must be on the tailnet (VPN on) to sync; offline, they keep working
locally and sync next time they're on.

## Notes
- No auth on the endpoint by design — access is already gated by tailnet membership.
- To reset sync, clear the endpoint field and Save.
- The JSON file is safe to copy/back up anytime.
