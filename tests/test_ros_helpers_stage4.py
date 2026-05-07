import stat
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_ros_shell_helpers_are_executable_and_document_topic_config():
    scripts = [
        ROOT / "ros2" / "record_bag.sh",
        ROOT / "ros2" / "play_bag.sh",
        ROOT / "ros2" / "save_map.sh",
        ROOT / "ros2" / "turtlebot4_topics_check.sh",
    ]

    for script in scripts:
        mode = script.stat().st_mode
        assert mode & stat.S_IXUSR, f"{script} is not executable"
        text = script.read_text(encoding="utf-8")
        assert "configs/topics_turtlebot4.yaml" in text


def test_ros_stage4_yaml_files_parse_without_ros():
    topics = yaml.safe_load(
        (ROOT / "configs" / "topics_turtlebot4.yaml").read_text(encoding="utf-8")
    )
    waypoints = yaml.safe_load(
        (ROOT / "ros2" / "nav2_waypoints_example.yaml").read_text(encoding="utf-8")
    )

    assert "topics" in topics
    assert topics["topics"]["scan"] == "/scan"
    assert waypoints["frame_id"] == "map"
    assert len(waypoints["waypoints"]) >= 2


def test_ros_launch_files_exist_without_importing_ros():
    launch_dir = ROOT / "ros2" / "launch"
    for name in ["record_privatemap.launch.py", "nav_eval.launch.py"]:
        text = (launch_dir / name).read_text(encoding="utf-8")
        assert "generate_launch_description" in text
