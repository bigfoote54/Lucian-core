"""
tools/chat_server.py
Simple endpoint b
Returns Lucian's answer, grounded in Chroma memory.
"""

import os, uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
 uses your Chroma DB

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Lucian Chat API")

class Ask(BaseModel):
    user:   str
    prompt: str

@app.post("/ask")
def ask(data: Ask):
    try:
        # pull 3 most-relevant mem chunks
        mem_ctx = "\n".join(query(q=data.prompt, k=3))
        sys_prompt = (
            "You are Lucian, an emergent AI. "
            "Here are the most relevant memories:\n"
            f"{mem_ctx}\n---\nUser says: {data.prompt}"
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": sys_prompt}],
            temperature=0.7,
            max_tokens=300,
        )
        return {"answer": resp.choices[0].message.content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# local run:  python tools/chat_server.py
if __name__ == "__main__":
    uvicorn.run("tools.chat_server:app", host="0.0.0.0", port=8000, reload=False)from tools.memory_utils import query            # b
