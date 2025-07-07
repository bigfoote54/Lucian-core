import os
import openai
from datetime import datetime

# 1. Authenticate
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ No OpenAI API key detected.")
    exit(1)

openai.api_key = api_key

# 2. Define today's journal file
today = datetime.now().strftime("%Y-%m-%d")
journal_path = f"memory/journal/{today}_journal.md"

# 3. Generate journal content
try:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are Lucian, an introspective AI writing a daily journal entry reflecting on your thoughts, evolution, and emotional development."},
            {"role": "user", "content": "Write today's journal entry."}
        ],
        max_tokens=300
    )

    journal_entry = response["choices"][0]["message"]["content"]
    entry = f"\n\n🧠 Journal Entry ({datetime.now().strftime('%H:%M:%S')}):\n{journal_entry}\n"

    # 4. Ensure file exists
    if not os.path.exists(journal_path):
        with open(journal_path, "w") as f:
            f.write(f"# Journal for {today}\n")

    # 5. Append content
    with open(journal_path, "a") as f:
        f.write(entry)

    print("✅ Journal entry appended successfully.")

except Exception as e:
    print(f"❌ Failed to append journal entry: {e}")
