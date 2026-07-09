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
from typing import List


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


def read_records(path: str, limit: int = 50) -> List[dict]:
    """Read the last ``limit`` transcript records, most recent first.

    Best-effort and dependency-free (mirrors ``append_record``): a missing
    file yields ``[]`` and malformed lines are skipped rather than raising, so
    a live/partially-written log never breaks the viewer.
    """
    if not path or not os.path.exists(path):
        return []
    records: List[dict] = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except (ValueError, TypeError):
                    continue  # skip a truncated/half-written trailing line
    except OSError:
        return []
    if limit and limit > 0:
        records = records[-limit:]
    records.reverse()  # most recent first
    return records
