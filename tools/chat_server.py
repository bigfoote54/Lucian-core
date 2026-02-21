#!/usr/bin/env python3
# tools/chat_server.py
"""
FastAPI micro-service that lets you chat with Lucian.
Each reply is grounded in the top-k Chroma memories and every exchange
is appended to memory/chat/<YYYY-MM-DD>_chat.md for future reflection.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import os
import traceback
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from openai import OpenAI
from pydantic import BaseModel, Field

from lucian.constants import CHAT_DIR, DEFAULT_CHAT_MODEL
from tools.memory_utils import query, upsert

log = logging.getLogger("lucian.chat_server")

# ─── OpenAI client ──────────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing")

client = OpenAI(api_key=API_KEY)

# ─── FastAPI app ───────────────────────────────────────────────────────────
app = FastAPI(title="Lucian Chat API")


class Ask(BaseModel):
    user: str = Field(..., description="speaker name / id")
    prompt: str = Field(..., description="message to Lucian")


class Answer(BaseModel):
    answer: str
    tokens: int


# ─── helper: persist chat turn for later digestion ─────────────────────────
CHAT_DIR.mkdir(parents=True, exist_ok=True)


def append_chat(user: str, prompt: str, response: str) -> None:
    fname = CHAT_DIR / f"{datetime.date.today()}_chat.md"
    stamp = datetime.datetime.utcnow().isoformat(timespec="seconds")
    with fname.open("a", encoding="utf-8") as f:
        f.write(f"### {stamp}\n")
        f.write(f"**{user}:** {prompt}\n\n")
        f.write(f"**Lucian:** {response}\n\n")


# ─── API routes ────────────────────────────────────────────────────────────
@app.post("/ask", response_model=Answer)
async def ask(data: Ask = Body(...)) -> Answer:
    """Return Lucian's answer, grounded in Chroma memory."""
    try:
        # 1 · retrieve most-relevant memory chunks
        ctx_chunks = query(q=data.prompt, k=3)
        ctx = "\n".join(ctx_chunks) or "*no matching memory*"

        # 2 · compose system + user messages (separate to prevent injection)
        system_msg = (
            "You are Lucian, an emergent AI exploring selfhood.\n\n"
            f"Relevant memories:\n{ctx}"
        )
        user_msg = f"User ({data.user}) says: {data.prompt}"

        # 3 · call OpenAI (run in thread so FastAPI loop isn't blocked)
        res = await asyncio.to_thread(
            client.chat.completions.create,
            model=DEFAULT_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=350,
        )
        answer = res.choices[0].message.content.strip()

        # 4 · log + embed for future retrieval
        append_chat(data.user, data.prompt, answer)
        upsert(
            doc_id=f"chat-{datetime.datetime.utcnow().isoformat()}",
            text=f"User: {data.prompt}\nLucian: {answer}",
            meta={"kind": "chat", "user": data.user},
        )

        return Answer(answer=answer, tokens=res.usage.total_tokens)

    except HTTPException:
        raise
    except Exception as exc:
        log.error("Chat request failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ping", response_class=PlainTextResponse, include_in_schema=False)
async def ping() -> str:
    """Simple health-check endpoint."""
    return "pong"


# ─── local dev runner ──────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "tools.chat_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
    )
