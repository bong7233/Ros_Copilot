#!/usr/bin/env python3
"""Phase 0 smoke test: confirm the Claude API is reachable from your machine.

This is the "LLM first call" deliverable of Phase 0 — it has nothing to do with
ROS2 yet. It just proves your key works and the anthropic SDK is installed, so
that Phase 1 (RAG) can build on it.

Usage:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 tools/llm_smoketest.py
"""
import os
import sys


def main() -> int:
    try:
        import anthropic
    except ImportError:
        print("anthropic SDK not installed. Run: pip install anthropic",
              file=sys.stderr)
        return 1

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set. Export it first "
              "(see .env.example).", file=sys.stderr)
        return 1

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": (
                "You are the brain of a ROS2 robot copilot being wired up for "
                "the first time. Reply in one short sentence confirming you are "
                "reachable."
            ),
        }],
    )
    text = next((b.text for b in resp.content if b.type == "text"), "")
    print("Claude replied:", text)
    print("OK - LLM reachable. Phase 0 LLM check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
