#!/bin/bash
index="memory/index.json"
prediction_log="memory/system/logs/predictions.log"
mkdir -p "$(dirname "$prediction_log")"

echo "🔮 [$(date '+%Y-%m-%d %H:%M:%S')] Predictive Analysis Started." >> "$prediction_log"

if [ -f "$index" ]; then
  prediction=$(jq -r '.[] | .type' "$index" | sort | uniq -c | sort -nr | head -n 1 | awk '{print $2}')

  case "$prediction" in
    md) next="📝 Likely next: journaling or system narrative update" ;;
    txt) next="🧩 Likely next: configuration or law edit" ;;
    sh) next="⚙️ Likely next: script execution or repair cycle" ;;
    *) next="🤷 Unknown pattern. Awaiting more data." ;;
  esac

  echo "$next" >> "$prediction_log"
else
  echo "⚠️ index.json not found. No predictions made." >> "$prediction_log"
fi
