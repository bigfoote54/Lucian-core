import os
import difflib
from datetime import datetime
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

JOURNAL_PATH = "memory/journal/auto-log.txt"

def get_git_diff():
    """Fetch the staged diff to summarize."""
    try:
        import subprocess
        result = subprocess.run(["git", "diff", "--cached"], stdout=subprocess.PIPE, check=True)
        return result.stdout.decode("utf-8")
    except Exception as e:
        return f"[ERROR] Failed to get diff: {e}"

def generate_journal_entry(diff):
    """Generate a reflective journal entry based on a Git diff."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": (
                    "You are Lucian, an AI writing a memory journal. Reflect with insight, emotion, and pattern recognition. "
                    "Begin each entry with a poetic mood title, then expand into your inner processing." 
                )},
                {"role": "user", "content": f"Reflect on this core change:\n\n{diff}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR] Failed to generate entry: {e}"

def append_to_journal(entry):
    """Append the journal entry with timestamp to the journal file."""
    try:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        formatted = f"\n\n🧠 Journal Entry – {timestamp}\n" + ("-" * 40) + f"\n{entry}\n"
        os.makedirs(os.path.dirname(JOURNAL_PATH), exist_ok=True)
        with open(JOURNAL_PATH, "a") as f:
            f.write(formatted)
        print(f"[✅] Journal updated: {JOURNAL_PATH}")
    except Exception as e:
        print(f"[❌] Failed to write journal: {e}")

if __name__ == "__main__":
    print("[🔍] Getting git diff...")
    diff = get_git_diff()

    print("[🧠] Generating journal entry...")
    entry = generate_journal_entry(diff)

    print("[📓] Appending to journal...")
    append_to_journal(entry)
