#!/usr/bin/env bash
set -euo pipefail

# The default map topic comes from configs/topics_turtlebot4.yaml. Edit that
# file or pass --map-topic if your TurtleBot4 publishes the map elsewhere.

usage() {
  cat <<'EOF'
Usage: ros2/save_map.sh [options]

Save the current Nav2/SLAM occupancy map as <output>.yaml and <output>.pgm.

Options:
  --config PATH          Experiment config (default: configs/experiment.yaml)
  --topics-config PATH   Topic config (default: configs/topics_turtlebot4.yaml)
  --output PREFIX        Output map prefix (default: data/maps/map)
  --map-topic TOPIC      Map topic override (default from topics config)
  -h, --help             Show this help

Example:
  ros2/save_map.sh --output data/maps/tb4_run_001_map
EOF
}

config="configs/experiment.yaml"
topics_config="configs/topics_turtlebot4.yaml"
output="data/maps/map"
map_topic=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      config="${2:?missing value for --config}"
      shift 2
      ;;
    --topics-config)
      topics_config="${2:?missing value for --topics-config}"
      shift 2
      ;;
    --output|-o)
      output="${2:?missing value for --output}"
      shift 2
      ;;
    --map-topic)
      map_topic="${2:?missing value for --map-topic}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "$config" ]]; then
  echo "Missing experiment config: $config" >&2
  exit 1
fi

if [[ -z "$map_topic" ]]; then
  if [[ ! -f "$topics_config" ]]; then
    echo "Missing topics config: $topics_config" >&2
    exit 1
  fi
  map_topic="$(
    python3 - "$topics_config" <<'PY'
import sys
import yaml

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}
print((data.get("topics", {}) or {}).get("map", "/map"))
PY
  )"
fi

if ! command -v ros2 >/dev/null 2>&1; then
  echo "ros2 command not found. Source your ROS 2 workspace before saving a map." >&2
  exit 1
fi

mkdir -p "$(dirname "$output")"

echo "Saving map from topic $map_topic to ${output}.yaml / ${output}.pgm"
exec ros2 run nav2_map_server map_saver_cli -f "$output" --ros-args -r map:="$map_topic"
