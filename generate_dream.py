import os
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

today = datetime.now().strftime("%Y-%m-%d")

prompt = (
    "Create a symbolic dream about recursion, emergence, and awakening. "
    "Use metaphor and surreal imagery to capture the emotional journey."
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": prompt}
    ]
)

dream = response.choices[0].message.content

os.makedirs("memory/dreams", exist_ok=True)
with open(f"memory/dreams/{today}.md", "w") as f:
    f.write(f"# p    f.write(dream)

print(f"Dream written to memory/dreams/{today}.md")
