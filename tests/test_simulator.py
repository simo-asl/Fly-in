import io
import re
import unittest
from contextlib import redirect_stdout

from parser import Parser
from drone_graph import DroneGraph
from simulation import SimulationEngine


class SimulatorTests(unittest.TestCase):
    def test_simulation_finishes(self) -> None:
        p = Parser("maps/easy/01_linear_path.txt")
        p.parse()
        graph = DroneGraph(p.zone_declarations, p.connection_declarations)
        engine = SimulationEngine(graph, p.nb_drones, p.start_hub, p.end_hub)

        buf = io.StringIO()
        with redirect_stdout(buf):
            engine.run_simulation()

        output = buf.getvalue()
        # Strip ANSI codes to check for zone names
        clean = re.sub(r"\x1b\[[0-9;]*m", "", output)
        self.assertIn("D1-goal", clean)
        self.assertIn("D2-goal", clean)


if __name__ == "__main__":
    unittest.main()
