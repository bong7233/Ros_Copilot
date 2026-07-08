"""A tiny lexical reranker for retrieved chunks.

Vector search is good at semantic similarity but can miss exact-term matches.
A cheap trick that often improves RAG: retrieve a wider net with the vector
store, then reorder by how many of the question's words each chunk contains, and
keep the top few. Dependency-free and unit-testable.

This is deliberately simple — a learned cross-encoder reranker is the next step
(see the Phase 5 eval extensions).
"""
import re
from typing import List


def lexical_score(question: str, text: str) -> float:
    """Fraction of the question's distinct words that appear in ``text``."""
    q = set(re.findall(r"\w+", question.lower()))
    if not q:
        return 0.0
    t = set(re.findall(r"\w+", text.lower()))
    return len(q & t) / len(q)


def rerank(question: str, hits: List[dict]) -> List[dict]:
    """Return hits reordered by lexical overlap with the question (desc)."""
    return sorted(hits, key=lambda h: lexical_score(question, h["text"]),
                  reverse=True)
