# VPS deployment (public demo)

This runs the public web demo: the FastAPI backend directly on the VPS host
(so it talks to the real Docker daemon the same way the local stdio tool
does — no socket-mounted container needed), plus the 3 sandboxed demo
containers, plus a periodic reset job. The frontend (`web/`) is deployed
separately to Vercel and is not part of this setup.

Tested against a small Hetzner/DigitalOcean box (1 vCPU / 2GB RAM is plenty).

## 1. Provision the box

- Ubuntu 22.04/24.04, a non-root user with sudo (`cyberrescue` in the units below).
- Point a DNS A record (e.g. `api.your-domain.example`) at the box's IP.

## 2. Install system dependencies

```bash
sudo apt update
sudo apt install -y git build-essential
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker cyberrescue
curl -LsSf https://astral.sh/uv/install.sh | sh   # as the cyberrescue user
sudo apt install -y caddy   # or: https://caddyserver.com/docs/install
```

Log out/in (or `newgrp docker`) so the `docker` group membership takes effect.

## 3. Clone and install

```bash
sudo mkdir -p /opt/cyberrescue && sudo chown cyberrescue:cyberrescue /opt/cyberrescue
git clone https://github.com/vivekpatil200320/cyberrescue.git /opt/cyberrescue
cd /opt/cyberrescue
uv sync --all-packages
```

## 4. Build and start the 3 demo containers

```bash
cd /opt/cyberrescue/infra
docker compose up -d --build
docker ps   # confirm broken-flask, leaking-node, crashed-nginx are present
```

## 5. Configure backend secrets

```bash
sudo mkdir -p /etc/cyberrescue
sudo cp /opt/cyberrescue/backend/.env.example /etc/cyberrescue/backend.env
sudo chmod 600 /etc/cyberrescue/backend.env
sudo $EDITOR /etc/cyberrescue/backend.env
```

Set at minimum:
- `ANTHROPIC_API_KEY` — server-side only key for the `/narrate` route.
- `ALLOWED_ORIGINS` — the exact Vercel URL(s) for the frontend, comma-separated.

## 6. Install and enable the systemd units

```bash
sudo cp /opt/cyberrescue/infra/systemd/*.service /opt/cyberrescue/infra/systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cyberrescue-backend.service
sudo systemctl enable --now cyberrescue-reset.timer
```

Check status/logs:

```bash
systemctl status cyberrescue-backend
journalctl -u cyberrescue-backend -f
systemctl list-timers cyberrescue-reset.timer
journalctl -u cyberrescue-reset
```

## 7. TLS + reverse proxy

```bash
sudo cp /opt/cyberrescue/infra/Caddyfile /etc/caddy/Caddyfile
# edit the domain in that file first
sudo systemctl reload caddy
```

Caddy issues a Let's Encrypt certificate automatically on first request.

## 8. Verify

```bash
curl https://api.your-domain.example/healthz
curl https://api.your-domain.example/api/containers
```

## 9. Deploying updates

`.github/workflows/ci.yml` has a `deploy` job that SSHes into the VPS on every push to `main`
(after tests pass). It's inert until you add these repo secrets (Settings → Secrets and
variables → Actions):

- `VPS_HOST` — the box's IP or hostname.
- `VPS_USER` — the deploy user (e.g. `cyberrescue`), must have passwordless `sudo systemctl restart cyberrescue-backend` and docker group membership.
- `VPS_SSH_KEY` — private key for a dedicated deploy keypair (add the public half to `~cyberrescue/.ssh/authorized_keys` on the box).

Without those secrets, the deploy job simply fails harmlessly — lint/test jobs are unaffected.
It runs the same steps as below:

```bash
cd /opt/cyberrescue && git pull
uv sync --all-packages
sudo systemctl restart cyberrescue-backend
cd infra && docker compose up -d --build
```
