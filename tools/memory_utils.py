# tools/memory_utils.py
"""
Light-weight memory wrapper for Lucian-core.
▪ If ChromaDB is present  ➜ use persistent vector search.
▪ If ChromaDB is missing  ➜ fall back to harmless stubs so the rest
  of the pipeline (dream generation, reflection, etc.) can still run.
"""

from pathlib import Path
import hashlib, os
from openai import OpenAI

client = OpenAI()          # uses OPENAI_API_KEY from environment

# ── Attempt to import ChromaDB ──────────────────────────────────────
try:
    import chromadb                      # heavy optional dependency
except ModuleNotFoundError:
    # ────────────────────────────────
    # Fallback -- no Chroma available
    # ────────────────────────────────
    def embed(text: str) -> list[float]:
        """Return a deterministic dummy embedding (stable hash)."""
        return [hashlib.md5(text.encode()).hexdigest().__hash__() % 1_000 / 1_000]

    def upsert(doc_id: str, text: str, meta: dict):
        """No-op when Chroma is absent."""
        pass

    def query(k: int = 3, **where) -> list[str]:
        """Return empty list (no memory context)."""
        return []

else:
    # ────────────────────────────────
    # Full Chroma implementation
    # ────────────────────────────────
    db_path = Path("memory/system/chroma")
    db_path.mkdir(parents=True, exist_ok=True)

    chroma  = chromadb.PersistentClient(path=str(db_path))
    coll    = chroma.get_or_create_collection(name="lucian_mem")

    def embed(text: str) -> list[float]:
        """Vector embed with OpenAI `text-embedding-3-small`."""
        return client.embeddings.create(
            model="text-embedding-3-small",
            input=[text]
        ).data[0].embedding

    def upsert(doc_id: str, text: str, meta: dict):
        """Add / update a document in Chroma."""
        coll.upsert(
            ids=[doc_id],
            embeddings=[embed(text)],
            documents=[text],
            metadatas=[meta]
        )

    def query(k: int = 3, **where) -> list[str]:
        """
        Retrieve the `k` most similar documents.
        Supply the search text via `q="..."`; any additional keyword
        args become a Chroma `where` filter (e.g. kind="dreams").
        """
        q_text = where.pop("q")
        res = coll.query(
            query_embeddings=[embed(q_text)],
            n_results=k,
            where=where
        )
        return [d for d in res["documents"][0]]
