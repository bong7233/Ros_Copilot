# copilot_bringup — Phase 4: launch & simulation

Brings the pieces up together, and (in sim) wires the C++ executor to real Nav2.

## Launch files

| File | What it starts |
|---|---|
| `copilot.launch.py` | The copilot AI nodes: RAG service, C++ executor + safety monitor, agent. No simulator. Pass `use_nav2:=true` to delegate motion to Nav2. |
| `sim.launch.py` | Gazebo (TurtleBot3) + Nav2 + the copilot nodes with `use_nav2:=true`. The full Phase 4 demo. |

## Run the AI nodes only (no sim)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
ros2 launch copilot_bringup copilot.launch.py
# executor runs in mock-motion mode; ask the agent from another terminal:
ros2 run copilot_agent agent_cli "좌표 (2,1)로 가"
```

## Run the full simulation (Phase 4)

```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup \
                 ros-humble-turtlebot3-gazebo
export TURTLEBOT3_MODEL=burger
ros2 launch copilot_bringup sim.launch.py
# then, in another terminal:
export ANTHROPIC_API_KEY=sk-ant-...
ros2 run copilot_agent agent_cli "앞쪽 방으로 이동해줘"
```

The executor validates the goal (bounds, e-stop) and forwards it to Nav2's
`navigate_to_pose`; the safety monitor can e-stop mid-motion, which cancels the
Nav2 goal.

## Why this phase needs local iteration

Gazebo, Nav2 params, and the map are environment- and version-specific. The
`sim.launch.py` here is a standard scaffold — expect to tweak the
`tb3_simulation_launch.py` arguments (map, SLAM vs. static map, headless) to your
installed Nav2. The `config/copilot_params.yaml` centralizes the copilot knobs
(safety bounds, e-stop distance) for tuning.

See [`../../../docs/ENVIRONMENT.md`](../../../docs/ENVIRONMENT.md) for how to get a
working ROS2 + Gazebo environment (Ubuntu / WSL2 / Docker).
