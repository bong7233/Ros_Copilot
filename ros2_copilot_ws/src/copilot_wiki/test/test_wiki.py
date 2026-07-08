"""Offline tests for the wiki generator's deterministic parts.

No API key needed — these cover the grounded-by-construction pieces (the mermaid
diagram and name sanitizing), not the LLM prose.

Run: PYTHONPATH=ros2_copilot_ws/src/copilot_wiki pytest .../test_wiki.py
"""
from copilot_wiki.wiki_gen import build_mermaid, safe_name


def test_safe_name():
    assert safe_name("/copilot_executor") == "copilot_executor"
    assert safe_name("/a/b") == "a_b"
    assert safe_name("/") == "root"


def _graph():
    return {
        "nodes": {
            "talker": {
                "namespace": "/",
                "publishers": [{"name": "/copilot/heartbeat",
                                "types": ["copilot_msgs/msg/Heartbeat"]}],
                "subscribers": [],
                "services": [],
            },
            "listener": {
                "namespace": "/",
                "publishers": [],
                "subscribers": [{"name": "/copilot/heartbeat",
                                 "types": ["copilot_msgs/msg/Heartbeat"]}],
                "services": [],
            },
        },
        "topics": {},
        "services": {},
    }


def test_build_mermaid_includes_real_edges():
    m = build_mermaid(_graph())
    assert "flowchart LR" in m
    assert "/copilot/heartbeat" in m
    # both a publisher edge and a subscriber edge exist
    assert "-->" in m


def test_build_mermaid_hides_noise_topics():
    graph = _graph()
    graph["nodes"]["talker"]["publishers"].append(
        {"name": "/rosout", "types": ["rcl_interfaces/msg/Log"]})
    m = build_mermaid(graph)
    # /rosout is in HIDE_TOPICS and must not appear (grounded + denoised)
    assert "/rosout" not in m
