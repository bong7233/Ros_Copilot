cmake_minimum_required(VERSION 3.8)
project(copilot_executor)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(copilot_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

add_executable(executor src/executor.cpp)
ament_target_dependencies(executor
  rclcpp rclcpp_action copilot_msgs std_msgs geometry_msgs)

add_executable(safety_monitor src/safety_monitor.cpp)
ament_target_dependencies(safety_monitor
  rclcpp sensor_msgs std_msgs)

install(TARGETS executor safety_monitor
  DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
