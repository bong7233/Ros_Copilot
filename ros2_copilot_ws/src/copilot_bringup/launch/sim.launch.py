"""End-to-end simulation: TurtleBot3 in Gazebo + Nav2 + the copilot nodes.

This is the Phase 4 target. It reuses Nav2's turnkey TB3 simulation launch
(Gazebo world + robot + Nav2 + RViz with a default map), then starts the copilot
nodes with `use_nav2:=true` so the C++ executor drives the robot via Nav2.

Prerequisites (install on Ubuntu / in the Docker image):
    sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup \
                     ros-humble-turtlebot3-gazebo
    export TURTLEBOT3_MODEL=burger   # or waffle

Run:
    ros2 launch copilot_bringup sim.launch.py

Then, in another sourced terminal:
    export ANTHROPIC_API_KEY=sk-ant-...
    ros2 run copilot_agent agent_cli "creado 앞쪽으로 이동해서 뭐가 보이는지 알려줘"

NOTE: this is the phase that needs local iteration. The exact map/params and the
`tb3_simulation_launch.py` arguments may differ across ROS2/Nav2 versions — adjust
the launch_arguments below to match your installed Nav2. If your Nav2 doesn't ship
`tb3_simulation_launch.py`, compose `turtlebot3_world.launch.py` +
`nav2_bringup/bringup_launch.py` (with a map) instead.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    copilot_dir = get_package_share_directory('copilot_bringup')

    # Gazebo world + TB3 + Nav2 + RViz (uses sim time internally).
    tb3_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            nav2_bringup_dir, 'launch', 'tb3_simulation_launch.py')),
        # e.g. launch_arguments={'headless': 'False', 'slam': 'True'}.items()
    )

    # The copilot AI nodes, wired to drive the robot through Nav2.
    copilot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            copilot_dir, 'launch', 'copilot.launch.py')),
        launch_arguments={
            'use_nav2': 'true',
            'use_sim_time': 'true',
        }.items(),
    )

    return LaunchDescription([tb3_sim, copilot])
