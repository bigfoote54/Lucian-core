#!/usr/bin/env python3
"""
tools/memory_utils.py
────────────────────────────────────────────────────────────────────────────
Small helper around Chroma-DB + OpenAI embeddings that Lucian-core uses
as its long-term associative memory.

Public API
──────────
embed(text: str) -> list[float]
    Return the embedding vector for *text*.

upsert(doc_id: str, text: str, meta: dict) -> None
    Add / update a document + embedding + metadata in the collection.

query(*, q: str, k: int = 3, **where) -> list[str]
    Retrieve the *k* most similar documents whose metadata match **where.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

# ─── OpenAI client (lazy) ──────────────────────────────────────────────────
load_dotenv()  # ensures OPENAI_API_KEY is in the env even if workflow sets only .env

_openai_client = None  # will be initialised on first use


def _client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        _openai_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    return _openai_client


# ─── Chroma-DB collection setup ────────────────────────────────────────────
try:
    import chromadb
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "❌ chromadb is not installed. "
        "Add `chromadb` to your workflow's pip-install step or "
        "switch to the vector store of your choice."
    ) from exc

CHROMA_PATH = Path("memory/system/chroma")
CHROMA_PATH.mkdir(parents=True, exist_ok=True)

_client_chroma = chromadb.PersistentClient(path=str(CHROMA_PATH))
_collection = _client_chroma.get_or_create_collection(name="lucian_mem")

# ─── Core helpers ──────────────────────────────────────────────────────────
_EMBED_MODEL = "text-embedding-3-small"


def embed(text: str) -> List[float]:
    """Return the embedding vector for *text*."""
    return _client().embeddings.create(model=_EMBED_MODEL, input=[text]).data[0].embedding


def upsert(doc_id: str, text: str, meta: Dict[str, Any] | None = None) -> None:
    """
    Insert or update a document.

    Parameters
    ----------
    doc_id : str
        Stable identifier (e.g. md5 hash of content).
    text : str
        Full text of the document.
    meta : dict, optional
        Arbitrary metadata (e.g. {"kind": "dream", "date": "2025-07-10"}).
    """
    _collection.upsert(
        ids=[doc_id],
        documents=[text],
        metadatas=[meta or {}],
        embeddings=[embed(text)],
    )


def query(*, q: str, k: int = 3, **where) -> List[str]:
    """
    Semantic search.

    Parameters
    ----------
    q : str
        Natural-language query.
    k : int, default 3
        Number of results.
    **where
        Exact-match filters on metadata, e.g. kind="dream".

    Returns
    -------
    list[str]
        The *documents* (text) of the top-k matches, ordered by similarity.
    """
    resp = _collection.query(
        query_embeddings=[embed(q)],
        n_results=k,
        where=where or None,
    )
    return resp["documents"][0]
