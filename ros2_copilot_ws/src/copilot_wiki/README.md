# copilot_wiki — Layer 3: LLM Wiki 🟨

Introspects the **live ROS2 graph** and auto-generates grounded Markdown docs:
an index with a mermaid node graph, plus one page per node listing its
publishers / subscribers / services with an LLM-written description.

```
running ROS2 graph ──introspect (rclpy)──> facts (nodes/topics/services)
                                              │
              mermaid graph (deterministic) ──┤
              per-node prose (Claude, grounded)┘
                                              ▼
                                   docs/generated/*.md
```

## Grounding — the whole point

The mermaid diagram is built **directly from the facts** (it literally cannot
invent an edge). The per-node text is written by Claude but constrained to
describe **only the listed interfaces** — no made-up topics. Same discipline as
RAG: describe what's real, admit when you can't.

## Run it

```bash
# from ros2_copilot_ws/, with the system running (Phase 0/2 nodes, etc.)
colcon build --packages-select copilot_wiki
source install/setup.bash
export ANTHROPIC_API_KEY=sk-ant-...

# inspect the raw facts first (no LLM call):
ros2 run copilot_wiki generate --dry-run

# generate the wiki:
ros2 run copilot_wiki generate --out docs/generated
```

Start a couple of nodes first so there's something to document, e.g.:

```bash
ros2 run copilot_py_demo talker &
ros2 run copilot_executor executor &
ros2 run copilot_wiki generate --out /tmp/wiki
```

## What you learn here

- ROS2 graph introspection API (`get_node_names_and_namespaces`,
  `get_publisher_names_and_types_by_node`, …)
- Deterministic (grounded-by-construction) vs. LLM-generated content, and when
  to use which
- Keeping generation grounded so docs stay trustworthy

## Improve later

- Parse source comments/params for richer descriptions
- Cross-link topics between node pages
- Regenerate on a timer or on graph change
