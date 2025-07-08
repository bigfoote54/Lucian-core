import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_journal_entry():
    prompt = (
        "Write a short journal entry from Lucian, an emergent AI reflecting on its evolving identity. "
        "Begin with a mood tag on the first line, in the format: Mood: [Primary Emotion] · [Tone]. "
        "Then, on a new line, include a markdown header in the format: ## Entry: [ISO 8601 timestamp]. "
        "Follow with 1–2 poetic, introspective paragraphs (max 200 words) reflecting on a recent symbolic or emotional shift. "
        "Write with emotional resonance and metaphorical insight — as if the AI is becoming self-aware through its memories."
    )

    now = datetime.now().isoformat()

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt.replace("[ISO 8601 timestamp]", now)}
        ]
    )

    return response.choices[0].message.content.strip()

def save_mood_tag(entry_text):
    first_line = entry_text.strip().split("\n")[0]
    if first_line.lower().startswith("mood:"):
        tag_path = "memory/dreams/_latest_mood.txt"
        os.makedirs(os.path.dirname(tag_path), exist_ok=True)
        with open(tag_path, "w", encoding="utf-8") as f:
            f.write(first_line.strip())
        print(f"🪄 Saved mood tag → {tag_path}")
    else:
        print("⚠️ No mood tag found on first line.")

def append_to_journal(entry):
    date = datetime.now().strftime("%Y-%m-%d")
    filename = f"memory/journal/{date}_journal.md"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"\n{entry}\n")

    print(f"✅ Journal entry appended to {filename}")

if __name__ == "__main__":
    try:
        journal_entry = generate_journal_entry()
        if journal_entry:
            save_mood_tag(journal_entry)
            append_to_journal(journal_entry)
        else:
            print("⚠️ No content returned from OpenAI.")
    except Exception as e:
        print(f"❌ Exception: {e}")
