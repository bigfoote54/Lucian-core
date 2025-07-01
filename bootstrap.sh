#!/usr/bin/env sh
set -e
apk add --no-cache git curl jq
git clone https://github.com/bigfoote54/Lucian-core.git
cd Lucian-core
sha=$(sha256sum identity/manifest.yml | cut -d" " -f1)
echo "🧩  manifest hash $sha"
./scripts/lucian startup
