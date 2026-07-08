"""Synchronous ROS2 calls used by the agent's tools.

Each function spins a short-lived temporary node to make one call and returns a
plain Python result. Using a fresh node (with its own temporary executor) keeps
these calls re-entrancy-free: they work whether called from a CLI or from inside
another node's callback under a MultiThreadedExecutor.

`rclpy.init()` must already have been called by the process using these.
"""
import math
import time
import uuid

import rclpy
from rclpy.action import ActionClient

from copilot_msgs.srv import Query
from copilot_msgs.action import ExecuteCommand
from nav_msgs.msg import Odometry

from . import config


def _yaw_from_quat(q) -> float:
    """Extract yaw (rotation about z) from a quaternion."""
    siny = 2.0 * (q.w * q.z + q.x * q.y)
    cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny, cosy)


def query_knowledge(question: str, timeout: float = 30.0):
    """Call the RAG service. Returns (answer: str, sources: list[str])."""
    node = rclpy.create_node(f"agent_query_{uuid.uuid4().hex[:8]}")
    try:
        client = node.create_client(Query, config.RAG_SERVICE)
        if not client.wait_for_service(timeout_sec=5.0):
            return f"RAG service {config.RAG_SERVICE} unavailable", []
        req = Query.Request()
        req.question = question
        future = client.call_async(req)
        rclpy.spin_until_future_complete(node, future, timeout_sec=timeout)
        if future.result() is None:
            return "RAG query timed out", []
        res = future.result()
        return res.answer, list(res.sources)
    finally:
        node.destroy_node()


def navigate_to(x: float, y: float, theta: float = 0.0, timeout: float = 60.0):
    """Send an ExecuteCommand goal to the executor. Returns (ok: bool, msg: str)."""
    node = rclpy.create_node(f"agent_nav_{uuid.uuid4().hex[:8]}")
    try:
        ac = ActionClient(node, ExecuteCommand, config.EXECUTE_ACTION)
        if not ac.wait_for_server(timeout_sec=5.0):
            return False, f"executor action {config.EXECUTE_ACTION} unavailable"

        goal = ExecuteCommand.Goal()
        goal.command = "navigate_to"
        goal.target.position.x = float(x)
        goal.target.position.y = float(y)
        # Encode yaw (theta) as a quaternion about z.
        goal.target.orientation.z = math.sin(theta / 2.0)
        goal.target.orientation.w = math.cos(theta / 2.0)

        send_future = ac.send_goal_async(goal)
        rclpy.spin_until_future_complete(node, send_future, timeout_sec=10.0)
        goal_handle = send_future.result()
        if goal_handle is None or not goal_handle.accepted:
            return False, "goal rejected by executor (failed a safety check?)"

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(node, result_future, timeout_sec=timeout)
        wrapped = result_future.result()
        if wrapped is None:
            return False, "navigation timed out"
        return wrapped.result.success, wrapped.result.message
    finally:
        node.destroy_node()


def get_robot_state(timeout: float = 5.0):
    """Read the robot's current pose from /odom.

    Returns a dict {x, y, yaw} or None if no odometry was received.
    """
    node = rclpy.create_node(f"agent_state_{uuid.uuid4().hex[:8]}")
    latest = {}
    try:
        node.create_subscription(
            Odometry, "/odom", lambda m: latest.__setitem__("msg", m), 10)
        deadline = time.time() + timeout
        while time.time() < deadline and "msg" not in latest:
            rclpy.spin_once(node, timeout_sec=0.1)
        if "msg" not in latest:
            return None
        p = latest["msg"].pose.pose
        return {
            "x": p.position.x,
            "y": p.position.y,
            "yaw": _yaw_from_quat(p.orientation),
        }
    finally:
        node.destroy_node()


def list_topics(timeout: float = 2.0):
    """Return the list of topic names currently on the ROS2 graph."""
    node = rclpy.create_node(f"agent_topics_{uuid.uuid4().hex[:8]}")
    try:
        deadline = time.time() + timeout
        while time.time() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        return sorted(name for name, _ in node.get_topic_names_and_types())
    finally:
        node.destroy_node()
