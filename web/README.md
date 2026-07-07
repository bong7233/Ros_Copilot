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

## Design notes

- One process: FastAPI serves both the JSON API and the static `frontend/`.
- The blocking agent loop runs in a thread pool so it doesn't block the event
  loop; each request spins short-lived ROS client nodes (see
  `copilot_agent/ros_bridge.py`).
- Frontend is a single dependency-free `index.html` (no build step).

## Extensions

- Stream the reply token-by-token (SSE) instead of waiting for the full answer
- Show which tools were called (surface the agent's tool trace)
- Auth + rate limiting before exposing beyond localhost
