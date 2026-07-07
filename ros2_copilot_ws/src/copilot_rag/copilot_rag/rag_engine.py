"""The RAG engine: retrieve -> build prompt -> call Claude -> answer + sources.

This is pure Python with no ROS2 dependency, so you can test it standalone
(`python3 -m copilot_rag.ask "..."`) before wiring it into a ROS2 service.
"""
from typing import List, Tuple

import anthropic

from . import config
from .store import VectorStore

# Grounding is the whole point of RAG: answer ONLY from retrieved context, cite
# it, and admit ignorance instead of hallucinating.
SYSTEM_PROMPT = (
    "You are a ROS2 knowledge assistant for a robot copilot. "
    "Answer the user's question using ONLY the provided context blocks. "
    "If the answer is not contained in the context, say you don't know rather "
    "than guessing. Cite the context blocks you use inline with their number, "
    "e.g. [1] or [2]. Respond in the same language as the user's question."
)


class RagEngine:
    def __init__(self, store: VectorStore,
                 model: str = config.DEFAULT_MODEL,
                 top_k: int = config.DEFAULT_TOP_K) -> None:
        self.store = store
        self.model = model
        self.top_k = top_k
        self.client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY

    def answer(self, question: str) -> Tuple[str, List[str]]:
        """Return (answer_text, source_list)."""
        hits = self.store.query(question, self.top_k)
        if not hits:
            return ("No relevant documents found in the knowledge base. "
                    "Did you ingest documents first?", [])

        context = self._format_context(hits)
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            }],
        )
        answer = next(
            (b.text for b in resp.content if b.type == "text"), "").strip()

        # Report the documents we grounded on (dedup, retrieval order).
        sources: List[str] = []
        for h in hits:
            if h["source"] not in sources:
                sources.append(h["source"])
        return answer, sources

    @staticmethod
    def _format_context(hits: List[dict]) -> str:
        blocks = []
        for i, h in enumerate(hits, start=1):
            blocks.append(f"[{i}] (source: {h['source']})\n{h['text']}")
        return "\n\n".join(blocks)
