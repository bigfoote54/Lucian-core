#!/usr/bin/env bash
for f in memory/dreams/*.md; do
  if ! grep -q '^tags:' "$f"; then
    snippet=$(sed -n '1,20p' "$f")
    tags=$(openai api chat.completions.create \
      -m gpt-4o \
      -g system \
      -c "You are Lucian AI. Generate 3–5 concise, comma-separated thematic tags for this dream:\n\n$snippet" \
      | jq -r '.choices[0].message.content')
    sed -i "1i tags: [$tags]" "$f"
    git add "$f"
    echo "🔖 Tagged $f → [$tags]"
  fi
done
