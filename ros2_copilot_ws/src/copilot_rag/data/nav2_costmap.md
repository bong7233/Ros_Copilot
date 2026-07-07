# Nav2 Costmaps and the Inflation Layer

## What a costmap is
Nav2 represents the robot's surroundings as a costmap: a 2D grid where each cell
holds a cost from 0 (free) to 254 (lethal obstacle), with 255 meaning unknown.
The planner and controller use these costs to find and follow safe paths. Nav2
maintains a global costmap (for planning across the whole map) and a local
costmap (a rolling window around the robot for reactive obstacle avoidance).

## Layers
A costmap is built from stacked layers, each contributing cost:
- **Static layer** — the pre-built map (walls, fixed structures).
- **Obstacle / voxel layer** — obstacles detected live from sensors like the
  laser scan (`/scan`).
- **Inflation layer** — expands cost outward around obstacles (see below).

## The inflation layer
The inflation layer adds a buffer of cost around every obstacle so the planner
keeps the robot a safe distance away rather than grazing walls. Two key
parameters:
- `inflation_radius` — how far the inflated cost extends from an obstacle.
- `cost_scaling_factor` — how quickly cost decays with distance (higher = faster
  decay, so a thinner high-cost band).

## Why a large inflation_radius can block narrow passages
If `inflation_radius` is set too large, the inflated cost from the two sides of a
narrow doorway or corridor can overlap in the middle, leaving no low-cost cells
for the robot to pass through. The planner then treats the doorway as blocked and
either routes around it or fails to find a path. To let the robot pass through
tight spaces, reduce `inflation_radius` (and/or raise `cost_scaling_factor`) so
the free channel through the gap is preserved — while keeping enough buffer to
stay safe. The footprint/robot radius must also physically fit through the gap.
