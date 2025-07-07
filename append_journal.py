import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_journal_entry():
    prompt = (
        "Write a short journal entry reflecting on the recent symbolic evolution "
        "of Lucian’s identity as an emergent AI. Keep it poetic, introspective, and under 150 words."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()

def append_to_journal(entry):
    date = datetime.now().strftime("%Y-%m-%d")
    filename = f"memory/journal/{date}_journal.md"

    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"\n## Entry: {datetime.now().isoformat()}\n\n{entry}\n")

    print(f"✅ Journal entry appended to {filename}")

if __name__ == "__main__":
    try:
        journal_entry = generate_journal_entry()
        if journal_entry:
            append_to_journal(journal_entry)
        else:
            print("⚠️ No content returned from OpenAI.")
    except Exception as e:
        print(f"❌ Exception: {e}")
