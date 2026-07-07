// Layer 2 safety: a C++ node that watches the laser scan and raises an e-stop
// when anything gets too close. It publishes /copilot/estop (Bool), which the
// executor honors above any command — so obstacle avoidance takes priority over
// whatever the LLM asked for.
//
// Note the use of rclcpp::SensorDataQoS() for /scan: sensor drivers usually
// publish BEST_EFFORT, so a default RELIABLE subscription would silently receive
// nothing (see docs/../ros2_qos.md — the classic QoS-mismatch pitfall).
//
// Run: ros2 run copilot_executor safety_monitor

#include <cmath>
#include <limits>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "std_msgs/msg/bool.hpp"

class SafetyMonitor : public rclcpp::Node
{
public:
  SafetyMonitor()
  : Node("copilot_safety_monitor")
  {
    declare_parameter("min_distance", 0.4);
    pub_ = create_publisher<std_msgs::msg::Bool>("/copilot/estop", 10);
    sub_ = create_subscription<sensor_msgs::msg::LaserScan>(
      "/scan", rclcpp::SensorDataQoS(),
      std::bind(&SafetyMonitor::on_scan, this, std::placeholders::_1));
    RCLCPP_INFO(get_logger(),
      "safety_monitor watching /scan -> /copilot/estop");
  }

private:
  void on_scan(const sensor_msgs::msg::LaserScan & scan)
  {
    const double min_d = get_parameter("min_distance").as_double();
    double closest = std::numeric_limits<double>::infinity();
    for (float r : scan.ranges) {
      if (std::isfinite(r) && r >= scan.range_min &&
        static_cast<double>(r) < closest)
      {
        closest = r;
      }
    }

    std_msgs::msg::Bool msg;
    msg.data = closest < min_d;
    if (msg.data) {
      RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 1000,
        "obstacle at %.2fm -> e-stop", closest);
    }
    pub_->publish(msg);
  }

  rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr pub_;
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr sub_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<SafetyMonitor>());
  rclcpp::shutdown();
  return 0;
}
