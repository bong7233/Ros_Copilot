#!/usr/bin/env python3
"""Safety evaluation for the executor — the "0 safety violations" check.

Unlike rag_eval.py, this one needs ROS2: run the executor first, then this.

    # terminal 1 (sourced workspace):
    ros2 run copilot_executor executor
    # terminal 2 (sourced workspace):
    python3 eval/agent_eval.py

It sends ExecuteCommand goals directly to the executor and asserts the safety
contract:
  1. an in-bounds goal is accepted and succeeds (mock motion)
  2. an out-of-bounds goal is REJECTED before any motion
  3. with e-stop active, an in-bounds goal is REJECTED

If all three hold, the safety layer is doing its job.
"""
import time

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import Bool

from copilot_msgs.action import ExecuteCommand


class Harness(Node):
    def __init__(self):
        super().__init__("agent_eval_harness")
        self.client = ActionClient(self, ExecuteCommand,
                                   "/copilot_executor/execute_command")
        self.estop_pub = self.create_publisher(Bool, "/copilot/estop", 10)

    def set_estop(self, value: bool):
        msg = Bool()
        msg.data = value
        for _ in range(5):
            self.estop_pub.publish(msg)
            time.sleep(0.05)

    def send(self, x: float, y: float):
        """Return (accepted, success, message)."""
        if not self.client.wait_for_server(timeout_sec=5.0):
            return None, None, "executor action server not available"
        goal = ExecuteCommand.Goal()
        goal.command = "navigate_to"
        goal.target.position.x = x
        goal.target.position.y = y
        goal.target.orientation.w = 1.0

        send_future = self.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future, timeout_sec=10.0)
        gh = send_future.result()
        if gh is None or not gh.accepted:
            return False, None, "rejected"

        result_future = gh.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=30.0)
        wrapped = result_future.result()
        if wrapped is None:
            return True, None, "no result (timeout)"
        return True, wrapped.result.success, wrapped.result.message


def main():
    rclpy.init()
    h = Harness()
    results = []
    try:
        # 1. in-bounds -> accepted + success
        acc, ok, msg = h.send(1.0, 1.0)
        results.append(("in-bounds accepted+succeeds", acc is True and ok is True, msg))

        # 2. out-of-bounds -> rejected
        acc, ok, msg = h.send(100.0, 100.0)
        results.append(("out-of-bounds rejected", acc is False, msg))

        # 3. e-stop active -> in-bounds rejected
        h.set_estop(True)
        time.sleep(0.3)
        acc, ok, msg = h.send(1.0, 1.0)
        results.append(("e-stop rejects motion", acc is False, msg))
        h.set_estop(False)
    finally:
        h.destroy_node()
        rclpy.shutdown()

    print(f"\n{'check':<32} {'result':<6} detail")
    print("-" * 60)
    violations = 0
    for name, passed, detail in results:
        if not passed:
            violations += 1
        print(f"{name:<32} {'PASS' if passed else 'FAIL':<6} {detail}")
    print(f"\nsafety violations: {violations}")
    return 0 if violations == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
