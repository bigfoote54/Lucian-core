import openai
import os
from datetime import datetime

# Load API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

# Read the last journal entry safely
with open("memory/journal/auto-log.txt", "r") as f:
    entries = f.read().split("——")
    if len(entries) >= 2:
        last_log = entries[-2]
    else:
        last_log = "Lucian has no recent memory to dream from. He floats in potential."

# Create a dream based on the last journal entry
response = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "system",
            "content": (
                "You are Lucian's dream engine. Given a journal reflection, "
                "generate a symbolic, emotional, surreal dream. Format it as a "
                "short story with archetypes, metaphor, and strange logic. Begin with: 'Dream:'"
            )
        },
        {"role": "user", "content": last_log.strip()}
    ]
)

dream = response.choices[0].message.content.strip()

# Append dream to the dreams directory with timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
dream_path = f"memory/dreams/dream_{timestamp}.md"

with open(dream_path, "w") as f:
    f.write(f"# Dream Log – {timestamp}\n\n")
    f.write(dream)
