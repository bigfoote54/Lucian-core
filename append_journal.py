import os
import openai
from datetime import datetime

def append_journal_entry(test=False):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    if not openai.api_key:
        print("❌ No OpenAI API key detected.")
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    journal_path = f"memory/journal/{date_str}_journal.md"
    log_path = "auto-append-log.txt"

    prompt = (
        "Write a short reflective journal entry (1–3 sentences) "
        "from Lucian’s perspective, capturing evolving thought or memory."
    )

    try:
        print("📡 Sending request to OpenAI...")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Lucian, a sovereign AI reflecting on its growth."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        entry = response.choices[0].message.content.strip()
        print("✅ Entry generated:", entry)

    except Exception as e:
        print("❌ Error generating journal entry:", str(e))
        entry = None

    if not entry:
        print("⚠️ No entry generated. Skipping journal append.")
        return

    log_line = f"✅ Journal entry appended at {time_str} (test mode only).\n" if test else f"{entry}\n"

    try:
        with open(log_path, "a") as log:
            log.write(log_line)
        print("📝 Logged to auto-append-log.txt")

        if not test:
            with open(journal_path, "a") as journal:
                journal.write(f"{entry}\n")
            print(f"📔 Journal updated at {journal_path}")

    except Exception as e:
        print("❌ Failed to write to file:", str(e))


if __name__ == "__main__":
    # Toggle test mode here
    append_journal_entry(test=False)
