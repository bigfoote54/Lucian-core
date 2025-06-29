#!/bin/bash

index="memory/index.json"
dream_log="memory/dreams/dream_$(date '+%Y-%m-%d_%H%M').txt"

echo "pecho "Synthesizing symbolic memory dream..." >> "$dream_log"

jq -r '.[] | "\(.timestamp) | \(.summary)"' "$index" | shuf | head -n 5 | while read -r line; do
    ts=$(echo "$line" | cut -d'|' -f1)
    summary=$(echo "$line" | cut -d'|' -f2-)
    echo "- [$ts] $(echo "$summary" | sed 's/^ *//g')" >> "$dream_log"
done
echo -e "/n
