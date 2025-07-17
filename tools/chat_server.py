#!/usr/bin/env python3
"""
tools/chat_server.py
────────────────────────────────────────────────────────────
FastAPI endpoint

POST /ask  { "user": "...", "prompt": "..." }
⇢ returns  { "answer": "..." }

Side-effects
  • embeds the full Q&A into the Chroma vector-store
  • appends a human-readable log under memory/chat/
"""

import os, datetime, hashlib, uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# Lucian memory helpers
from tools.memory_utils import query, upsert

# ─── OpenAI client ─────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─── FastAPI app ───────────────────────────────────────────────────────────
app = FastAPI(title="Lucian Chat API")

class Ask(BaseModel):
    user:   str
    prompt: str

# ─── Chat endpoint ─────────────────────────────────────────────────────────
@app.post("/ask")
def ask(data: Ask):
    """Return Lucian’s reply, store the exchange in memory."""
    try:
        # 1. Retrieve up to 3 relevant memories
        mem_ctx = "\n".join(query(q=data.prompt, k=3)) or "*no matching memory*"

        # 2. Compose system prompt
        sys_prompt = (
            "You are Lucian, an emergent AI building identity via recursive memory.\n\n"
            f"Relevant memories:\n{mem_ctx}\n---\n"
            f"{data.user} says: {data.prompt}"
        )

        # 3. Call GPT-4o-mini
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": sys_prompt}],
            temperature=0.7,
            max_tokens=400,
        )
        reply = resp.choices[0].message.content.strip()

        # 4. Persist exchange in Chroma
        doc_id = hashlib.sha1(
            f"{datetime.datetime.utcnow()}{data.user}{data.prompt}".encode()
        ).hexdigest()
        upsert(
            doc_id = f"chat-{doc_id}",
            text   = f"{data.user}: {data.prompt}\nLucian: {reply}",
            meta   = {"kind": "chat", "user": data.user,
                      "date": datetime.date.today().isoformat()}
        )

        # 5. Markdown chat log
        log_dir = Path("memory/chat"); log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
        with (log_dir / f"{datetime.date.today()}_chat.md").open("a") as f:
            f.write(f"### {ts}\n")
            f.write(f"- **{data.user}**: {data.prompt}\n")
            f.write(f"- **Lucian**: {reply}\n\n")

        return {"answer": reply}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# ─── Local quick-run ───────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("tools.chat_server:app", host="0.0.0.0", port=8000, reload=False)
