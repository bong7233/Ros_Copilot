"""Config for the agent brain. Overridable via env vars."""
import os

# The agent does multi-step reasoning, so default to the strongest model.
MODEL = os.environ.get("COPILOT_AGENT_MODEL", "claude-opus-4-8")

# ROS interface names the agent's tools talk to.
RAG_SERVICE = os.environ.get("COPILOT_RAG_SERVICE", "/copilot_rag/query")
EXECUTE_ACTION = os.environ.get(
    "COPILOT_EXECUTE_ACTION", "/copilot_executor/execute_command")
