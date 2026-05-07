#!/usr/bin/env python3
"""Export trajectory.csv from a ROS 2 bag /odom topic.

Writes schema:
run_id,timestamp,x,y,z,qx,qy,qz,qw,yaw
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import rosbag2_py
from nav_msgs.msg import Odometry
from rclpy.serialization import deserialize_message


def yaw_from_quaternion(x: float, y: float, z: float, w: float) -> float:
    """Return yaw angle in radians from quaternion."""
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


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


def export_odom(
    run_id: str,
    bag_dir: Path,
    output_csv: Path,
    topic: str = "/odom",
) -> int:
    reader = open_reader(bag_dir)

    topics = {
        t.name: t.type
        for t in reader.get_all_topics_and_types()
    }

    if topic not in topics:
        available = ", ".join(sorted(topics))
        raise RuntimeError(
            f"Topic {topic!r} not found in {bag_dir}. Available topics: {available}"
        )

    if topics[topic] != "nav_msgs/msg/Odometry":
        raise RuntimeError(
            f"Topic {topic!r} has type {topics[topic]!r}, expected nav_msgs/msg/Odometry"
        )

    output_csv.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with output_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["run_id", "timestamp", "x", "y", "z", "qx", "qy", "qz", "qw", "yaw"])

        while reader.has_next():
            name, data, timestamp_ns = reader.read_next()
            if name != topic:
                continue

            msg = deserialize_message(data, Odometry)

            p = msg.pose.pose.position
            q = msg.pose.pose.orientation
            yaw = yaw_from_quaternion(q.x, q.y, q.z, q.w)

            # Prefer the message header stamp when available; fallback to bag timestamp.
            stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            if stamp == 0.0:
                stamp = timestamp_ns * 1e-9

            writer.writerow([
                run_id,
                f"{stamp:.9f}",
                f"{p.x:.9f}",
                f"{p.y:.9f}",
                f"{p.z:.9f}",
                f"{q.x:.9f}",
                f"{q.y:.9f}",
                f"{q.z:.9f}",
                f"{q.w:.9f}",
                f"{yaw:.9f}",
            ])
            count += 1

    if count == 0:
        raise RuntimeError(f"No messages found for topic {topic!r} in {bag_dir}")

    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--bag-dir", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--topic", default="/odom")
    args = parser.parse_args()

    count = export_odom(
        run_id=args.run_id,
        bag_dir=Path(args.bag_dir),
        output_csv=Path(args.output_csv),
        topic=args.topic,
    )

    print(f"Exported {count} odometry rows to {args.output_csv}")


if __name__ == "__main__":
    main()
