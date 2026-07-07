# ros2_copilot_ws — colcon workspace

The ROS2 Copilot source lives here. See the top-level [docs](../docs/) for the
architecture, roadmap, and learning guide.

## Phase 0 — what's here now

| Package | Language | Role |
|---|---|---|
| `copilot_msgs` | interfaces (CMake) | Shared `msg` / `srv` / `action` definitions, built by both C++ and Python |
| `copilot_py_demo` | Python (rclpy) | Publishes `Heartbeat` on `/copilot/heartbeat` |
| `copilot_cpp_demo` | C++ (rclcpp) | Subscribes to `/copilot/heartbeat` |
| `tools/llm_smoketest.py` | Python | Confirms the Claude API is reachable (LLM first call) |

These demo packages prove the foundation: a **custom interface** built once and
used from **both C++ and Python**, plus a working **LLM call**. Later phases add
`copilot_rag`, `copilot_agent`, `copilot_executor`, `copilot_wiki`, and
`copilot_bringup` (see [ARCHITECTURE](../docs/ARCHITECTURE.md)).

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
