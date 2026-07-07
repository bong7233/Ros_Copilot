cmake_minimum_required(VERSION 3.8)
project(copilot_cpp_demo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(copilot_msgs REQUIRED)

add_executable(listener src/listener.cpp)
ament_target_dependencies(listener rclcpp copilot_msgs)

install(TARGETS listener
  DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
