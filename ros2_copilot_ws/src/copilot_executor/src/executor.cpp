// Layer 2 "hands + safety": a C++ (rclcpp) action server for ExecuteCommand.
//
// The AI agent (Python) never drives the robot directly — it sends a high-level
// ExecuteCommand goal here. This node:
//   1. VALIDATES the goal (target within map bounds, not e-stopped)   <- safety
//   2. executes it, streaming feedback, aborting if e-stop fires
//
// Phase 2 uses a mock motion loop. Phase 4 replaces the loop with a real Nav2
// NavigateToPose action call. Keeping validation in C++ means "even if the LLM
// asks for something unsafe, the robot won't do it."
//
// Run: ros2 run copilot_executor executor

#include <atomic>
#include <functional>
#include <memory>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "std_msgs/msg/bool.hpp"
#include "copilot_msgs/action/execute_command.hpp"

using ExecuteCommand = copilot_msgs::action::ExecuteCommand;
using GoalHandle = rclcpp_action::ServerGoalHandle<ExecuteCommand>;

class Executor : public rclcpp::Node
{
public:
  Executor()
  : Node("copilot_executor")
  {
    declare_parameter("bounds_min_x", -10.0);
    declare_parameter("bounds_max_x", 10.0);
    declare_parameter("bounds_min_y", -10.0);
    declare_parameter("bounds_max_y", 10.0);

    estop_sub_ = create_subscription<std_msgs::msg::Bool>(
      "/copilot/estop", 10,
      [this](const std_msgs::msg::Bool & msg) {estop_active_ = msg.data;});

    action_server_ = rclcpp_action::create_server<ExecuteCommand>(
      this, "~/execute_command",
      std::bind(&Executor::handle_goal, this, std::placeholders::_1,
        std::placeholders::_2),
      std::bind(&Executor::handle_cancel, this, std::placeholders::_1),
      std::bind(&Executor::handle_accepted, this, std::placeholders::_1));

    RCLCPP_INFO(get_logger(),
      "copilot_executor ready (action: ~/execute_command)");
  }

private:
  rclcpp_action::GoalResponse handle_goal(
    const rclcpp_action::GoalUUID &,
    std::shared_ptr<const ExecuteCommand::Goal> goal)
  {
    const auto & p = goal->target.position;
    if (estop_active_) {
      RCLCPP_WARN(get_logger(), "rejecting goal: e-stop active");
      return rclcpp_action::GoalResponse::REJECT;
    }
    if (!within_bounds(p.x, p.y)) {
      RCLCPP_WARN(get_logger(),
        "rejecting goal: target (%.2f, %.2f) out of bounds", p.x, p.y);
      return rclcpp_action::GoalResponse::REJECT;
    }
    RCLCPP_INFO(get_logger(), "accepting '%s' -> (%.2f, %.2f)",
      goal->command.c_str(), p.x, p.y);
    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  rclcpp_action::CancelResponse handle_cancel(
    const std::shared_ptr<GoalHandle>)
  {
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  void handle_accepted(const std::shared_ptr<GoalHandle> goal_handle)
  {
    // Run execution off the executor thread so we don't block callbacks.
    std::thread{std::bind(&Executor::execute, this, goal_handle)}.detach();
  }

  void execute(const std::shared_ptr<GoalHandle> goal_handle)
  {
    auto feedback = std::make_shared<ExecuteCommand::Feedback>();
    auto result = std::make_shared<ExecuteCommand::Result>();
    rclcpp::Rate rate(2.0);

    const int steps = 10;
    for (int i = 1; i <= steps; ++i) {
      if (estop_active_) {
        result->success = false;
        result->message = "aborted: e-stop triggered mid-motion";
        goal_handle->abort(result);
        RCLCPP_WARN(get_logger(), "aborted by e-stop");
        return;
      }
      if (goal_handle->is_canceling()) {
        result->success = false;
        result->message = "canceled";
        goal_handle->canceled(result);
        return;
      }
      feedback->status = "navigating";
      feedback->progress = static_cast<float>(i) / static_cast<float>(steps);
      goal_handle->publish_feedback(feedback);
      rate.sleep();
    }

    result->success = true;
    result->message = "arrived (simulated)";
    goal_handle->succeed(result);
    RCLCPP_INFO(get_logger(), "goal complete");
  }

  bool within_bounds(double x, double y)
  {
    return x >= get_parameter("bounds_min_x").as_double() &&
           x <= get_parameter("bounds_max_x").as_double() &&
           y >= get_parameter("bounds_min_y").as_double() &&
           y <= get_parameter("bounds_max_y").as_double();
  }

  rclcpp_action::Server<ExecuteCommand>::SharedPtr action_server_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr estop_sub_;
  std::atomic<bool> estop_active_{false};
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Executor>());
  rclcpp::shutdown();
  return 0;
}
