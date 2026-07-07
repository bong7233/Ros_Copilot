#!/usr/bin/env bash
# One-command web demo, run INSIDE the container:
#   docker run -it --rm -p 8000:8000 -e ANTHROPIC_API_KEY=sk-ant-... \
#              robo-copilot bash /app/docker/web-demo.sh
# Then open http://localhost:8000
set -e

source /opt/ros/humble/setup.bash
source /app/ros2_copilot_ws/install/setup.bash

echo "[1/3] Ingesting sample knowledge into the RAG store…"
( cd /app/ros2_copilot_ws/src/copilot_rag && python3 -m copilot_rag.ingest data ) || true

echo "[2/3] Launching the ROS2 copilot nodes (background)…"
ros2 launch copilot_bringup copilot.launch.py > /tmp/copilot.log 2>&1 &
sleep 6

echo "[3/3] Starting the web server on http://localhost:8000 …"
exec uvicorn server:app --app-dir /app/web/backend --host 0.0.0.0 --port 8000
