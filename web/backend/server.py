"""FastAPI backend: a thin web layer over the copilot agent.

POST /api/ask {message} -> {reply}  runs the same AgentBrain used by the ROS2
agent node. The agent's tools (query_knowledge, navigate_to) talk to the running
ROS2 nodes over DDS, so start the ROS2 system alongside this for tools to work:

    # terminal 1 (sourced workspace): the ROS2 nodes
    ros2 launch copilot_bringup copilot.launch.py
    # terminal 2 (sourced workspace): the web server
    export ANTHROPIC_API_KEY=sk-ant-...
    uvicorn server:app --app-dir web/backend --host 0.0.0.0 --port 8000

Then open http://localhost:8000

Requires the workspace to be built and sourced (so `copilot_agent` and
`copilot_msgs` import), plus `pip install -r web/backend/requirements.txt`.
"""
import asyncio
import json
import os
import threading
import time
import uuid
from contextlib import asynccontextmanager

import rclpy
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from copilot_agent.agent import AgentBrain

_state = {"brain": None}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    rclpy.init()
    _state["brain"] = AgentBrain()
    try:
        yield
    finally:
        rclpy.shutdown()


app = FastAPI(title="ROS2 Copilot", lifespan=lifespan)


class AskRequest(BaseModel):
    message: str
    history: list = []  # prior [{"role", "content"}] text turns (optional)


@app.post("/api/ask")
async def ask(req: AskRequest):
    brain = _state["brain"]
    # The agent loop is blocking (LLM + ROS calls) — run it off the event loop.
    reply = await asyncio.get_event_loop().run_in_executor(
        None, brain.run, req.message, req.history)
    return {"reply": reply}


@app.post("/api/ask/stream")
async def ask_stream(req: AskRequest):
    """Server-Sent Events: stream tool calls, results, usage, and final text."""
    brain = _state["brain"]
    loop = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def worker():
        try:
            for event in brain.run_events(req.message, req.history):
                loop.call_soon_threadsafe(queue.put_nowait, event)
        except Exception as exc:  # noqa: BLE001 - surface to the client
            loop.call_soon_threadsafe(
                queue.put_nowait, {"type": "error", "message": str(exc)})
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)  # done sentinel

    threading.Thread(target=worker, daemon=True).start()

    async def event_stream():
        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ---- LLM Wiki: introspect the live ROS2 graph and (optionally) describe it ----

def _collect_graph() -> dict:
    """Spin a short-lived node to introspect the ROS2 graph (no LLM)."""
    from copilot_wiki.introspect import collect_graph
    node = rclpy.create_node(f"web_wiki_{uuid.uuid4().hex[:8]}")
    try:
        deadline = time.time() + 2.0
        while time.time() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        return collect_graph(node)
    finally:
        node.destroy_node()


@app.get("/api/wiki")
async def wiki():
    """Live system structure: nodes + their interfaces + a mermaid diagram."""
    def work():
        from copilot_wiki.wiki_gen import build_mermaid
        graph = _collect_graph()
        return {"nodes": graph["nodes"], "mermaid": build_mermaid(graph)}
    return await asyncio.get_event_loop().run_in_executor(None, work)


@app.get("/api/wiki/describe")
async def wiki_describe(node: str):
    """On-demand: LLM-written, grounded description of one node."""
    def work():
        from copilot_wiki import config as wcfg
        from copilot_wiki.wiki_gen import describe_node
        import anthropic
        graph = _collect_graph()
        info = graph["nodes"].get(node)
        if not info:
            return {"description": "(node not found on the graph)"}
        client = anthropic.Anthropic()
        return {"description": describe_node(client, node, info, wcfg.MODEL)}
    return await asyncio.get_event_loop().run_in_executor(None, work)


# ---- Live system status: runtime health of the running ROS2 system ----

