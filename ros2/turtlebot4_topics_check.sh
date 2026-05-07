#!/usr/bin/env bash
set -euo pipefail

# TurtleBot4 topic names can differ across namespaces and sensor setups. This
# check reads configs/topics_turtlebot4.yaml; edit that file if any expected
# topic below is intentionally different on your robot.

usage() {
  cat <<'EOF'
Usage: ros2/turtlebot4_topics_check.sh [options]

Verify that the configured TurtleBot4 topics are currently visible in ROS 2.

Options:
  --config PATH          Experiment config (default: configs/experiment.yaml)
  --topics-config PATH   Topic config (default: configs/topics_turtlebot4.yaml)
  -h, --help             Show this help

Example:
  ros2/turtlebot4_topics_check.sh
EOF
}

config="configs/experiment.yaml"
topics_config="configs/topics_turtlebot4.yaml"

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

if [[ ! -f "$topics_config" ]]; then
  echo "Missing topics config: $topics_config" >&2
  exit 1
fi

if ! command -v ros2 >/dev/null 2>&1; then
  echo "ros2 command not found. Source your ROS 2 workspace before checking topics." >&2
  exit 1
fi

mapfile -t expected < <(
  python3 - "$topics_config" <<'PY'
import sys
import yaml

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}
topics = data.get("topics", {})
if not isinstance(topics, dict):
    raise SystemExit(f"{path}: expected a 'topics' mapping")
for name, value in topics.items():
    if value:
        print(f"{name}\t{value}")
PY
)

mapfile -t available < <(ros2 topic list)

missing=0
for item in "${expected[@]}"; do
  name="${item%%$'\t'*}"
  topic="${item#*$'\t'}"
  found=0
  for live_topic in "${available[@]}"; do
    if [[ "$live_topic" == "$topic" ]]; then
      found=1
      break
    fi
  done

  if [[ "$found" -eq 1 ]]; then
    printf '[ok]      %-12s %s\n' "$name" "$topic"
  else
    printf '[missing] %-12s %s\n' "$name" "$topic"
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo "One or more configured topics were not found. Edit $topics_config if your TurtleBot4 topic names differ." >&2
  exit 1
fi

echo "All configured TurtleBot4 topics are visible."
