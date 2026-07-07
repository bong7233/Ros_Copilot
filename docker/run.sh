#!/usr/bin/env bash
# Run the ROS2 Copilot container.
#
#   Headless (AI nodes, RAG, agent, Nav2 without GUI):
#       ANTHROPIC_API_KEY=sk-ant-... ./docker/run.sh
#
#   With Gazebo/RViz GUI on a Linux host with X11:
#       xhost +local:docker
#       ANTHROPIC_API_KEY=sk-ant-... ./docker/run.sh gui
#
# On Windows/macOS, GUI needs an X server (VcXsrv / XQuartz) or use WSLg on
# Windows 11. See docs/ENVIRONMENT.md.
set -euo pipefail

IMAGE="robo-copilot"
MODE="${1:-headless}"

COMMON=(--rm -it
  -e "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}"
  --net=host)

if [[ "$MODE" == "gui" ]]; then
  exec docker run "${COMMON[@]}" \
    -e "DISPLAY=${DISPLAY:-:0}" \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    "$IMAGE" bash
else
  exec docker run "${COMMON[@]}" "$IMAGE" bash
fi
