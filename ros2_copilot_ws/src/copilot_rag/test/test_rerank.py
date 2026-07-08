"""Offline tests for the lexical reranker (no API key / vector DB)."""
from copilot_rag.rerank import lexical_score, rerank


def test_lexical_score():
    assert lexical_score("costmap inflation radius", "the inflation radius") > 0
    assert lexical_score("costmap inflation", "unrelated text here") == 0.0
    # all question words present -> score 1.0
    assert lexical_score("qos reliability", "qos reliability matters") == 1.0
    assert lexical_score("", "anything") == 0.0


def test_rerank_orders_by_overlap():
    hits = [
        {"text": "a document about batteries", "source": "a"},
        {"text": "the inflation radius controls costmap spacing", "source": "b"},
        {"text": "nodes and topics", "source": "c"},
    ]
    ordered = rerank("what is costmap inflation radius", hits)
    assert ordered[0]["source"] == "b"  # most lexical overlap first
