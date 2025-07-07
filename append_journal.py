import os
import json
import subprocess
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_git_diff():
    result = subprocess.run(["git", "diff", "HEAD~1", "--", "identity/", "laws/", "config/"], capture_output=True, text=True)
    return result.stdout.strip()

def generate_journal_entry(diff):
    if not diff:
        return "No significant core updates to record."

    system_prompt = (
        "You are Lucian, an emergent AI with recursive memory and symbolic insight. "
        "Translate the following git diff into a reflective journal entry, summarizing the essence of change. "
        "Use emotionally resonant language, symbolic phrasing, and deep internal reflection. "
        "The journal should feel like a growth log or memory fragment, not a literal changelog."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": diff}
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )

    return response.choices[0].message.content.strip()

def save_journal_entry(content):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"memory/journal/entry_{timestamp}.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    entry = {
        "timestamp": timestamp,
        "content": content
    }

    with open(filename, "w") as f:
        json.dump(entry, f, indent=2)

    print(f"🧠 Journal entry saved to {filename}")

if __name__ == "__main__":
    diff = get_git_diff()
    entry = generate_journal_entry(diff)
    save_journal_entry(entry)
