#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

bash scripts/install-docker.sh
bash scripts/setup-env.sh
echo ""
echo "Edit .env now, then run:"
echo "  bash scripts/start-app.sh"
echo "  bash scripts/start-tunnel.sh"
echo ""
echo "Admin steps after the tunnel URL is ready:"
echo "  1. Set BASE_URL in .env to your trycloudflare.com URL"
echo "  2. docker compose up -d"
echo "  3. Open BASE_URL/admin and create a poll"
echo "  4. Add events and share the invite code"
