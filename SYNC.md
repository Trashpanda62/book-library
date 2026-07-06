# Cross-device sync — LIVE

Cross-device sync is **set up and running** on the home TrueNAS. Every device that opens
the app while on the tailnet shares one library (last edit wins). Nothing to configure —
the endpoint is baked into the app.

**Endpoint:** `https://keen-truenas.tailfbd25a.ts.net:8443` (tailnet-only, not public)

## How it's deployed (for reference / rebuild)

Host: TrueNAS `keen-truenas` (100.87.208.99).

1. **Sync server** — a Docker container, auto-restarts on boot:
   ```bash
   docker run -d --name booklib-sync --restart unless-stopped --network host \
     -v /mnt/Truenas/Network-Drive/book-library-sync:/data \
     python:3.12-alpine \
     python3 /data/sync_server.py --port 8799 --file /data/library.json
   ```
   The shared library lives at `/mnt/Truenas/Network-Drive/book-library-sync/library.json`
   (also reachable on Windows at `Z:\book-library-sync\library.json`). That file *is* the
   backup — copy it anytime.

2. **HTTPS over tailnet** — `tailscale serve` inside the host-networked `tailscale` container
   proxies the tailnet HTTPS port to the sync server:
   ```bash
   docker exec tailscale tailscale serve --bg --https=8443 http://localhost:8799
   ```
   (Port 8443 is used because TrueNAS nginx already owns 443. The serve config persists.)

## Ops

- Status:   `docker exec tailscale tailscale serve status`
- Logs:     `docker logs booklib-sync`
- Restart:  `docker restart booklib-sync`
- Turn off in the app: Settings → Sync → clear the box → Save.
- Reset the shared library: `rm /mnt/Truenas/Network-Drive/book-library-sync/library.json`

## Notes
- No auth by design — access is gated by tailnet membership.
- Devices must be on the tailnet (VPN on) to sync; offline they keep working locally and
  sync next time they're on.
