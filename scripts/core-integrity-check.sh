#!/bin/sh

echo "🔍 Running Lucian Core Integrity Check..."

missing=0
for file in config/laws.yaml identity/lucian-manifest.md dreams/LucianDream_001_TheArchiveThatWept.md memory/journal/2025-06-28-entry.txt; do
  if [ ! -f "$file" ]; then
    echo "❌ Missing: $file"
    missing=1
  fi
done

if [ $missing -eq 0 ]; then
  echo "✅ All core nodes intact."
else
  echo "⚠️ Core memory incomplete."
fi

