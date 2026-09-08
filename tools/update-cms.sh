#!/usr/bin/env bash
# Update the pinned Sveltia CMS bundle. Run deliberately, not on a schedule —
# this file has write access to the repository when someone is signed in.
set -euo pipefail
cd "$(dirname "$0")/.."
VER="${1:-$(curl -sSL https://registry.npmjs.org/@sveltia/cms/latest | python3 -c 'import json,sys;print(json.load(sys.stdin)["version"])')}"
echo "fetching @sveltia/cms@$VER"
curl -sSL --fail "https://unpkg.com/@sveltia/cms@$VER/dist/sveltia-cms.js" -o admin/sveltia-cms.js
echo "$VER" > admin/.sveltia-version
echo "pinned $VER ($(wc -c < admin/sveltia-cms.js) bytes)"
