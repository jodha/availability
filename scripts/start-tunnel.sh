#!/usr/bin/env bash
set -euo pipefail

if ! command -v cloudflared >/dev/null 2>&1; then
  ARCH="$(uname -m)"
  FILE="cloudflared-linux-amd64"
  [[ "$ARCH" == "aarch64" ]] && FILE="cloudflared-linux-arm64"
  curl -fL -o cloudflared "https://github.com/cloudflare/cloudflared/releases/latest/download/${FILE}"
  chmod +x cloudflared
  sudo mv cloudflared /usr/local/bin/
fi

echo "Starting Cloudflare tunnel. Copy the full https://....trycloudflare.com URL from the output."
cloudflared tunnel --url http://localhost:8000
