"""Ingest documents into the RAG vector store.

Usage (standalone, no ROS2 build needed — run from the package directory):
    python3 -m copilot_rag.ingest data
    python3 -m copilot_rag.ingest data ../../          # also index the workspace

Or after `colcon build`:
    ros2 run copilot_rag ingest data
"""
import argparse
import os
from typing import Iterator, List

from . import config
from .chunking import chunk_text
from .store import VectorStore

TEXT_EXT = {".md", ".txt", ".py", ".yaml", ".yml", ".cpp", ".hpp", ".h", ".rst"}
SKIP_DIRS = {"build", "install", "log", ".git", "__pycache__", ".venv", "venv"}


def iter_files(paths: List[str]) -> Iterator[str]:
    for p in paths:
        if os.path.isfile(p):
            yield p
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for f in files:
                    if os.path.splitext(f)[1].lower() in TEXT_EXT:
                        yield os.path.join(root, f)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(
        description="Ingest documents into the RAG vector store.")
    ap.add_argument("paths", nargs="*",
                    help="files or directories to ingest (default: ./data)")
    ap.add_argument("--db", default=config.DEFAULT_DB_PATH)
    ap.add_argument("--collection", default=config.DEFAULT_COLLECTION)
    ap.add_argument("--chunk-size", type=int, default=config.CHUNK_SIZE)
    ap.add_argument("--overlap", type=int, default=config.CHUNK_OVERLAP)
    args = ap.parse_args(argv)

    paths = args.paths or ["data"]
    store = VectorStore(args.db, args.collection)

    total_files = 0
    total_chunks = 0
    for fp in iter_files(paths):
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                text = fh.read()
        except (UnicodeDecodeError, OSError):
            continue
        if not text.strip():
            continue
        chunks = chunk_text(text, source=os.path.relpath(fp),
                            chunk_size=args.chunk_size, overlap=args.overlap)
        store.add(chunks)
        total_files += 1
        total_chunks += len(chunks)
        print(f"  + {fp}  ({len(chunks)} chunks)")

    print(f"\nIngested {total_files} files, {total_chunks} chunks.")
    print(f"Collection '{args.collection}' now holds {store.count()} chunks "
          f"at {args.db}")


if __name__ == "__main__":
    main()
