"""ROS2 service node exposing the agent as copilot_msgs/srv/Ask at ~/ask.

Uses a MultiThreadedExecutor + ReentrantCallbackGroup so the (blocking) agent
loop in the service callback can make its own ROS calls (via ros_bridge, which
spins temporary nodes) without deadlocking the executor.

Run:
    ros2 run copilot_agent agent
    ros2 service call /copilot_agent/ask copilot_msgs/srv/Ask "{request: '창고로 가'}"
"""
import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from copilot_msgs.srv import Ask

from .agent import AgentBrain


class AgentNode(Node):
    def __init__(self) -> None:
        super().__init__('copilot_agent')
        self.brain = AgentBrain()
        self.cbg = ReentrantCallbackGroup()
        self.srv = self.create_service(
            Ask, '~/ask', self.on_ask, callback_group=self.cbg)
        self.get_logger().info("agent ready at ~/ask")

    def on_ask(self, request, response):
        self.get_logger().info(f"ask: {request.request}")
        try:
            response.reply = self.brain.run(
                request.request, log=self.get_logger().info)
        except Exception as exc:  # noqa: BLE001 - surface failure to caller
            self.get_logger().error(f"agent failed: {exc}")
            response.reply = f"error: {exc}"
        return response


def main(args=None) -> None:
    rclpy.init(args=args)
    node = AgentNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
