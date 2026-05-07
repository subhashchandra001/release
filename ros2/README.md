# ROS 2 Helpers

These scripts are thin wrappers for collecting and replaying TurtleBot4 data for
PrivateMap-Bench. Run them from the repository root after sourcing your ROS 2
and TurtleBot4 workspaces.

The default topic names come from `configs/topics_turtlebot4.yaml`. TurtleBot4
topics can differ when the robot is namespaced or sensors are remapped, so edit
that file before recording if your robot uses different names.

## Check Topics

```bash
ros2/turtlebot4_topics_check.sh
```

This verifies that the configured scan, odometry, TF, camera, map, and pose
topics are visible. Missing topics usually mean the robot stack is not fully
running or the names in `configs/topics_turtlebot4.yaml` need to be updated.

## Record A Bag

```bash
ros2/record_bag.sh --run-id tb4_run_001
```

By default, bags are written under `data/raw_rosbags/`. Raw bags should stay out
of Git. Use `--output` to choose a different local path, or `--all` if you need a
full diagnostic bag.

## Play A Bag

```bash
ros2/play_bag.sh data/raw_rosbags/tb4_run_001 --clock
```

Use `--clock` when replaying into SLAM, Nav2, or artifact export nodes that use
simulation time.

## Save A Map

```bash
ros2/save_map.sh --output data/maps/tb4_run_001_map
```

This calls `nav2_map_server`'s `map_saver_cli` and writes
`data/maps/tb4_run_001_map.yaml` plus `data/maps/tb4_run_001_map.pgm`.

## Launch Files

Record configured topics with a launch file:

```bash
ros2 launch ros2/launch/record_privatemap.launch.py run_id:=tb4_run_001
```

Start a Nav2 evaluation launch using a saved map:

```bash
ros2 launch ros2/launch/nav_eval.launch.py map:=data/maps/tb4_run_001_map.yaml
```

The example waypoint file at `ros2/nav2_waypoints_example.yaml` is a template
only. Replace the poses with measured map-frame waypoints for your environment.
