"""Offline tests for transcript logging (no ROS / no API key)."""
import json
import os
import tempfile

from copilot_agent.transcript import append_record, read_records


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


def test_read_records_missing_file_returns_empty():
    assert read_records("/no/such/transcripts.jsonl") == []
    assert read_records(None) == []


def test_read_records_most_recent_first_and_limit():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "transcripts.jsonl")
        for i in range(5):
            append_record(path, {"user": f"q{i}", "reply": f"a{i}"})

        recent = read_records(path, limit=3)
        assert [r["user"] for r in recent] == ["q4", "q3", "q2"]  # newest first

        all_recs = read_records(path, limit=0)  # 0 = no cap
        assert len(all_recs) == 5


def test_read_records_skips_malformed_lines():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "transcripts.jsonl")
        append_record(path, {"user": "ok", "reply": "fine"})
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("{ this is not valid json\n")  # e.g. a half-written line

        recs = read_records(path)
        assert len(recs) == 1 and recs[0]["user"] == "ok"
