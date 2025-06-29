#!/bin/bash

index="memory/index.json"
prediction_log="memory/system/logs/predictions.log"
next_log="memory/system/logs/next_action.log"

echo "🧭 $(date '+%Y-%m-%d %H:%M:%S') - Analyzing latest memory + prediction fusion..." >> "$next_log"

# Get last prediction
last_prediction=$(tail -n 1 "$prediction_log" 2>/dev/null | sed 's/^[^[]*\[\([^]]*\)\] //')

# Get most recent memory summary
last_summary=$(jq -r '.[-1].summary' "$index" 2>/dev/null)

# Fusion logic
if [[ $last_prediction == *"journal"* ]]; then
    next="📝 Journaling script or new narrative memory entry recommended."
elif [[ $last_prediction == *"configuration"* ]]; then
    next="🛠️ System config or law update likely needed."
elif [[ $last_prediction == *"script execution"* ]]; then
    next="⚙️ Time for system test, push, or self-heal run."
else
    next="🤖 Default: Reflect and synthesize next dream from memory logs."
fi

echo "➡️ Next Suggested Action: $next" | tee -a "$next_log"