# Health-relevant topics we measure a publish rate (Hz) for, when present.
_STATUS_TOPICS = ["/odom", "/scan", "/cmd_vel", "/copilot/estop", "/tf", "/map"]


def _collect_status(window_sec: float = 2.0) -> dict:
    """Sample the live system for a short window and summarize its health.

    Complements the wiki (static structure) with *runtime* signals: which
    nodes are alive, how fast key topics publish (Hz), the e-stop state, the
    robot pose, and whether the RAG service / executor action are reachable.
    """
    from rosidl_runtime_py.utilities import get_message
    from copilot_agent import config as acfg
    from copilot_agent.ros_bridge import _yaw_from_quat

    node = rclpy.create_node(f"web_status_{uuid.uuid4().hex[:8]}")
    counts: dict = {}
    latest: dict = {}
    subs = []
    try:
        topics = dict(node.get_topic_names_and_types())
        services = dict(node.get_service_names_and_types())

        def make_cb(name):
            def cb(msg):
                counts[name] = counts.get(name, 0) + 1
                latest[name] = msg
            return cb

        for tname in _STATUS_TOPICS:
            types = topics.get(tname)
            if not types:
                continue
            try:
                msg_cls = get_message(types[0])
            except Exception:  # noqa: BLE001 - unknown/uninstalled type
                continue
            counts[tname] = 0
            subs.append(node.create_subscription(
                msg_cls, tname, make_cb(tname), 10))

        deadline = time.time() + window_sec
        while time.time() < deadline:
            rclpy.spin_once(node, timeout_sec=0.05)

        topics_out = []
        for tname in _STATUS_TOPICS:
            if tname not in counts:
                continue
            topics_out.append({
                "name": tname,
                "hz": round(counts[tname] / window_sec, 1),
                "type": topics.get(tname, ["?"])[0],
            })

        robot = None
        if "/odom" in latest:
            p = latest["/odom"].pose.pose
            robot = {"x": round(p.position.x, 3), "y": round(p.position.y, 3),
                     "yaw": round(_yaw_from_quat(p.orientation), 3)}

        estop = None
        if "/copilot/estop" in latest:
            estop = {"engaged": bool(latest["/copilot/estop"].data)}

        names = sorted(n for n, _ in node.get_node_names_and_namespaces()
                       if n != node.get_name())

        return {
            "nodes": {"count": len(names), "names": names},
            "robot": robot,
            "estop": estop,
            "topics": topics_out,
            "services": {
                "rag": acfg.RAG_SERVICE in services,
                "executor_action": any(
                    s.startswith(acfg.EXECUTE_ACTION) for s in services),
            },
            "window_sec": window_sec,
        }
    finally:
        for s in subs:
            node.destroy_subscription(s)
        node.destroy_node()


@app.get("/api/status")
async def status():
    """Live runtime health snapshot (nodes, topic Hz, e-stop, pose, services)."""
    return await asyncio.get_event_loop().run_in_executor(None, _collect_status)


# ---- Transcripts: browse past agent interactions (if logging is enabled) ----

@app.get("/api/transcripts")
async def transcripts(limit: int = 50):
    """Return recent agent interaction records (most recent first).

    Reads the JSONL file the agent appends to when COPILOT_AGENT_LOG is set
    (shared with the ROS2 agent node). Returns an empty list + a hint when
    logging is off or nothing has been recorded yet.
    """
    from copilot_agent import config as acfg
    from copilot_agent.transcript import read_records
    path = acfg.TRANSCRIPT_PATH
    if not path:
        return {"enabled": False, "path": None, "records": [],
                "hint": "Set COPILOT_AGENT_LOG to a file path to record "
                        "transcripts."}
    records = await asyncio.get_event_loop().run_in_executor(
        None, read_records, path, limit)
    return {"enabled": True, "path": path, "records": records}


# Serve the static chat UI. Mounted last so /api/* routes take precedence.
_FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=_FRONTEND, html=True), name="frontend")
