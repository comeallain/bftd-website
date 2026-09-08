#!/usr/bin/env bash
# Re-download the self-hosted webfonts from Google Fonts and regenerate
# fonts/fonts.css. Run this only when the set of typefaces changes.
#
# The fonts are served from our own domain deliberately: loading them from
# Google's CDN transmits every visitor's IP address to Google before any
# interaction, which we do not want to be doing from a Dublin-based company.
set -euo pipefail
cd "$(dirname "$0")/.."

UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
URL='https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@400&family=DM+Sans:wght@400;500;700&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap'

mkdir -p fonts
curl -sS -A "$UA" "$URL" -o /tmp/gf.css
python3 tools/build_fonts.py /tmp/gf.css
rm -f /tmp/gf.css
echo "fonts regenerated"
