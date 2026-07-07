"""LLM-as-judge: grade whether a RAG answer is correct and grounded.

Used by rag_eval.py --judge. Kept separate so it can be reused for the agent.
"""
import anthropic

_client = anthropic.Anthropic()

SYSTEM = (
    "You are a strict grader for a ROS2 knowledge assistant. Given a question, "
    "the assistant's answer, and the key terms a correct answer must convey, "
    "decide if the answer is correct and grounded. Output exactly 'PASS' or "
    "'FAIL' on the first line, then a one-line reason."
)


def grade(question: str, answer: str, must_convey, model: str = "claude-sonnet-5"):
    """Return (passed: bool, reason: str)."""
    prompt = (
        f"Question:\n{question}\n\n"
        f"Answer:\n{answer}\n\n"
        f"Key terms the answer must convey: {', '.join(must_convey) or '(none)'}\n\n"
        "Grade it."
    )
    resp = _client.messages.create(
        model=model, max_tokens=200, system=SYSTEM,
        messages=[{"role": "user", "content": prompt}])
    text = next((b.text for b in resp.content if b.type == "text"), "").strip()
    passed = text.upper().startswith("PASS")
    reason = text.split("\n", 1)[1].strip() if "\n" in text else ""
    return passed, reason
