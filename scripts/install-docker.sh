#!/usr/bin/env bash
set -euo pipefail

if command -v docker >/dev/null 2>&1 && systemctl is-active docker >/dev/null 2>&1; then
  echo "Docker is already installed and running."
  docker ps
  exit 0
fi

sudo apt update
if sudo apt install -y docker.io docker-compose-v2 git; then
  sudo systemctl enable --now docker
else
  sudo apt install -y ca-certificates curl git
  curl -fsSL https://get.docker.com | sudo sh
fi

sudo usermod -aG docker "$USER"
echo "Docker installed. Run 'newgrp docker' or log out and back in if docker ps fails."
docker ps
