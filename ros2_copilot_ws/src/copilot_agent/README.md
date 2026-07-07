# copilot_agent + copilot_executor — Layer 2: AI Agent 🟩

Natural-language command → the agent reasons and calls tools → the robot acts,
with a C++ safety layer in between.

```
user ──> copilot_agent (Python brain)
             │  Claude picks tools
             ├─ query_knowledge ──> /copilot_rag/query        (Layer 1 RAG 🟦)
             └─ navigate_to ──────> /copilot_executor/execute_command (C++ action)
                                          │ safety validation (bounds, e-stop)
                                          └─> (mock nav now; Nav2 in Phase 4)
   copilot_safety_monitor (C++) ── /scan ──> /copilot/estop ──> executor aborts
```

## Pieces

| Package / node | Language | Role |
|---|---|---|
| `copilot_agent` `agent` | Python (rclpy) | `~/ask` service; runs the Claude agent loop |
| `copilot_agent` `agent_cli` | Python | one-shot CLI to test the agent |
| `copilot_executor` `executor` | **C++ (rclcpp)** | `ExecuteCommand` action server + safety validation |
| `copilot_executor` `safety_monitor` | **C++ (rclcpp)** | `/scan` → `/copilot/estop` emergency stop |

**Why C++ here:** the executor and safety monitor are the real-time / safety
critical parts — writing them in `rclcpp` both fits the role you're targeting and
guarantees "even if the LLM asks for something unsafe, the robot won't do it."

## Run it (needs the RAG service too)

```bash
# from ros2_copilot_ws/
colcon build
source install/setup.bash
export ANTHROPIC_API_KEY=sk-ant-...

# terminal 1 — RAG (Layer 1); ingest once beforehand (see copilot_rag/README.md)
ros2 run copilot_rag query_server
# terminal 2 — C++ executor
ros2 run copilot_executor executor
# terminal 3 — C++ safety monitor (optional; needs a /scan source)
ros2 run copilot_executor safety_monitor
# terminal 4 — ask the agent
ros2 run copilot_agent agent_cli "지식 베이스에서 costmap inflation이 뭔지 찾아보고, 그다음 좌표 (2, 1)로 가줘"
```

Or run the agent as a service:

```bash
ros2 run copilot_agent agent
ros2 service call /copilot_agent/ask copilot_msgs/srv/Ask "{request: '좌표 (2,1)로 가'}"
```

## Try the safety path

Publish a fake e-stop and watch the executor reject/abort:

```bash
ros2 topic pub /copilot/estop std_msgs/msg/Bool "{data: true}" -1
# now a navigate_to goal is rejected; set it back to false to allow motion
```

Or a target outside the map bounds (default ±10 m) is rejected by the executor's
validation before any motion.

## Known simplifications (improve later)

- `navigate_to` runs a mock motion loop — Phase 4 swaps in Nav2 `NavigateToPose`
- `get_robot_state` / `list_topics` tools not added yet
- Agent uses a manual loop (no streaming); fine for an MVP
