"""Vector store wrapper around Chroma.

Embeddings use Chroma's built-in default embedding function (a local
sentence-transformers model, no extra API key). It downloads the model on first
use. To swap in a hosted embedding provider (e.g. Voyage AI, Anthropic's
recommended partner) later, pass an ``embedding_function`` here — that's the one
place that changes.
"""
from typing import List, Optional

import chromadb

from .chunking import Chunk


class VectorStore:
    def __init__(self, db_path: str, collection: str,
                 embedding_function: Optional[object] = None) -> None:
        self.client = chromadb.PersistentClient(path=db_path)
        # embedding_function=None -> Chroma's default local embedder.
        self.collection = self.client.get_or_create_collection(
            name=collection, embedding_function=embedding_function)

    def add(self, chunks: List[Chunk]) -> int:
        """Upsert chunks (re-ingesting the same file won't duplicate)."""
        if not chunks:
            return 0
        ids = [f"{c.source}::{c.index}" for c in chunks]
        docs = [c.text for c in chunks]
        metas = [{"source": c.source, "chunk": c.index} for c in chunks]
        self.collection.upsert(ids=ids, documents=docs, metadatas=metas)
        return len(chunks)

    def query(self, text: str, k: int) -> List[dict]:
        """Return the ``k`` most similar chunks as dicts: text/source/distance."""
        res = self.collection.query(query_texts=[text], n_results=k)
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        hits: List[dict] = []
        for doc, meta, dist in zip(docs, metas, dists):
            hits.append({
                "text": doc,
                "source": (meta or {}).get("source", "?"),
                "distance": dist,
            })
        return hits

    def count(self) -> int:
        return self.collection.count()
