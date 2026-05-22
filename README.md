# Availability

Share a poll link with friends so they can mark yes, no, or maybe for each event you create. Supports 1 to 30 events per poll.

## Features

- Separate admin login at `/admin`
- Invite-only user signup
- Email and password login with display names
- Users see everyone's availability
- Users can update answers anytime
- Email calendar file for Yes and Maybe events
- Single timezone: configured in `.env` (default `America/Denver`)

## Local development (macOS or Ubuntu)

```bash
cd ubuntu_proj
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

Run tests:

```bash
PYTHONPATH=. pytest
```

## Ubuntu 24.04 production setup

### 1. Install Docker

First check whether Docker is installed:

```bash
which docker
systemctl status docker
dpkg -l | grep docker
```

If you see `Unit docker.service could not be found`, Docker Engine is **not installed yet**.

#### Option A: Ubuntu packages (simplest)

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
newgrp docker
docker ps
```

#### Option B: Official Docker install script (if Option A fails)

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker
docker ps
```

Verify Docker works **without sudo**:

```bash
docker ps
```

If you see `permission denied` on `/var/run/docker.sock`, your user is not in the `docker` group yet. Run:

```bash
sudo usermod -aG docker "$USER"
newgrp docker
docker ps
```

If it still fails, log out of Ubuntu completely and log back in (or reboot), then run `docker ps` again.

Temporary workaround (not recommended long-term):

```bash
sudo docker compose up -d --build
```

### 2. Clone and configure

```bash
git clone YOUR_GITHUB_REPO_URL availability
cd availability
cp .env.example .env
nano .env
```

Set these values in `.env`:

- `SECRET_KEY` — long random string
- `ADMIN_USERNAME` and `ADMIN_PASSWORD` — your admin login
- `INVITE_CODE` — code you share with friends for signup
- `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` — Gmail and app password
- `BASE_URL` — your public URL once the tunnel is running

### 3. Start the app

Run this from the folder that contains `Dockerfile` and `docker-compose.yml`:

```bash
cd availability
ls Dockerfile docker-compose.yml
docker compose build --no-cache
docker compose up -d
```

Use `--build` if you prefer one command:

```bash
docker compose up -d --build
```

The app listens on port 8000.

#### "image availability-web is not gettable"

That means Docker tried to **download** the image from the internet instead of **building** it locally. Fix:

```bash
cd availability
docker compose build
docker compose up -d
```

Do not run `docker compose pull` for this project. If build fails, check you cloned the full repo and have network access for `pip install` inside the build.

### 4. Expose with Cloudflare Tunnel (free HTTPS link)

Install cloudflared:

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
```

Quick temporary URL:

```bash
cloudflared tunnel --url http://localhost:8000
```

Copy the `https://*.trycloudflare.com` URL and set `BASE_URL` in `.env` to that value, then restart:

```bash
docker compose up -d
```

Share the HTTPS link and your invite code with friends.

### 5. Admin workflow

1. Open `https://YOUR-URL/admin`
2. Log in with admin credentials
3. Create a poll
4. Add events (title, start time, location) — up to 30 per poll
5. Share the site link and invite code
6. View the availability table on the admin page

## Push to GitHub

From your dev machine:

```bash
cd ubuntu_proj
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

## Data

SQLite database is stored in the Docker volume `availability_data` at `/data/availability.db`.
