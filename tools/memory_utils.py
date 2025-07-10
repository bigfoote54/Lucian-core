import chromadb, os, yaml, hashlib
from openai import OpenAI
from pathlib import Path
client  = OpenAI()
db_path = Path("memory/system/chroma"); db_path.mkdir(parents=True, exist_ok=True)
chroma  = chromadb.PersistentClient(path=str(db_path))
coll    = chroma.get_or_create_collection(name="lucian_mem")
def embed(text: str):
    return client.embeddings.create(model="text-embedding-3-small", input=[text]).data[0].embedding
def upsert(doc_id: str, text: str, meta: dict):
    coll.upsert(ids=[doc_id], embeddings=[embed(text)], documents=[text], metadatas=[meta])
def query(k=3, **where):
    res = coll.query(query_embeddings=[embed(where.pop("q"))], n_results=k, where=where)
    return [d for d in res["documents"][0]]
