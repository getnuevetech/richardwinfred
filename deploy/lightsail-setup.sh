#!/usr/bin/env bash
# One-time setup for an Ubuntu Lightsail instance (OS-only blueprint).
# Run on the server, from a copy of this repo:
#   sudo ./deploy/lightsail-setup.sh richardwinfred.com info@richardwinfred.com
# Include www only after that DNS record exists:
#   sudo WWW=1 ./deploy/lightsail-setup.sh richardwinfred.com info@richardwinfred.com
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo ./deploy/lightsail-setup.sh example.com you@example.com" >&2
  exit 1
fi

DOMAIN="${1:-}"
EMAIL="${2:-}"
if [[ ! "$DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]] || [[ ! "$EMAIL" =~ ^[^[:space:]@]+@[^[:space:]@]+$ ]]; then
  echo "Usage: sudo ./deploy/lightsail-setup.sh example.com you@example.com" >&2
  exit 1
fi

SRC="$(cd "$(dirname "$0")/.." && pwd)"
WEB_ROOT="/var/www/richardwinfred"
NAMES="$DOMAIN"
CERT_ARGS=(-d "$DOMAIN")
if [[ "${WWW:-}" == "1" ]]; then
  NAMES="$DOMAIN www.$DOMAIN"
  CERT_ARGS+=(-d "www.$DOMAIN")
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx rsync

install -d -m 755 "$WEB_ROOT"
rsync -a --delete \
  --exclude '.git/' \
  --exclude 'deploy/' \
  --exclude 'README.md' \
  --exclude '.gitignore' \
  --exclude '.DS_Store' \
  "$SRC"/ "$WEB_ROOT"/
chown -R www-data:www-data "$WEB_ROOT"

install -d -m 755 /etc/nginx/snippets
install -m 644 "$SRC/deploy/nginx/security-headers.conf" /etc/nginx/snippets/richardwinfred-headers.conf
sed "s/__SERVER_NAMES__/${NAMES}/g" "$SRC/deploy/nginx/richardwinfred.conf" > /etc/nginx/sites-available/richardwinfred
ln -sfn /etc/nginx/sites-available/richardwinfred /etc/nginx/sites-enabled/richardwinfred
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl enable nginx
systemctl reload nginx

echo "HTTP is up. Requesting a certificate for: ${NAMES}"
echo "DNS A records must already point at this instance, and Lightsail networking must allow TCP 80 and 443."
certbot --nginx "${CERT_ARGS[@]}" \
  --non-interactive --agree-tos --email "$EMAIL" --redirect

echo "Site is available at https://${DOMAIN}/"
