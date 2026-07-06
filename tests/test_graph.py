import unittest

from parser import Parser
from drone_graph import DroneGraph


class GraphTests(unittest.TestCase):
    def test_neighbors_and_zone_lookup(self) -> None:
        p = Parser("maps/easy/01_linear_path.txt")
        p.parse()
        graph = DroneGraph(p.zone_declarations, p.connection_declarations)
        start_neighbors = graph.get_neighbors("start")
        neighbour_names = [n.name for n, _ in start_neighbors]
        self.assertIn("waypoint1", neighbour_names)
        z = graph.get_zone("waypoint1")
        assert z is not None
        self.assertEqual(z.x, 1)
        self.assertEqual(z.y, 0)


if __name__ == "__main__":
    unittest.main()
