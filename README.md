# Availability

Share a poll link with friends so they can mark yes, no, or maybe for each event you create. Supports 1 to 30 events per poll.

**Repo:** https://github.com/jodha/availability

## Features

- Separate admin login at `/admin`
- **Email whitelist login** — no password; allowed emails in `allowed_emails.txt` + admin UI
- First visit: pick a display name once
- **Global location catalog** — add venues once, pick when creating events
- Users see everyone's availability
- Users can update answers anytime
- **iMIP calendar invites** — one email per Yes/Maybe event (Add to calendar)
- Admin can **resend calendar invites** when a location changes
- Single timezone: configured in `.env` (default `America/Denver`)

## Quick start on Ubuntu 24.04

```bash
git clone https://github.com/jodha/availability.git
cd availability
bash scripts/ubuntu-setup.sh
nano .env
nano allowed_emails.txt
bash scripts/start-app.sh
bash scripts/start-tunnel.sh
```

## Configure

**`.env`** — secrets, SMTP, `BASE_URL`

**`allowed_emails.txt`** — one email per line (who may log in)

## Admin workflow

1. Add allowed emails and locations (venue + address)
2. Create a poll
3. Add events — pick location or add inline
4. Share site link with allowed users
5. If a location changes, use **Resend calendar invites** for affected events

## Run tests

```bash
pytest
```
