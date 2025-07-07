import openai, os, datetime

openai.api_key = os.getenv("OPENAI_API_KEY")

commit = os.popen("git log -1 --pretty=%B").read().strip()
date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
prompt = f"Reflect on this core change and write a journal entry:\n\n{commit}"

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}]
)

journal_text = response.choices[0].message.content
entry = f"# p
with open("memory/journal/auto-log.md", "a") as f:
    f.write(entry + "\n---\n")
