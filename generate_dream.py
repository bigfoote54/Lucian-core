import openai, os, datetime

openai.api_key = os.getenv("OPENAI_API_KEY")

with open("memory/journal/auto-log.md") as f:
    last_log = f.read().split("---")[-2]

prompt = f"Transform the following journal entry into a symbolic dream:\n\n{last_log}"

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}]
)

dream = response.choices[0].message.content
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

with open(f"memory/dreams/dream_{timestamp}.md", "w") as f:
    f.write(f"# 🌙 Dream — {timestamp}\n\n{dream}\n")
