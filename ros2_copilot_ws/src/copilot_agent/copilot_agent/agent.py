"""The agent brain: Claude decides which tools to call; we execute them on ROS.

This is a *manual* agent loop (rather than the SDK tool_runner) because each tool
call maps to a ROS2 call — a service or an action — and we want explicit control
over that. The loop:

    user text -> Claude -> (tool_use? run ROS call, feed result back : done)

Pure Python + anthropic + our ros_bridge; no rclpy node here, so it can run from
a CLI or be wrapped in a ROS2 service node (see agent_node.py).
"""
from typing import Callable, List

import anthropic

from . import config
from . import ros_bridge

SYSTEM_PROMPT = (
    "You are the brain of a ROS2 mobile-robot copilot. Your tools: "
    "query_knowledge (look up ROS2/robotics facts you are unsure about), "
    "navigate_to (command the robot to a target pose), "
    "get_robot_state (read the robot's current position), and "
    "list_topics (see what ROS2 topics are active). "
    "Think before acting, and prefer checking knowledge first when a move "
    "might be unsafe or ambiguous. NEVER claim the robot moved or arrived "
    "unless navigate_to actually returned success — if it failed or was "
    "rejected, report that honestly. Respond in the user's language."
)

TOOLS = [
    {
        "name": "query_knowledge",
        "description": (
            "Look up ROS2/robotics knowledge from the robot's document "
            "knowledge base (RAG). Use when you need facts, definitions, or "
            "guidance you are not certain about."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to look up.",
                },
            },
            "required": ["question"],
        },
    },
    {
        "name": "navigate_to",
        "description": (
            "Command the robot to navigate to a target pose in the map frame. "
            "The executor validates safety before moving and may reject the "
            "goal; always check the returned status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "number", "description": "target x (meters)"},
                "y": {"type": "number", "description": "target y (meters)"},
                "theta": {
                    "type": "number",
                    "description": "target heading (radians), default 0",
                },
            },
            "required": ["x", "y"],
        },
    },
    {
        "name": "get_robot_state",
        "description": (
            "Read the robot's current position (x, y, yaw) from odometry. "
            "Use when the user asks where the robot is, or before deciding "
            "how far/where to move."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_topics",
        "description": (
            "List the ROS2 topics currently active on the system. Use to "
            "inspect what data streams exist or to debug the running system."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
]


class AgentBrain:
    def __init__(self, model: str = config.MODEL) -> None:
        self.client = anthropic.Anthropic()
        self.model = model

    def run(self, user_text: str, log: Callable[[str], None] = print) -> str:
        messages: List[dict] = [{"role": "user", "content": user_text}]
        total_in = total_out = 0
        while True:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
            total_in += resp.usage.input_tokens
            total_out += resp.usage.output_tokens
            if resp.stop_reason != "tool_use":
                log(f"[usage] input_tokens={total_in} output_tokens={total_out}")
                return next(
                    (b.text for b in resp.content if b.type == "text"), "")

            # Echo the assistant turn (incl. tool_use blocks) back into history.
            messages.append({"role": "assistant", "content": resp.content})

            tool_results = []
            for block in resp.content:
                if block.type != "tool_use":
                    continue
                log(f"[tool] {block.name}({block.input})")
                output = self._dispatch(block.name, block.input)
                log(f"[result] {output}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
            messages.append({"role": "user", "content": tool_results})

    @staticmethod
    def _dispatch(name: str, inp: dict) -> str:
        if name == "query_knowledge":
            answer, sources = ros_bridge.query_knowledge(inp["question"])
            src = ", ".join(sources) if sources else "none"
            return f"{answer}\n(sources: {src})"
        if name == "navigate_to":
            ok, msg = ros_bridge.navigate_to(
                float(inp["x"]), float(inp["y"]),
                float(inp.get("theta", 0.0)))
            return f"{'SUCCESS' if ok else 'FAILED'}: {msg}"
        if name == "get_robot_state":
            state = ros_bridge.get_robot_state()
            if state is None:
                return "no odometry available (is the robot/sim running?)"
            return (f"x={state['x']:.2f}, y={state['y']:.2f}, "
                    f"yaw={state['yaw']:.2f} rad")
        if name == "list_topics":
            topics = ros_bridge.list_topics()
            return "active topics:\n" + "\n".join(f"- {t}" for t in topics)
        return f"unknown tool: {name}"
