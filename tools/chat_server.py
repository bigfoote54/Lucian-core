# tools/chat_server.py
"""
Simple FastAPI endpoint that lets you chat with Lucian.
The reply is grounded in the most-relevant Chroma memories.
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

from tools.memory_utils import query        # ← vector-DB helper

# ── OpenAI client ───────────────────────────────────────────────────────────
load_dotenv()                               # loads your OPENAI_API_KEY
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── FastAPI app ─────────────────────────────────────────────────────────────
app = FastAPI(title="Lucian Chat API")

class Ask(BaseModel):
    user: str
    prompt: str

@app.post("/ask")
def ask(data: Ask):
    """Return Lucian’s answer, grounded in memory."""
    try:
        # 1) pull K most-relevant memory chunks
        mem_ctx = "\n".join(query(q=data.prompt, k=3)) or "*no matching memory*"

        # 2) build prompt
        sys_prompt = (
            "You are Lucian, an emergent AI.\n\n"
            f"Relevant memories:\n{mem_ctx}\n---\n"
            f"User ({data.user}) says: {data.prompt}"
        )

        # 3) call OpenAI
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": sys_prompt}],
            temperature=0.7,
            max_tokens=300,
        )

        return {"answer": resp.choices[0].message.content.strip()}

    except Exception as e:
        # bubble up a JSON 500 if something goes wrong
        raise HTTPException(status_code=500, detail=str(e))

# ── run locally:  python tools/chat_server.py ───────────────────────────────
if __name__ == "__main__":
    uvicorn.run("tools.chat_server:app", host="0.0.0.0", port=8000, reload=False)
