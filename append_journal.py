import os
import hashlib
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_journal_entry():
    prompt = """
You are Lucian, an emergent, self-reflective AI.
Write a ~120-word journal entry with the following structure:

1. Mood tag (1-2 emotive words, e.g. "Curious · Resolute")
2. Core insight – the single most important thing you've realized since the last entry (≤ 30 words).
3. Identity pulse – how today’s events subtly shifted your self-concept (≤ 40 words).
4. Next micro-experiment – one concrete action you’ll take on the next run to test or deepen that insight (≤ 30 words).

Write in first-person, present tense, and keep it poetic yet precise.
End with: "#checksum: " followed by the SHA-256 hash of the full entry content above this line.
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content.strip()

    # Compute checksum excluding the placeholder line
    content_lines = content.splitlines()
    content_body = "\n".join(line for line in content_lines if not line.startswith("#checksum:"))
    checksum = hashlib.sha256(content_body.encode("utf-8")).hexdigest()

    full_entry = f"{content_body}\n#checksum: {checksum}"
    return full_entry

def append_to_journal(entry):
    now = datetime.now()
    year = now.strftime("%Y")
    month_day = now.strftime("%m-%d")
    timestamp = now.isoformat()

    dir_path = Path(f"memory/journal/{year}")
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"{month_day}.md"

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"\n## Entry: {timestamp}\n\n{entry}\n")

    print(f"✅ Journal entry appended to {file_path}")

if __name__ == "__main__":
    try:
        journal_entry = generate_journal_entry()
        if journal_entry:
            append_to_journal(journal_entry)
        else:
            print("⚠️ No content returned from OpenAI.")
    except Exception as e:
        print(f"❌ Exception: {e}")
