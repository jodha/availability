#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  echo ".env already exists. Edit it manually if needed."
  exit 0
fi

cp .env.example .env
python3 - <<'PY'
import secrets
from pathlib import Path

path = Path(".env")
text = path.read_text()
text = text.replace("change-me-to-a-long-random-string", secrets.token_hex(32))
path.write_text(text)
PY
echo "Created .env with a generated SECRET_KEY."
echo "Edit .env to set ADMIN_PASSWORD, INVITE_CODE, SMTP settings, and BASE_URL."
