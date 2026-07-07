"""Run the agent once from the command line — the simplest way to test it.

Requires the RAG service and executor action server to be running (for the
tools to work), plus ANTHROPIC_API_KEY.

Usage (after colcon build + source):
    ros2 run copilot_agent agent_cli "창고 구역으로 가줘"
    ros2 run copilot_agent agent_cli "What is a costmap inflation layer?"
"""
import sys

import rclpy

from .agent import AgentBrain


def main(args=None) -> None:
    rclpy.init(args=args)
    user_text = " ".join(sys.argv[1:]).strip() or "안녕, 넌 뭘 할 수 있어?"
    try:
        brain = AgentBrain()
        reply = brain.run(user_text)
        print("\n=== Agent reply ===")
        print(reply)
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
