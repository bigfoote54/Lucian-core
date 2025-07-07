import os
from datetime import datetime

# 1. Check for OpenAI API key (for future use)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ No API key found in environment.")
else:
    print("✅ API key detected.")

# 2. Define the fallback journal content for test
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
content = f"✅ Journal entry appended at {timestamp} (test mode only).\n"

# 3. Determine file path for today's journal
today = datetime.now().strftime("%Y-%m-%d")
journal_path = f"memory/journal/{today}_journal.md"

try:
    # 4. Ensure the file exists
    if not os.path.exists(journal_path):
        with open(journal_path, "w") as f:
            f.write(f"# Journal for {today}\n\n")

    # 5. Append test content
    with open(journal_path, "a") as f:
        f.write(content)

    print("✅ Successfully appended to journal.")

except Exception as e:
    print(f"❌ Failed to append journal entry: {e}")
