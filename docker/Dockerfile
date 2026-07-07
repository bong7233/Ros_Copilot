# ROS2 Copilot dev/run image.
# Build from the repo root:
#     docker build -f docker/Dockerfile -t robo-copilot .
#
# Base: full ROS2 Humble desktop (includes Gazebo + RViz).
FROM osrf/ros:humble-desktop-full

SHELL ["/bin/bash", "-c"]

# System deps: Nav2, TurtleBot3 simulation, pip, git.
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3-pip git \
      ros-humble-navigation2 \
      ros-humble-nav2-bringup \
      ros-humble-turtlebot3 \
      ros-humble-turtlebot3-gazebo \
 && rm -rf /var/lib/apt/lists/*

ENV TURTLEBOT3_MODEL=burger

# Copy the whole repo (ros2 ws + web + eval + docker scripts).
WORKDIR /app
COPY . /app

# Python deps: AI layers + web backend.
RUN pip3 install --no-cache-dir -r requirements.txt -r web/backend/requirements.txt

# Build the ROS2 workspace.
RUN source /opt/ros/humble/setup.bash && \
    cd ros2_copilot_ws && \
    (rosdep update && rosdep install --from-paths src --ignore-src -r -y || true) && \
    colcon build --symlink-install

# Auto-source ROS + the workspace in interactive shells.
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "source /app/ros2_copilot_ws/install/setup.bash" >> /root/.bashrc && \
    echo "cd /app" >> /root/.bashrc

CMD ["bash"]
