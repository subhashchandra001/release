#!/usr/bin/env bash
set -euo pipefail

# TurtleBot4 topic names vary by image, namespace, and sensor configuration.
# This script reads configs/topics_turtlebot4.yaml by default; edit that file
# or pass --topics-config if your robot publishes different topic names.

usage() {
  cat <<'EOF'
Usage: ros2/record_bag.sh [options]
       ros2/record_bag.sh RUN_ID

Record the configured TurtleBot4 topics to a ROS 2 bag.

Options:
  --config PATH          Experiment config (default: configs/experiment.yaml)
  --topics-config PATH   Topic config (default: configs/topics_turtlebot4.yaml)
  --run-id NAME          Run id used in the output bag name (default: manual)
  --output PATH          Output bag directory (default: data/raw_rosbags/<run-id>_<timestamp>)
  --all                  Record all topics instead of the configured topic set
  -h, --help             Show this help

Example:
  ros2/record_bag.sh --run-id tb4_run_001
  ros2/record_bag.sh run_test_30s
EOF
}

config="configs/experiment.yaml"
topics_config="configs/topics_turtlebot4.yaml"
run_id="manual"
output=""
record_all=0

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
    --run-id)
      run_id="${2:?missing value for --run-id}"
      shift 2
      ;;
    --output|-o)
      output="${2:?missing value for --output}"
      shift 2
      ;;
    --all)
      record_all=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ "$run_id" == "manual" && -z "$output" && "$1" != -* ]]; then
        run_id="$1"
        output="data/raw_rosbags/$run_id"
        shift
      else
        echo "Unknown argument: $1" >&2
        usage >&2
        exit 2
      fi
      ;;
  esac
done

if [[ ! -f "$config" ]]; then
  echo "Missing experiment config: $config" >&2
  exit 1
fi

if ! command -v ros2 >/dev/null 2>&1; then
  echo "ros2 command not found. Source your ROS 2 workspace before recording." >&2
  exit 1
fi

if [[ -z "$output" ]]; then
  timestamp="$(date +%Y%m%d_%H%M%S)"
  output="data/raw_rosbags/${run_id}_${timestamp}"
fi

mkdir -p "$(dirname "$output")"

if [[ "$record_all" -eq 1 ]]; then
  echo "Recording all ROS 2 topics to $output"
  exec ros2 bag record -a -o "$output"
fi

if [[ ! -f "$topics_config" ]]; then
  echo "Missing topics config: $topics_config" >&2
  exit 1
fi

mapfile -t topics < <(
  python3 - "$topics_config" <<'PY'
import sys
import yaml

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}
topics = data.get("topics", {})
if not isinstance(topics, dict):
    raise SystemExit(f"{path}: expected a 'topics' mapping")
for value in topics.values():
    if value:
        print(value)
PY
)

if [[ "${#topics[@]}" -eq 0 ]]; then
  echo "No topics found in $topics_config" >&2
  exit 1
fi

echo "Recording configured TurtleBot4 topics to $output"
printf '  %s\n' "${topics[@]}"
exec ros2 bag record -o "$output" "${topics[@]}"
