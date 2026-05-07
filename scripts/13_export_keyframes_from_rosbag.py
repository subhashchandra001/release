#!/usr/bin/env python3
"""Export sampled RGB keyframes from a ROS 2 bag.

Writes:
- data/processed/<run_id>/keyframes/kf_XXXXXX.png
- data/processed/<run_id>/keyframes.csv

Schema:
run_id,keyframe_id,timestamp,rgb_path,depth_path,x,y,z,qx,qy,qz,qw,yaw

Pose fields are left blank unless a later synchronization step is added.
This avoids fabricating image poses.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np
import rosbag2_py
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import Image


def open_reader(bag_dir: Path) -> rosbag2_py.SequentialReader:
    if not bag_dir.exists():
        raise FileNotFoundError(f"Bag directory does not exist: {bag_dir}")

    storage_options = rosbag2_py.StorageOptions(
        uri=str(bag_dir),
        storage_id="mcap",
    )
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr",
    )

    reader = rosbag2_py.SequentialReader()
    reader.open(storage_options, converter_options)
    return reader


def image_to_bgr(msg: Image) -> np.ndarray:
    height = int(msg.height)
    width = int(msg.width)
    encoding = msg.encoding.lower()

    if encoding in {"rgb8", "bgr8"}:
        arr = np.frombuffer(msg.data, dtype=np.uint8).reshape(height, width, 3)
        if encoding == "rgb8":
            return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        return arr

    if encoding in {"rgba8", "bgra8"}:
        arr = np.frombuffer(msg.data, dtype=np.uint8).reshape(height, width, 4)
        if encoding == "rgba8":
            return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        return cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)

    if encoding in {"mono8", "8uc1"}:
        arr = np.frombuffer(msg.data, dtype=np.uint8).reshape(height, width)
        return cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)

    raise RuntimeError(f"Unsupported image encoding: {msg.encoding!r}")


def export_keyframes(
    run_id: str,
    bag_dir: Path,
    output_dir: Path,
    output_csv: Path,
    topic: str,
    every_seconds: float,
    max_frames: int | None,
) -> int:
    reader = open_reader(bag_dir)
    topics = {t.name: t.type for t in reader.get_all_topics_and_types()}

    if topic not in topics:
        available = ", ".join(sorted(topics))
        raise RuntimeError(
            f"Topic {topic!r} not found in {bag_dir}. Available topics: {available}"
        )

    if topics[topic] != "sensor_msgs/msg/Image":
        raise RuntimeError(
            f"Topic {topic!r} has type {topics[topic]!r}, expected sensor_msgs/msg/Image"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    last_saved_stamp: float | None = None

    with output_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "run_id",
            "keyframe_id",
            "timestamp",
            "rgb_path",
            "depth_path",
            "x",
            "y",
            "z",
            "qx",
            "qy",
            "qz",
            "qw",
            "yaw",
        ])

        while reader.has_next():
            name, data, timestamp_ns = reader.read_next()
            if name != topic:
                continue

            msg = deserialize_message(data, Image)

            stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            if stamp == 0.0:
                stamp = timestamp_ns * 1e-9

            if last_saved_stamp is not None and (stamp - last_saved_stamp) < every_seconds:
                continue

            image_bgr = image_to_bgr(msg)

            keyframe_id = f"kf_{count:06d}"
            rgb_rel_path = f"keyframes/{keyframe_id}.png"
            rgb_abs_path = output_dir / f"{keyframe_id}.png"

            ok = cv2.imwrite(str(rgb_abs_path), image_bgr)
            if not ok:
                raise RuntimeError(f"Failed to write image: {rgb_abs_path}")

            writer.writerow([
                run_id,
                keyframe_id,
                f"{stamp:.9f}",
                rgb_rel_path,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ])

            count += 1
            last_saved_stamp = stamp

            if max_frames is not None and count >= max_frames:
                break

    if count == 0:
        raise RuntimeError(f"No keyframes exported from topic {topic!r} in {bag_dir}")

    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--bag-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--topic", default="/oakd/rgb/preview/image_raw")
    parser.add_argument("--every-seconds", type=float, default=2.0)
    parser.add_argument("--max-frames", type=int, default=120)
    args = parser.parse_args()

    max_frames = args.max_frames if args.max_frames > 0 else None

    count = export_keyframes(
        run_id=args.run_id,
        bag_dir=Path(args.bag_dir),
        output_dir=Path(args.output_dir),
        output_csv=Path(args.output_csv),
        topic=args.topic,
        every_seconds=args.every_seconds,
        max_frames=max_frames,
    )

    print(f"Exported {count} keyframes to {args.output_dir}")
    print(f"Wrote keyframe index to {args.output_csv}")


if __name__ == "__main__":
    main()
