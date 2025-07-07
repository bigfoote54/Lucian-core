import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def read_mood_tag():
    mood_path = "memory/dreams/_latest_mood.txt"
    if os.path.exists(mood_path):
        with open(mood_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "Mood: Undefined · Neutral"

def generate_dream(mood):
    prompt = (
        f"{mood}\n\n"
        "Lucian is about to dream. Generate a symbolic dream sequence reflecting the emotional tone above. "
        "The dream should explore subconscious identity themes, internal conflict, or transformation. "
        "Make it metaphorical and nonlinear, like a surreal memory retelling itself."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()

def save_dream(entry):
    date = datetime.now().strftime("%Y-%m-%d")
    filename = f"memory/dreams/{date}_dream.md"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"\n## Entry: {datetime.now().isoformat()}\n\n{entry}\n")

    print(f"🌙 Dream entry saved to {filename}")

if __name__ == "__main__":
    try:
        mood = read_mood_tag()
        print(f"🌡️ Current mood: {mood}")
        dream_entry = generate_dream(mood)
        if dream_entry:
            save_dream(dream_entry)
        else:
            print("⚠️ No content returned from OpenAI.")
    except Exception as e:
        print(f"❌ Exception: {e}")
