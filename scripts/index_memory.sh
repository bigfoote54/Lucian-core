#!/bin/bash
log="memory/index.json"
echo "[" > $log
find memory/ \( -name "*.txt" -o -name "*.md" \) | while read -r file; do
  type=$(echo "$file" | cut -d'/' -f2)
  timestamp=$(date -r "$file" +"%Y-%m-%d %H:%M:%S")
  first_line=$(head -n 1 "$file" | sed 's/"/\\"/g')
  echo "  { \"path\": \"$file\", \"type\": \"$type\", \"timestamp\": \"$timestamp\", \"summary\": \"$first_line\" }," >> $log
done
sed -i '' -e '$ s/},/}/' $log 2>/dev/null || sed -i '$ s/},/}/' $log
echo "]" >> $log
