// Layer 2 "hands + safety": a C++ (rclcpp) action server for ExecuteCommand.
//
// The AI agent (Python) never drives the robot directly — it sends a high-level
// ExecuteCommand goal here. This node:
//   1. VALIDATES the goal (target within map bounds, not e-stopped)   <- safety
//   2. executes it, streaming feedback, aborting if e-stop fires
//
// Two execution backends, chosen by the `use_nav2` parameter:
//   - use_nav2:=false (default) -> a mock motion loop. Runs with no simulator,
//     so Phases 0-3 work without Nav2 installed.
//   - use_nav2:=true            -> delegates to Nav2's NavigateToPose action
//     (Phase 4). Safety validation + e-stop still apply on top of Nav2.
//
// Keeping validation in C++ means "even if the LLM asks for something unsafe,
// the robot won't do it."
//
// Run: ros2 run copilot_executor executor --ros-args -p use_nav2:=true

#include <atomic>
#include <chrono>
#include <functional>
#include <future>
#include <memory>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "std_msgs/msg/bool.hpp"
#include "copilot_msgs/action/execute_command.hpp"
#include "nav2_msgs/action/navigate_to_pose.hpp"

using namespace std::chrono_literals;
using ExecuteCommand = copilot_msgs::action::ExecuteCommand;
using GoalHandle = rclcpp_action::ServerGoalHandle<ExecuteCommand>;
using NavigateToPose = nav2_msgs::action::NavigateToPose;

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
    declare_parameter("use_nav2", false);

    estop_sub_ = create_subscription<std_msgs::msg::Bool>(
      "/copilot/estop", 10,
      [this](const std_msgs::msg::Bool & msg) {estop_active_ = msg.data;});

    nav2_client_ = rclcpp_action::create_client<NavigateToPose>(
      this, "navigate_to_pose");

    action_server_ = rclcpp_action::create_server<ExecuteCommand>(
      this, "~/execute_command",
      std::bind(&Executor::handle_goal, this, std::placeholders::_1,
        std::placeholders::_2),
      std::bind(&Executor::handle_cancel, this, std::placeholders::_1),
      std::bind(&Executor::handle_accepted, this, std::placeholders::_1));

    RCLCPP_INFO(get_logger(),
      "copilot_executor ready (action: ~/execute_command, use_nav2=%s)",
      get_parameter("use_nav2").as_bool() ? "true" : "false");
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
    if (get_parameter("use_nav2").as_bool()) {
      run_nav2(goal_handle);
    } else {
      run_mock(goal_handle);
    }
  }

  // ---- Backend A: mock motion (no simulator needed) ----
  void run_mock(const std::shared_ptr<GoalHandle> goal_handle)
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
      feedback->status = "navigating (mock)";
      feedback->progress = static_cast<float>(i) / static_cast<float>(steps);
      goal_handle->publish_feedback(feedback);
      rate.sleep();
    }

    result->success = true;
    result->message = "arrived (simulated)";
    goal_handle->succeed(result);
    RCLCPP_INFO(get_logger(), "goal complete (mock)");
  }

  // ---- Backend B: delegate to Nav2 NavigateToPose (Phase 4) ----
  void run_nav2(const std::shared_ptr<GoalHandle> goal_handle)
  {
    auto result = std::make_shared<ExecuteCommand::Result>();

    if (!nav2_client_->wait_for_action_server(2s)) {
      result->success = false;
      result->message = "Nav2 action server (navigate_to_pose) unavailable";
      goal_handle->abort(result);
      RCLCPP_ERROR(get_logger(), "%s", result->message.c_str());
      return;
    }

    const auto exec_goal = goal_handle->get_goal();
    NavigateToPose::Goal nav_goal;
    nav_goal.pose.header.frame_id = "map";
    nav_goal.pose.header.stamp = now();
    nav_goal.pose.pose = exec_goal->target;

    // Shared so the result callback stays valid even if we return early.
    auto done = std::make_shared<std::promise<void>>();
    auto done_fut = done->get_future();
    auto nav_success = std::make_shared<std::atomic<bool>>(false);

    rclcpp_action::Client<NavigateToPose>::SendGoalOptions opts;
    opts.feedback_callback =
      [this, goal_handle](
      rclcpp_action::ClientGoalHandle<NavigateToPose>::SharedPtr,
      const std::shared_ptr<const NavigateToPose::Feedback>) {
        auto fb = std::make_shared<ExecuteCommand::Feedback>();
        fb->status = "navigating (nav2)";
        fb->progress = 0.0f;  // Nav2 reports distance_remaining, not a fraction
        goal_handle->publish_feedback(fb);
      };
    opts.result_callback =
      [done, nav_success](
      const rclcpp_action::ClientGoalHandle<NavigateToPose>::WrappedResult & r) {
        nav_success->store(r.code == rclcpp_action::ResultCode::SUCCEEDED);
        done->set_value();
      };

    auto gh_future = nav2_client_->async_send_goal(nav_goal, opts);
    if (gh_future.wait_for(5s) != std::future_status::ready) {
      result->success = false;
      result->message = "Nav2 did not respond to the goal";
      goal_handle->abort(result);
      return;
    }
    auto nav_gh = gh_future.get();
    if (!nav_gh) {
      result->success = false;
      result->message = "Nav2 rejected the goal";
      goal_handle->abort(result);
      return;
    }

    // Monitor until Nav2 finishes, honoring e-stop and cancellation.
    while (done_fut.wait_for(100ms) != std::future_status::ready) {
      if (estop_active_ || goal_handle->is_canceling()) {
        nav2_client_->async_cancel_goal(nav_gh);
        result->success = false;
        if (estop_active_) {
          result->message = "aborted: e-stop triggered mid-motion";
          goal_handle->abort(result);
          RCLCPP_WARN(get_logger(), "aborted Nav2 goal by e-stop");
        } else {
          result->message = "canceled";
          goal_handle->canceled(result);
        }
        return;
      }
    }

    result->success = nav_success->load();
    result->message = result->success ? "arrived (Nav2)" : "Nav2 navigation failed";
    if (result->success) {
      goal_handle->succeed(result);
    } else {
      goal_handle->abort(result);
    }
    RCLCPP_INFO(get_logger(), "goal complete (nav2): %s", result->message.c_str());
  }

  bool within_bounds(double x, double y)
  {
    return x >= get_parameter("bounds_min_x").as_double() &&
           x <= get_parameter("bounds_max_x").as_double() &&
           y >= get_parameter("bounds_min_y").as_double() &&
           y <= get_parameter("bounds_max_y").as_double();
  }

  rclcpp_action::Server<ExecuteCommand>::SharedPtr action_server_;
  rclcpp_action::Client<NavigateToPose>::SharedPtr nav2_client_;
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
