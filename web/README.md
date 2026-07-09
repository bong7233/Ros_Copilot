# web — Phase 6: chat web frontend (optional)

A thin web UI to talk to the robot agent from a browser — the "web app" face of
the system, matching this repo's original web-project intent. It does **not**
replace the ROS2 core; it wraps the agent's `~/ask` capability in HTTP.

```
browser (chat UI)  ──HTTP /api/ask──>  FastAPI (server.py)
                                            │ AgentBrain.run()
                                            ├─ query_knowledge ─> RAG node (DDS)
                                            └─ navigate_to ─────> executor (DDS)
```

## Run

Build + source the workspace first (so `copilot_agent` / `copilot_msgs` import).

```bash
# terminal 1 — the ROS2 nodes (so the agent's tools work)
ros2 launch copilot_bringup copilot.launch.py

# terminal 2 — the web server (same sourced env)
pip install -r web/backend/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn server:app --app-dir web/backend --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000> and chat. Try:
- "costmap inflation이 뭐야?" → the agent uses RAG and answers with sources
- "좌표 (2,1)로 가줘" → the agent calls the executor to navigate

If you start the web server **without** the ROS2 nodes running, the chat still
works but tool calls return "unavailable" — the agent will say so honestly.

Watch the **🔧 tool chips** appear live as the agent decides to look up
knowledge or command the robot — the web UI streams the agent's trace over
Server-Sent Events and shows token usage per answer. When the agent uses RAG,
the **📄 source documents** it grounded on are shown as citation chips under the
answer. Conversation is
**multi-turn**: the browser keeps the prior turns and sends them as context, so
you can say "그럼 거기로 가" after asking about a place. "새 대화" clears it.

## Endpoints

- `POST /api/ask` → `{reply}` (blocking, simple)
- `POST /api/ask/stream` → Server-Sent Events: `tool_call` / `tool_result` /
  `usage` / `final` (used by the chat UI)

## Design notes

- One process: FastAPI serves both the JSON API and the static `frontend/`.
- The agent loop is a generator (`AgentBrain.run_events`); the SSE endpoint runs
  it in a background thread feeding an asyncio queue, so the event loop stays
  responsive. Each request spins short-lived ROS client nodes (see
  `copilot_agent/ros_bridge.py`).
- Frontend is a single dependency-free `index.html` (no build step); it parses
  SSE from a `fetch` stream reader.

## Extensions

- Token-by-token streaming of the final text (not just per-event)
- Auth + rate limiting before exposing beyond localhost
- Server-side session history (currently the browser holds it)
