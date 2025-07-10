from pathlib import Path, PurePosixPath
from datetime import datetime
from tools.memory_utils import upsert
for kind in ("dreams","reflection"):
    for p in Path("memory",kind).glob("*.md"):
        txt = p.read_text()
        doc_id = hashlib.md5(txt.encode()).hexdigest()
        meta = {"kind": kind, "date": p.name.split("_")[0]}
        upsert(doc_id, txt, meta)
print("✅ back-filled embeddings")
