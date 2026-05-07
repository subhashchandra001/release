"""Launch ros2 bag recording for PrivateMap-Bench TurtleBot4 topics."""

from pathlib import Path

import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
from launch.substitutions import LaunchConfiguration


def _truthy(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


def _record_process(context, *_args, **_kwargs):
    topics_config = Path(LaunchConfiguration("topics_config").perform(context))
    output = LaunchConfiguration("output").perform(context)
    all_topics = _truthy(LaunchConfiguration("all_topics").perform(context))

    if all_topics:
        cmd = ["ros2", "bag", "record", "-a", "-o", output]
    else:
        # Edit configs/topics_turtlebot4.yaml if your TurtleBot4 topic names
        # differ because of namespacing, sensor changes, or custom remaps.
        with topics_config.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        topics = [topic for topic in (data.get("topics", {}) or {}).values() if topic]
        if not topics:
            raise RuntimeError(f"No topics found in {topics_config}")
        cmd = ["ros2", "bag", "record", "-o", output, *topics]

    return [ExecuteProcess(cmd=cmd, output="screen")]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "topics_config",
                default_value="configs/topics_turtlebot4.yaml",
                description="YAML file containing the TurtleBot4 topic names.",
            ),
            DeclareLaunchArgument(
                "run_id",
                default_value="manual",
                description="Run identifier used when output is not overridden.",
            ),
            DeclareLaunchArgument(
                "output",
                default_value=[
                    "data/raw_rosbags/",
                    LaunchConfiguration("run_id"),
                ],
                description="Output bag directory.",
            ),
            DeclareLaunchArgument(
                "all_topics",
                default_value="false",
                description="Record every visible topic instead of configured topics.",
            ),
            OpaqueFunction(function=_record_process),
        ]
    )
