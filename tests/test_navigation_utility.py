from __future__ import annotations

import numpy as np
import pytest

from privatemap.utility.navigation_utility import NavigationUtilityError, astar_plan


def test_astar_plan_finds_path_around_obstacle() -> None:
    grid = np.array(
        [
            [0, 0, 0, 0],
            [0, 100, 100, 0],
            [0, 0, 0, 0],
        ],
        dtype=np.int8,
    )

    plan = astar_plan(grid, (0, 0), (0, 3))

    assert plan.success
    assert plan.path[0] == (0, 0)
    assert plan.path[-1] == (0, 3)
    assert all(grid[cell] == 0 for cell in plan.path)
    assert plan.cost == 3.0


def test_astar_plan_reports_unreachable_goal() -> None:
    grid = np.array([[0, 100, 0]], dtype=np.int8)

    plan = astar_plan(grid, (0, 0), (0, 2))

    assert not plan.success
    assert plan.cost == float("inf")


def test_astar_plan_rejects_blocked_start() -> None:
    with pytest.raises(NavigationUtilityError, match="start cell"):
        astar_plan(np.array([[100, 0]], dtype=np.int8), (0, 0), (0, 1))
