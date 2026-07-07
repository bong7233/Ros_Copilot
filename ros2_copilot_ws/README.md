# ros2_copilot_ws — colcon workspace

The ROS2 Copilot source lives here. See the top-level [docs](../docs/) for the
architecture, roadmap, and learning guide.

## Packages so far

| Package | Language | Phase | Role |
|---|---|---|---|
| `copilot_msgs` | interfaces (CMake) | 0 | Shared `msg` / `srv` / `action`, built by C++ and Python |
| `copilot_py_demo` | Python (rclpy) | 0 | Publishes `Heartbeat` on `/copilot/heartbeat` |
| `copilot_cpp_demo` | C++ (rclcpp) | 0 | Subscribes to `/copilot/heartbeat` |
| `copilot_rag` | Python (rclpy) | 1 | 🟦 RAG knowledge assistant, service `/copilot_rag/query` |
| `copilot_agent` | Python (rclpy) | 2 | 🟩 LLM agent brain, service `/copilot_agent/ask` |
| `copilot_executor` | **C++ (rclcpp)** | 2 | 🟩 `ExecuteCommand` action server + safety validation |
| `copilot_wiki` | Python (rclpy) | 3 | 🟨 auto-generate grounded docs from the ROS2 graph |
| `copilot_bringup` | launch (CMake) | 4 | launch files; Gazebo + Nav2 + copilot integration |
| `tools/llm_smoketest.py` | Python | 0 | Confirms the Claude API is reachable |

Phase 5 (evaluation) is next — see [ARCHITECTURE](../docs/ARCHITECTURE.md). For how
to get a working ROS2/Gazebo environment (Ubuntu / WSL2 / Docker) see
[docs/ENVIRONMENT.md](../docs/ENVIRONMENT.md).

## Phase 1 — RAG MVP 🟦

`copilot_rag` retrieves relevant document chunks and has Claude answer grounded
in them, with sources. It works **standalone (no ROS2 build)** or as a ROS2
service. See [`src/copilot_rag/README.md`](src/copilot_rag/README.md) for the
full walkthrough. Quick start:

```bash
pip install anthropic chromadb
export ANTHROPIC_API_KEY=sk-ant-...
cd src/copilot_rag
python3 -m copilot_rag.ingest data
python3 -m copilot_rag.ask "Why does a large inflation_radius block a doorway?"
```

## Phase 2 — AI Agent + C++ executor 🟩

The agent (`copilot_agent`, Python) reasons with Claude and calls tools that map
to ROS2 interfaces: `query_knowledge` → the RAG service, `navigate_to` → a **C++
action server** (`copilot_executor`) that validates safety before moving. A **C++
safety monitor** turns `/scan` obstacles into an e-stop that overrides any
command. This is where the C++/Python balance lives — see
[`src/copilot_agent/README.md`](src/copilot_agent/README.md).

## Phase 3 — LLM Wiki 🟨

`copilot_wiki` introspects the **live ROS2 graph** and auto-generates grounded
Markdown docs: a mermaid node graph (built deterministically from the facts) plus
one LLM-written page per node. Run the system, then
`ros2 run copilot_wiki generate --out docs/generated` (or `--dry-run` to see the
raw facts). See [`src/copilot_wiki/README.md`](src/copilot_wiki/README.md).

## Phase 4+ — needs local simulation

Phase 4 (Gazebo + Nav2 end-to-end) and Phase 5 (evaluation) are best developed
against a running simulator on your machine. The `copilot_executor` mock motion
is where real Nav2 `NavigateToPose` plugs in.

## Prerequisites

- ROS2 (Humble or Jazzy) installed and sourced
- `colcon` build tool
- Python: `pip install anthropic` (for the LLM smoke test)

## Build & run

```bash
# From ros2_copilot_ws/
colcon build
source install/setup.bash

# Terminal A — C++ listener
ros2 run copilot_cpp_demo listener

# Terminal B — Python talker
ros2 run copilot_py_demo talker
```

You should see the listener print `heard heartbeat #N from 'copilot_talker'`
once per second — that's a C++ node receiving a message a Python node published,
over a custom interface you built. ✅

## LLM smoke test (independent of ROS2)

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # or copy .env.example to .env
python3 tools/llm_smoketest.py
```

## Phase 0 "done when"

- [ ] `colcon build` succeeds
- [ ] C++ listener receives the Python talker's `Heartbeat` over `copilot_msgs`
- [ ] `llm_smoketest.py` prints a Claude reply

When all three pass, move on to **Phase 1 (RAG MVP)** in the [roadmap](../docs/ROADMAP.md).
