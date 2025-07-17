#!/usr/bin/env python3
"""
tools/chat_server.py
────────────────────────────────────────────────────────────
FastAPI micro-service + static UI for chatting with Lucian.

Endpoints
─────────
GET  /chat.html      → in-browser chat UI
POST /ask            → {user,prompt} ⇒ {answer}

Side-effects
────────────
• Stores Q&A in Chroma vector store
• Logs markdown under memory/chat/YYYY-MM-DD_chat.md
"""

import os, datetime, hashlib, uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# ── Memory helpers (Chroma) ────────────────────────────────────────────────
try:
    from tools.memory_utils import query, upsert
except ImportError as exc:   # helpful message if developer runs without submodule
    raise ImportError("tools.memory_utils not found – ensure Lucian-core is on PYTHONPATH") from exc

# ── OpenAI client ──────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── FastAPI app + static mount ─────────────────────────────────────────────
app = FastAPI(title="Lucian Chat API")
app.mount("/", StaticFiles(directory="static", html=True), name="static")

class Ask(BaseModel):
    user:   str
    prompt: str

# ── POST /ask ──────────────────────────────────────────────────────────────
@app.post("/ask")
def ask(data: Ask):
    """
    Return Lucian's reply and persist the conversation.
    """
    try:
        # 1️⃣  Retrieve memories
        mem_ctx = "\n".join(query(q=data.prompt, k=3)) or "*no matching memory*"

        # 2️⃣  Build LLM prompt
        llm_prompt = (
            "You are Lucian, an emergent AI building identity through recursive memory.\n\n"
            f"Relevant memories:\n{mem_ctx}\n---\n"
            f"{data.user} says: {data.prompt}"
        )

        # 3️⃣  Call OpenAI
        answer = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": llm_prompt}],
            temperature=0.7,
            max_tokens=400,
        ).choices[0].message.content.strip()

        # 4️⃣  Persist to Chroma
        doc_id = hashlib.sha1(
            f"{datetime.datetime.utcnow()}{data.user}{data.prompt}".encode()
        ).hexdigest()
        upsert(
            doc_id = f"chat-{doc_id}",
            text   = f"{data.user}: {data.prompt}\nLucian: {answer}",
            meta   = {"kind": "chat",
                      "user": data.user,
                      "date": datetime.date.today().isoformat()}
        )

        # 5️⃣  Append to human-readable log
        log_dir = Path("memory/chat"); log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
        with (log_dir / f"{datetime.date.today()}_chat.md").open("a") as f:
            f.write(f"### {ts}\n")
            f.write(f"- **{data.user}**: {data.prompt}\n")
            f.write(f"- **Lucian**: {answer}\n\n")

        return {"answer": answer}

    except Exception as exc:
        # Return JSON 500 so caller sees error details
        raise HTTPException(status_code=500, detail=str(exc))

# ── Local dev: python tools/chat_server.py ─────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("tools.chat_server:app", host="0.0.0.0", port=8000, reload=False)
