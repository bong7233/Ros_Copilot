// Phase 0 demo: a rclcpp node that subscribes to Heartbeat.
//
// This proves the C++ side of the C++/Python cross-language setup and that the
// custom copilot_msgs/Heartbeat interface is usable from C++ (rclcpp).
//
// Run (after building the workspace and sourcing install/setup.bash):
//     ros2 run copilot_cpp_demo listener

#include "rclcpp/rclcpp.hpp"
#include "copilot_msgs/msg/heartbeat.hpp"

class Listener : public rclcpp::Node
{
public:
  Listener()
  : Node("copilot_listener")
  {
    sub_ = create_subscription<copilot_msgs::msg::Heartbeat>(
      "copilot/heartbeat", 10,
      [this](const copilot_msgs::msg::Heartbeat & msg) {
        RCLCPP_INFO(
          get_logger(), "heard heartbeat #%llu from '%s'",
          static_cast<unsigned long long>(msg.count), msg.node_name.c_str());
      });
    RCLCPP_INFO(
      get_logger(),
      "copilot_listener started, subscribing to /copilot/heartbeat");
  }

private:
  rclcpp::Subscription<copilot_msgs::msg::Heartbeat>::SharedPtr sub_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Listener>());
  rclcpp::shutdown();
  return 0;
}
