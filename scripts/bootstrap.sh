#!/bin/sh

echo "🧠 Initializing Lucian core directories..."
mkdir -p config identity memory/journal dreams
touch config/laws.yaml config/system-flags.json
touch identity/lucian-manifest.md identity/version.md
touch dreams/LucianDream_001_TheArchiveThatWept.md
touch memory/journal/2025-06-28-entry.txt
echo "✅ Core structure rebuilt."
