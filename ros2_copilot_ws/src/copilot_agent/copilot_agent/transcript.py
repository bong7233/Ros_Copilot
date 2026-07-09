"""Optional conversation-transcript logging for the agent.

When the COPILOT_AGENT_LOG env var points to a file, each interaction (user
message, the tools the agent called, the reply, and token usage) is appended as
one JSON line. Useful for debugging a running system and for collecting eval
data. Best-effort: logging failures never break the agent.

Dependency-free (json/os/datetime) so it imports and unit-tests without ROS or
the Anthropic SDK.
"""
import json
import os
from datetime import datetime, timezone


def append_record(path: str, record: dict) -> None:
    """Append one interaction record as a JSON line (never raises)."""
    try:
        parent = os.path.dirname(os.path.abspath(path))
        os.makedirs(parent, exist_ok=True)
        line = {"ts": datetime.now(timezone.utc).isoformat(), **record}
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError:
        pass  # observability must never crash the agent
