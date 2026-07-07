"""Offline unit tests for the chunker — no API key or vector DB needed.

Run: pytest src/copilot_rag/test/test_chunking.py
"""
from copilot_rag.chunking import chunk_text


def test_sliding_window_overlap():
    text = "abcdefghij" * 30  # 300 chars, no whitespace
    chunks = chunk_text(text, source="x", chunk_size=100, overlap=20)

    assert len(chunks) > 1
    # Consecutive chunks overlap by exactly `overlap` characters.
    assert chunks[0].text[-20:] == chunks[1].text[:20]
    for i, c in enumerate(chunks):
        assert c.index == i
        assert c.source == "x"
        assert len(c.text) <= 100


def test_empty_input_yields_no_chunks():
    assert chunk_text("   \n  \n", "x") == []


def test_overlap_must_be_smaller_than_chunk_size():
    try:
        chunk_text("abc", "x", chunk_size=100, overlap=100)
    except ValueError:
        return
    raise AssertionError("expected ValueError when overlap >= chunk_size")
