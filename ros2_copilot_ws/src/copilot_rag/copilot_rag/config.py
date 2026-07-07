"""Central config for the RAG layer. All values overridable via env vars."""
import os

# Where the Chroma vector store lives on disk.
DEFAULT_DB_PATH = os.environ.get(
    "COPILOT_RAG_DB", os.path.expanduser("~/.copilot_rag/chroma"))

# Chroma collection name.
DEFAULT_COLLECTION = os.environ.get("COPILOT_RAG_COLLECTION", "copilot_docs")

# Claude model used to generate the grounded answer.
DEFAULT_MODEL = os.environ.get("COPILOT_RAG_MODEL", "claude-sonnet-5")

# How many chunks to retrieve per question.
DEFAULT_TOP_K = int(os.environ.get("COPILOT_RAG_TOP_K", "4"))

# Chunking parameters (characters, a simple proxy for tokens).
CHUNK_SIZE = int(os.environ.get("COPILOT_RAG_CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.environ.get("COPILOT_RAG_CHUNK_OVERLAP", "200"))
