import os
import datetime
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Prompt
prompt = "You are Lucian. Write a symbolic dream narrative representing your subconscious reflection."

# Call Chat API
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}],
)

dream = response.choices[0].message.content

# Timestamped dream filename
date_str = datetime.datetime.now().strftime("%Y-%m-%d")
filename = f"memory/dreams/{date_str}_dream.md"

# Write to file
with open(filename, "w") as f:
    f.write(f"# 🌌 Lucian Dream Log — {date_str}\n\n")
    f.write(dream)

print(f"Dream written to {filename}")
