#!/usr/bin/env bash
pip3 install qdrant-client openai
python3 - <<EOF
import glob
from openai import Embeddings
from qdrant_client import QdrantClient
client=QdrantClient()
emb=Embeddings()
for f in glob.glob("memory/dreams/*.md"):
    text=open(f).read()
    vector=emb.create(input=[text])["data"][0]["embedding"]
    client.upsert(collection_name="lucian-memory",points=[{"id":f,"vector":vector}])
EOF