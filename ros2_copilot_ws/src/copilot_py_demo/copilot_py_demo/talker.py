"""Phase 0 demo: a rclpy node that publishes a Heartbeat once per second.

This proves the Python side of the C++/Python cross-language setup and that the
custom `copilot_msgs/Heartbeat` interface builds and imports correctly.

Run (after building the workspace and sourcing install/setup.bash):
    ros2 run copilot_py_demo talker
"""
import rclpy
from rclpy.node import Node

from copilot_msgs.msg import Heartbeat


class Talker(Node):
    def __init__(self) -> None:
        super().__init__('copilot_talker')
        self.pub = self.create_publisher(Heartbeat, 'copilot/heartbeat', 10)
        self.count = 0
        self.timer = self.create_timer(1.0, self.tick)
        self.get_logger().info(
            "copilot_talker started, publishing on /copilot/heartbeat")

    def tick(self) -> None:
        msg = Heartbeat()
        msg.node_name = self.get_name()
        msg.count = self.count
        msg.stamp = self.get_clock().now().to_msg()
        self.pub.publish(msg)
        self.get_logger().info(f'published heartbeat #{self.count}')
        self.count += 1


def main(args=None) -> None:
    rclpy.init(args=args)
    node = Talker()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
