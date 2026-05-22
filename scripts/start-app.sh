#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env. Run scripts/setup-env.sh first."
  exit 1
fi

docker compose up -d --build
docker compose ps
curl -fsS http://localhost:8000 >/dev/null
echo "App is running at http://localhost:8000"
