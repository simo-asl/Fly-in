"""Tests for the Fly-in simulation engine."""

import io
import re
import unittest
from contextlib import redirect_stdout

from drone_graph import DroneGraph
from errors import PathNotFoundError
from parser import Connection, Zone
from simulation import SimulationEngine


class SimulatorTests(unittest.TestCase):
    """Test routing, capacity, and movement behavior."""

    @staticmethod
    def _run(
        zones: list[Zone],
        connections: list[Connection],
        drones: int,
        start: str = "start",
        end: str = "goal",
    ) -> list[str]:
        """Run a simulation and return clean output lines."""
        graph = DroneGraph(zones, connections)
        engine = SimulationEngine(
            graph,
            drones,
            start,
            end,
        )

        output = io.StringIO()

        with redirect_stdout(output):
            engine.run_simulation()

        clean = re.sub(
            r"\x1b\[[0-9;]*m",
            "",
            output.getvalue(),
        )

        return [
            line
            for line in clean.splitlines()
            if line.strip()
        ]

    def test_all_drones_reach_goal(self) -> None:
        """Deliver every drone to the end zone."""
        lines = self._run(
            zones=[
                Zone("start", 0, 0),
                Zone("middle", 1, 0),
                Zone("goal", 2, 0),
            ],
            connections=[
                Connection("start", "middle"),
                Connection("middle", "goal"),
            ],
            drones=2,
        )

        output = " ".join(lines)

        self.assertIn("D1-goal", output)
        self.assertIn("D2-goal", output)

    def test_zone_capacity_is_respected(self) -> None:
        """Prevent two drones from entering a capacity-one zone."""
        lines = self._run(
            zones=[
                Zone("start", 0, 0),
                Zone(
                    "middle",
                    1,
                    0,
                    max_drones=1,
                ),
                Zone("goal", 2, 0),
            ],
            connections=[
                Connection("start", "middle"),
                Connection("middle", "goal"),
            ],
            drones=2,
        )

        middle_turns = [
            line
            for line in lines
            if "-middle" in line
        ]

        for line in middle_turns:
            arrivals = [
                movement
                for movement in line.split()
                if movement.endswith("-middle")
            ]
            self.assertLessEqual(len(arrivals), 1)

    def test_normal_connection_capacity_is_respected(
        self,
    ) -> None:
        """Limit normal-link traversal to its capacity."""
        lines = self._run(
            zones=[
                Zone("start", 0, 0),
                Zone("goal", 1, 0),
            ],
            connections=[
                Connection(
                    "start",
                    "goal",
                    max_link_capacity=1,
                )
            ],
            drones=2,
        )

        goal_turns = [
            line
            for line in lines
            if "-goal" in line
        ]

        self.assertEqual(len(goal_turns), 2)

        for line in goal_turns:
            arrivals = [
                movement
                for movement in line.split()
                if movement.endswith("-goal")
            ]
            self.assertEqual(len(arrivals), 1)

    def test_link_capacity_two_allows_two_drones(
        self,
    ) -> None:
        """Allow simultaneous traversal when link capacity is two."""
        lines = self._run(
            zones=[
                Zone("start", 0, 0),
                Zone("goal", 1, 0),
            ],
            connections=[
                Connection(
                    "start",
                    "goal",
                    max_link_capacity=2,
                )
            ],
            drones=2,
        )

        self.assertEqual(len(lines), 1)
        self.assertIn("D1-goal", lines[0])
        self.assertIn("D2-goal", lines[0])

    def test_restricted_zone_takes_two_turns(self) -> None:
        """Represent restricted movement using a transit turn."""
        lines = self._run(
            zones=[
                Zone("start", 0, 0),
                Zone(
                    "restricted",
                    1,
                    0,
                    zone_type="restricted",
                ),
                Zone("goal", 2, 0),
            ],
            connections=[
                Connection("start", "restricted"),
                Connection("restricted", "goal"),
            ],
            drones=1,
        )

        self.assertEqual(
            lines,
            [
                "D1-start-restricted",
                "D1-restricted",
                "D1-goal",
            ],
        )

    def test_blocked_zone_is_avoided(self) -> None:
        """Route drones without entering blocked zones."""
        lines = self._run(
            zones=[
                Zone("start", 0, 0),
                Zone(
                    "blocked",
                    1,
                    0,
                    zone_type="blocked",
                ),
                Zone("safe", 1, 1),
                Zone("goal", 2, 0),
            ],
            connections=[
                Connection("start", "blocked"),
                Connection("blocked", "goal"),
                Connection("start", "safe"),
                Connection("safe", "goal"),
            ],
            drones=1,
        )

        output = " ".join(lines)

        self.assertNotIn("D1-blocked", output)
        self.assertIn("D1-safe", output)
        self.assertIn("D1-goal", output)

    def test_missing_path_raises_error(self) -> None:
        """Raise an error when the end cannot be reached."""
        graph = DroneGraph(
            zones=[
                Zone("start", 0, 0),
                Zone("goal", 1, 0),
            ],
            connections=[],
        )
        engine = SimulationEngine(
            graph,
            drones_count=1,
            start_hub="start",
            end_hub="goal",
        )

        with self.assertRaises(PathNotFoundError):
            engine.run_simulation()


if __name__ == "__main__":
    unittest.main()
