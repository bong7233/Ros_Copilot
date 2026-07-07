# ROS2 Copilot dev/run image.
# Build from the repo root:
#     docker build -f docker/Dockerfile -t robo-copilot .
#
# Base: full ROS2 Humble desktop (includes Gazebo + RViz).
FROM osrf/ros:humble-desktop-full

SHELL ["/bin/bash", "-c"]

# System deps: Nav2, TurtleBot3 simulation, pip.
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3-pip \
      ros-humble-navigation2 \
      ros-humble-nav2-bringup \
      ros-humble-turtlebot3 \
      ros-humble-turtlebot3-gazebo \
 && rm -rf /var/lib/apt/lists/*

# Python deps for the AI layers (anthropic, chromadb).
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

ENV TURTLEBOT3_MODEL=burger

# Copy the workspace and build it.
WORKDIR /ws
COPY ros2_copilot_ws/ /ws/
RUN source /opt/ros/humble/setup.bash && \
    rosdep update && \
    apt-get update && \
    rosdep install --from-paths src --ignore-src -r -y || true && \
    rm -rf /var/lib/apt/lists/* && \
    colcon build --symlink-install

# Auto-source ROS + the workspace in interactive shells.
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "source /ws/install/setup.bash" >> /root/.bashrc

CMD ["bash"]
