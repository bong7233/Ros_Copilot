"""Config for the LLM Wiki generator. Overridable via env vars."""
import os

MODEL = os.environ.get("COPILOT_WIKI_MODEL", "claude-sonnet-5")
OUT_DIR = os.environ.get("COPILOT_WIKI_OUT", "docs/generated")

# Noise topics/nodes to hide from the generated diagram and pages.
HIDE_TOPICS = {"/parameter_events", "/rosout"}
