"""Text chunking for the RAG pipeline.

Splits a document into overlapping windows small enough to embed and retrieve.
Kept dependency-free (no tokenizer) so it's easy to read, test, and reason about.

This is the *simplest* useful chunker: a fixed-size sliding window with overlap.
It can split mid-sentence — that's fine for an MVP. Paragraph- or heading-aware
chunking is a natural improvement to try later (see Phase 5 in the roadmap).
"""
from dataclasses import dataclass
from typing import List


@dataclass
class Chunk:
    text: str
    source: str
    index: int


def chunk_text(text: str, source: str,
               chunk_size: int = 1000, overlap: int = 200) -> List[Chunk]:
    """Return overlapping ~chunk_size-char chunks of ``text``.

    Consecutive chunks share ``overlap`` characters so context isn't lost at a
    boundary. ``chunk_size`` and ``overlap`` are in characters.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    # Normalize trailing whitespace per line; keep structure otherwise.
    text = "\n".join(line.rstrip() for line in text.splitlines())

    step = chunk_size - overlap
    chunks: List[Chunk] = []
    start = 0
    index = 0
    while start < len(text):
        piece = text[start:start + chunk_size].strip()
        if piece:
            chunks.append(Chunk(text=piece, source=source, index=index))
            index += 1
        start += step
    return chunks
