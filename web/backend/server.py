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
import os
from contextlib import asynccontextmanager

import rclpy
from fastapi import FastAPI
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


@app.post("/api/ask")
async def ask(req: AskRequest):
    brain = _state["brain"]
    # The agent loop is blocking (LLM + ROS calls) — run it off the event loop.
    reply = await asyncio.get_event_loop().run_in_executor(
        None, brain.run, req.message)
    return {"reply": reply}


# Serve the static chat UI. Mounted last so /api/* routes take precedence.
_FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=_FRONTEND, html=True), name="frontend")
