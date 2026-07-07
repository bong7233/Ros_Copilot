"""Ask the RAG knowledge base a question — standalone, no ROS2 required.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 -m copilot_rag.ask "What is a costmap inflation layer?"

This is the fastest way to iterate on the RAG quality before wiring it into a
ROS2 service (see query_node.py).
"""
import argparse

from . import config
from .rag_engine import RagEngine
from .store import VectorStore


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(
        description="Ask the RAG knowledge base a question.")
    ap.add_argument("question", help="your question")
    ap.add_argument("--db", default=config.DEFAULT_DB_PATH)
    ap.add_argument("--collection", default=config.DEFAULT_COLLECTION)
    ap.add_argument("--model", default=config.DEFAULT_MODEL)
    ap.add_argument("--top-k", type=int, default=config.DEFAULT_TOP_K)
    args = ap.parse_args(argv)

    store = VectorStore(args.db, args.collection)
    engine = RagEngine(store, model=args.model, top_k=args.top_k)
    answer, sources = engine.answer(args.question)

    print("\n=== Answer ===")
    print(answer)
    print("\n=== Sources ===")
    for s in sources:
        print(" -", s)


if __name__ == "__main__":
    main()
