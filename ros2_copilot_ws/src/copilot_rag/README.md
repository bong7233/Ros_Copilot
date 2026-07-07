# copilot_rag — Layer 1: RAG knowledge assistant 🟦

Answers ROS2/robotics questions grounded in retrieved documents, with sources.
Exposed as a ROS2 service (`/copilot_rag/query`), and also usable standalone.

## Pipeline

```
docs ──chunk──> embed ──> Chroma vector store
                                  │
question ──> retrieve top-k ──> build prompt ──> Claude ──> answer + sources
```

| File | Role |
|---|---|
| `chunking.py` | split documents into overlapping chunks (dependency-free, unit-tested) |
| `store.py` | Chroma vector store wrapper (embeddings + retrieval) |
| `rag_engine.py` | retrieve → prompt → Claude → grounded answer + sources |
| `ingest.py` | CLI: load docs into the store (`ingest`) |
| `ask.py` | CLI: ask a question without ROS2 (`ask`) |
| `query_node.py` | ROS2 service node wrapping the engine (`query_server`) |
| `data/` | sample knowledge (ROS2 concepts, Nav2 costmap, QoS) |

## Setup

```bash
pip install anthropic chromadb        # not rosdep/apt packages
export ANTHROPIC_API_KEY=sk-ant-...   # or copy repo-root .env.example to .env
```

The embedding model is Chroma's built-in local model (no extra API key); it
downloads on first use.

## Try it standalone (no ROS2 build)

From this directory (`ros2_copilot_ws/src/copilot_rag/`):

```bash
python3 -m copilot_rag.ingest data
python3 -m copilot_rag.ask "Why does a large inflation_radius block a narrow doorway?"
python3 -m copilot_rag.ask "내 subscriber가 메시지를 못 받는데 뭘 먼저 확인해야 해?"
```

You should get an answer grounded in the sample docs, with the source files
listed. Ask something not in the docs — it should say it doesn't know (that's
grounding working).

## Try it as a ROS2 service

```bash
# from ros2_copilot_ws/
colcon build --packages-select copilot_msgs copilot_rag
source install/setup.bash
ros2 run copilot_rag ingest src/copilot_rag/data       # first time only
ros2 run copilot_rag query_server
# in another terminal:
ros2 service call /copilot_rag/query copilot_msgs/srv/Query \
  "{question: 'What is a ROS2 action used for?'}"
```

## Run the offline test

```bash
pytest src/copilot_rag/test/test_chunking.py
```

## Known simplifications (improve later — Phase 5)

- Fixed-size character chunking (paragraph/heading-aware is better)
- No reranking after retrieval
- Sources = retrieved docs (not parsed from the model's actual `[n]` citations)
- LLM call blocks the service callback (single-threaded executor)
