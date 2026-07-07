#!/usr/bin/env bash
# Run the ROS2 Copilot container.
#
#   Web demo (chat UI at http://localhost:8000) — easiest:
#       ANTHROPIC_API_KEY=sk-ant-... ./docker/run.sh web
#
#   Headless shell (RAG, agent, eval — no GUI):
#       ANTHROPIC_API_KEY=sk-ant-... ./docker/run.sh
#
#   GUI shell (Gazebo/RViz on a Linux host with X11):
#       xhost +local:docker
#       ANTHROPIC_API_KEY=sk-ant-... ./docker/run.sh gui
#
# On Windows/macOS the GUI mode needs an X server (or Win11 WSLg). The `web`
# mode works everywhere. See docs/HOW_TO_RUN.md.
set -euo pipefail

IMAGE="robo-copilot"
MODE="${1:-headless}"
KEY="${ANTHROPIC_API_KEY:-}"

case "$MODE" in
  web)
    exec docker run --rm -it -p 8000:8000 \
      -e "ANTHROPIC_API_KEY=$KEY" \
      "$IMAGE" bash /app/docker/web-demo.sh
    ;;
  gui)
    exec docker run --rm -it --net=host \
      -e "ANTHROPIC_API_KEY=$KEY" \
      -e "DISPLAY=${DISPLAY:-:0}" \
      -v /tmp/.X11-unix:/tmp/.X11-unix \
      "$IMAGE" bash
    ;;
  *)
    exec docker run --rm -it \
      -e "ANTHROPIC_API_KEY=$KEY" \
      "$IMAGE" bash
    ;;
esac
