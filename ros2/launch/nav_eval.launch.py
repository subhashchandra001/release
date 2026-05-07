"""Launch Nav2 against a saved map for PrivateMap-Bench utility evaluation."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _optional_bag_play(context, *_args, **_kwargs):
    bag = LaunchConfiguration("bag").perform(context)
    if not bag:
        return []
    cmd = ["ros2", "bag", "play", bag, "--clock"]
    return [ExecuteProcess(cmd=cmd, output="screen")]


def generate_launch_description():
    nav2_launch = Path(get_package_share_directory("nav2_bringup")) / "launch" / "bringup_launch.py"

    # Nav2 consumes map and TF topics. If your TurtleBot4 topics differ from
    # configs/topics_turtlebot4.yaml, update that config before collecting bags
    # and keep remaps consistent in your local Nav2 parameter file.
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(nav2_launch)),
        launch_arguments={
            "map": LaunchConfiguration("map"),
            "params_file": LaunchConfiguration("params_file"),
            "use_sim_time": LaunchConfiguration("use_sim_time"),
        }.items(),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "map",
                default_value="data/maps/map.yaml",
                description="Saved occupancy map YAML to load in Nav2.",
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value="",
                description="Nav2 params file. Pass a TurtleBot4-specific file for real runs.",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Use /clock, recommended when evaluating from bag playback.",
            ),
            DeclareLaunchArgument(
                "bag",
                default_value="",
                description="Optional bag path to play with --clock.",
            ),
            nav2,
            OpaqueFunction(function=_optional_bag_play),
        ]
    )
