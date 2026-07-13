"""Tests for the Fly-in graph."""

import unittest

from drone_graph import DroneGraph
from parser import Connection, Zone


class GraphTests(unittest.TestCase):
    """Test graph construction and lookup operations."""

    def setUp(self) -> None:
        """Create a small graph for each test."""
        self.start = Zone("start", 0, 0)
        self.middle = Zone("middle", 1, 0)
        self.goal = Zone("goal", 2, 0)
        self.blocked = Zone(
            "blocked",
            1,
            1,
            zone_type="blocked",
        )

        self.start_middle = Connection(
            "start",
            "middle",
        )
        self.middle_goal = Connection(
            "middle",
            "goal",
            max_link_capacity=2,
        )
        self.middle_blocked = Connection(
            "middle",
            "blocked",
        )

        self.graph = DroneGraph(
            [
                self.start,
                self.middle,
                self.goal,
                self.blocked,
            ],
            [
                self.start_middle,
                self.middle_goal,
                self.middle_blocked,
            ],
        )

    def test_zone_lookup(self) -> None:
        """Find a zone by name."""
        self.assertIs(
            self.graph.get_zone("middle"),
            self.middle,
        )

    def test_unknown_zone_returns_none(self) -> None:
        """Return None for an unknown zone."""
        self.assertIsNone(
            self.graph.get_zone("missing")
        )

    def test_connection_lookup_is_bidirectional(self) -> None:
        """Find the same connection in both directions."""
        forward = self.graph.get_connection(
            "middle",
            "goal",
        )
        backward = self.graph.get_connection(
            "goal",
            "middle",
        )

        self.assertIs(forward, self.middle_goal)
        self.assertIs(backward, self.middle_goal)

    def test_unknown_connection_returns_none(self) -> None:
        """Return None when zones are not connected."""
        self.assertIsNone(
            self.graph.get_connection("start", "goal")
        )

    def test_neighbors_are_bidirectional(self) -> None:
        """Expose regular connections in both directions."""
        start_neighbors = {
            zone.name
            for zone, _ in self.graph.get_neighbors("start")
        }
        middle_neighbors = {
            zone.name
            for zone, _ in self.graph.get_neighbors("middle")
        }

        self.assertEqual(start_neighbors, {"middle"})
        self.assertIn("start", middle_neighbors)
        self.assertIn("goal", middle_neighbors)

    def test_blocked_zone_is_not_reachable(self) -> None:
        """Prevent movement into blocked zones."""
        middle_neighbors = {
            zone.name
            for zone, _ in self.graph.get_neighbors("middle")
        }

        self.assertNotIn("blocked", middle_neighbors)

    def test_connection_capacity_is_preserved(self) -> None:
        """Keep capacity metadata in the graph."""
        connection = self.graph.get_connection(
            "middle",
            "goal",
        )

        self.assertIsNotNone(connection)
        assert connection is not None

        self.assertEqual(
            connection.max_link_capacity,
            2,
        )


if __name__ == "__main__":
    unittest.main()
