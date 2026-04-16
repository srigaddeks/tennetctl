#!/bin/sh
# Replace build-time placeholders with runtime environment variables.
set -eu

NEXT_DIR=/app/apps/web/.next

if [ ! -d "$NEXT_DIR" ]; then
  echo "Missing Next build directory: $NEXT_DIR" >&2
  exit 1
fi

find "$NEXT_DIR" -type f \( -name "*.js" -o -name "*.json" \) | while read -r file; do
  sed -i \
    -e "s|__NEXT_PUBLIC_API_URL__|${NEXT_PUBLIC_API_URL:-}|g" \
    -e "s|__NEXT_PUBLIC_SITE_URL__|${NEXT_PUBLIC_SITE_URL:-}|g" \
    -e "s|__NEXT_PUBLIC_APP_ENV__|${NEXT_PUBLIC_APP_ENV:-production}|g" \
    -e "s|__NEXT_PUBLIC_OAUTH_ENABLED__|${NEXT_PUBLIC_OAUTH_ENABLED:-false}|g" \
    "$file"
done

if [ -f "$NEXT_DIR/routes-manifest.json" ]; then
  sed -i \
    -e "s|script-src 'self'|script-src 'self' 'unsafe-inline'|g" \
    "$NEXT_DIR/routes-manifest.json"
fi
