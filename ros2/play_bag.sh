#!/usr/bin/env bash
set -euo pipefail

# Playback uses the topics stored in the bag. If your TurtleBot4 topics differ
# from configs/topics_turtlebot4.yaml, update that config before recording so
# downstream export scripts see the expected topic names.

usage() {
  cat <<'EOF'
Usage: ros2/play_bag.sh BAG_PATH [options]

Play a ROS 2 bag for offline export, SLAM replay, or navigation evaluation.

Options:
  --config PATH       Experiment config (default: configs/experiment.yaml)
  --rate FLOAT        Playback rate (default: 1.0)
  --clock             Publish /clock during playback (recommended for replay)
  --loop              Loop playback
  --start-paused      Start paused
  -h, --help          Show this help

Example:
  ros2/play_bag.sh data/raw_rosbags/tb4_run_001 --clock
EOF
}

config="configs/experiment.yaml"
rate="1.0"
clock=0
loop=0
start_paused=0
bag_path=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      config="${2:?missing value for --config}"
      shift 2
      ;;
    --rate)
      rate="${2:?missing value for --rate}"
      shift 2
      ;;
    --clock)
      clock=1
      shift
      ;;
    --loop)
      loop=1
      shift
      ;;
    --start-paused)
      start_paused=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$bag_path" ]]; then
        bag_path="$1"
        shift
      else
        echo "Unexpected argument: $1" >&2
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

if [[ -z "$bag_path" ]]; then
  echo "Missing BAG_PATH" >&2
  usage >&2
  exit 2
fi

if [[ ! -e "$bag_path" ]]; then
  echo "Bag path does not exist: $bag_path" >&2
  exit 1
fi

if ! command -v ros2 >/dev/null 2>&1; then
  echo "ros2 command not found. Source your ROS 2 workspace before playback." >&2
  exit 1
fi

cmd=(ros2 bag play "$bag_path" --rate "$rate")
if [[ "$clock" -eq 1 ]]; then
  cmd+=(--clock)
fi
if [[ "$loop" -eq 1 ]]; then
  cmd+=(--loop)
fi
if [[ "$start_paused" -eq 1 ]]; then
  cmd+=(--start-paused)
fi

echo "Playing ROS 2 bag: $bag_path"
exec "${cmd[@]}"
