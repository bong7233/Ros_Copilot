"""Offline tests for transcript logging (no ROS / no API key)."""
import json
import os
import tempfile

from copilot_agent.transcript import append_record


def test_append_writes_valid_jsonl():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "sub", "transcripts.jsonl")  # nested dir created
        append_record(path, {"user": "hi", "reply": "hello"})
        append_record(path, {"user": "go", "reply": "ok"})

        with open(path, encoding="utf-8") as fh:
            lines = [json.loads(x) for x in fh if x.strip()]

        assert len(lines) == 2
        assert lines[0]["user"] == "hi" and lines[0]["reply"] == "hello"
        assert "ts" in lines[0]  # timestamp injected


def test_append_never_raises_on_bad_path():
    # A path under a file (not a dir) is invalid; must be swallowed, not raised.
    with tempfile.NamedTemporaryFile() as f:
        bad = os.path.join(f.name, "nope.jsonl")
        append_record(bad, {"user": "x"})  # should not raise
