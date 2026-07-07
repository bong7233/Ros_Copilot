"""Bring up the copilot AI nodes (no simulator).

This launches Layer 1-2: the RAG service, the C++ executor + safety monitor, and
the agent. Use `use_nav2:=true` to make the executor delegate to Nav2 (requires
Nav2 running — see sim.launch.py).

    ros2 launch copilot_bringup copilot.launch.py
    ros2 launch copilot_bringup copilot.launch.py use_nav2:=true use_sim_time:=true
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    use_nav2 = LaunchConfiguration('use_nav2')
    use_sim_time = LaunchConfiguration('use_sim_time')

    common = [{'use_sim_time': ParameterValue(use_sim_time, value_type=bool)}]

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_nav2', default_value='false',
            description='If true, the executor delegates motion to Nav2.'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use the /clock from the simulator.'),

        Node(package='copilot_rag', executable='query_server',
             name='copilot_rag', output='screen', parameters=common),

        Node(package='copilot_executor', executable='executor',
             name='copilot_executor', output='screen',
             parameters=common + [{
                 'use_nav2': ParameterValue(use_nav2, value_type=bool),
             }]),

        Node(package='copilot_executor', executable='safety_monitor',
             name='copilot_safety_monitor', output='screen', parameters=common),

        Node(package='copilot_agent', executable='agent',
             name='copilot_agent', output='screen', parameters=common),
    ])
