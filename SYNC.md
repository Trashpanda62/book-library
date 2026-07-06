# Cross-device sync — LIVE (public, no VPN)

Sync is set up and running. Every device that opens the app shares one library
(last edit wins). **No tailnet / VPN / app required** — the endpoint is public HTTPS,
baked into the app.

**Endpoint:** `https://books.retrogaming.win`  (Cloudflare Tunnel → home TrueNAS)

## How it's deployed (for reference / rebuild)

Host: TrueNAS `keen-truenas` (tailnet 100.87.208.99; SSH `root@` with `~/.ssh/truenas_claude`).

1. **Sync server** — Docker container, auto-restarts on boot:
   ```bash
   docker run -d --name booklib-sync --restart unless-stopped --network host \
     -v /mnt/Truenas/Network-Drive/book-library-sync:/data \
     python:3.12-alpine \
     python3 /data/sync_server.py --port 8799 --file /data/library.json
   ```
   Shared library + backup file: `/mnt/Truenas/Network-Drive/book-library-sync/library.json`
   (also `Z:\book-library-sync\library.json` on Windows).

2. **Public HTTPS** — the existing host-networked `cloudflared` tunnel routes a hostname to it.
   Added via the Cloudflare API (token in the vault secrets):
   - Tunnel ingress rule: `books.retrogaming.win` → `http://127.0.0.1:8799`
   - DNS: CNAME `books.retrogaming.win` → `<tunnel-id>.cfargotunnel.com` (proxied)
   - Cloudflare account `4468938c…`, tunnel `12c9cb2b-…`, zone `retrogaming.win`.
   The tunnel config lives in Cloudflare (dashboard-managed) so it persists across reboots.

   A tailnet-only `tailscale serve` on `:8443` also still exists as a private fallback.

## Ops
- Status:  `curl https://books.retrogaming.win/health`  (→ `ok`)
- Logs:    `docker logs booklib-sync`
- Restart: `docker restart booklib-sync`
- Reset shared library: `rm /mnt/Truenas/Network-Drive/book-library-sync/library.json`
- Turn off in the app: Settings → Sync → clear the box → Save.

## Notes / caveats
- The endpoint is **public and unauthenticated** — anyone with the app URL pulls the library,
  and an edit from any device pushes (last-write-wins). Fine for a shared/family wishlist.
  If we later want a read-only "share" link or a write token, that's a small addition.
