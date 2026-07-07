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
    "You are the brain of a ROS2 mobile-robot copilot. You can look up "
    "ROS2/robotics knowledge and command the robot to navigate. "
    "Use query_knowledge when you need facts you are unsure about. "
    "Use navigate_to when the user wants the robot to move. "
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
]


class AgentBrain:
    def __init__(self, model: str = config.MODEL) -> None:
        self.client = anthropic.Anthropic()
        self.model = model

    def run(self, user_text: str, log: Callable[[str], None] = print) -> str:
        messages: List[dict] = [{"role": "user", "content": user_text}]
        while True:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
            if resp.stop_reason != "tool_use":
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
        return f"unknown tool: {name}"
