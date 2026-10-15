#!/usr/bin/env bash
# Publish the site from this machine to a Lightsail instance that
# lightsail-setup.sh has already prepared.
#   ./deploy/push.sh ubuntu@STATIC_IP
set -euo pipefail

HOST="${1:-}"
if [[ -z "$HOST" ]]; then
  echo "Usage: ./deploy/push.sh ubuntu@STATIC_IP" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
rsync -az --delete \
  --exclude '.git/' \
  --exclude 'deploy/' \
  --exclude 'README.md' \
  --exclude '.gitignore' \
  --exclude '.DS_Store' \
  -e ssh \
  --rsync-path="sudo rsync" \
  "$ROOT"/ "${HOST}:/var/www/richardwinfred/"
ssh "$HOST" "sudo chown -R www-data:www-data /var/www/richardwinfred && sudo nginx -t && sudo systemctl reload nginx"
echo "Published to ${HOST}"
