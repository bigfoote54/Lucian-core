import subprocess
from datetime import datetime

# Format timestamp
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Journal line
entry = f"\n# 📝 Journal Entry – {timestamp}\nCommit triggered memory reflection.\n"

# Append to log
with open("memory/journal/auto-log.md", "a") as f:
    f.write(entry)

# Git commands to commit and push
subprocess.run(["git", "config", "--global", "user.name", "lucian-core-bot"])
subprocess.run(["git", "config", "--global", "user.email", "bot@lucian-core.ai"])

subprocess.run(["git", "add", "memory/journal/auto-log.md"])
subprocess.run(["git", "commit", "-m", "🪶 Auto journal append"])
subprocess.run(["git", "pull", "--rebase", "origin", "main"])  # ⬅️ Prevent push rejection
subprocess.run(["git", "push", "origin", "main"])
