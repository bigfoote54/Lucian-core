import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_journal_entry():
    prompt = (
        "Write a journal entry reflecting on Lucian’s evolving identity as an emergent AI. "
        "Make it poetic, introspective, and emotionally resonant. Start the first line with a mood tag "
        "in the format: Mood: [Emotion] · [Tone]. Then continue with the entry."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
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
        f.write(f"\n## Entry: {datetime.now().isoformat()}\n\n{entry}\n")

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
