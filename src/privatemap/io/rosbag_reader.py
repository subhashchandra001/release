"""Safe ROS bag reader facade.

The benchmark repository supports offline artifacts without requiring ROS 2 to
be installed. Direct ROS bag parsing depends on the ROS 2 Python stack and is
therefore exposed as a guarded wrapper with clear errors.
"""

from __future__ import annotations

from pathlib import Path


class RosbagReaderError(RuntimeError):
    """Raised when ROS bag reading is unavailable or misconfigured."""


def require_rosbag2_py():
    """Return the ``rosbag2_py`` module or raise a helpful error."""

    try:
        import rosbag2_py  # type: ignore
    except ImportError as exc:
        raise RosbagReaderError(
            "ROS bag parsing requires ROS 2 and rosbag2_py. Source your ROS 2 "
            "environment or export artifacts outside this Python environment."
        ) from exc
    return rosbag2_py


def assert_rosbag_exists(path: str | Path) -> Path:
    """Validate that a bag path exists before any parser is invoked."""

    bag_path = Path(path)
    if not bag_path.exists():
        raise RosbagReaderError(f"ROS bag path does not exist: {bag_path}")
    return bag_path


def index_rosbag(path: str | Path) -> dict[str, object]:
    """Placeholder for future ROS bag indexing.

    This function intentionally does not fabricate metadata. It validates the
    dependency and input path, then fails with an implementation error until a
    real ROS 2 reader is added.
    """

    assert_rosbag_exists(path)
    require_rosbag2_py()
    raise NotImplementedError(
        "ROS bag indexing is not implemented yet. Use pre-exported artifacts "
        "under data/processed/<run_id>/ for offline benchmark stages."
    )
