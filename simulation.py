import heapq
from drone_graph import DroneGraph


ZONE_PRIORITY: dict[str, float] = {
    "priority": 0.9,
    "normal": 1.0,
    "restricted": 2.0,
    "blocked": float("inf")
}


class DroneSimulationState:
    def __init__(self, name: str, path: list[str]) -> None:
        """Initialize the DroneSimulationState with a name and path."""
        self.name: str = name
        self.path: list[str] = path
        self.current_zone_index: int = 0
        self.transit_turns_left: int = 0
        self.is_finished: bool = False


class SimulationEngine:
    def __init__(self, graph: DroneGraph, drones_count: int,
                 start_hub: str, end_hub: str) -> None:
        """Initialize the SimulationEngine with a graph,
            drone count, start hub, and end hub."""
        self.graph: DroneGraph = graph
        self.start_hub = start_hub
        self.end_hub = end_hub
        self.drones: list[DroneSimulationState] = []
        self.traffic_penalty: dict[str, float] = {}
        self._assign_paths_to_drones(drones_count)

    def _assign_paths_to_drones(self, drones_count: int) -> None:
        """Assign paths to drones based on the shortest path."""
        for i in range(drones_count):
            path = self._find_shortest_path(self.start_hub, self.end_hub)
            if path:
                drone_state = DroneSimulationState(f"D{i+1}", path)
                self.drones.append(drone_state)

                for zone_name in path:
                    if zone_name != self.start_hub and \
                          zone_name != self.end_hub:
                        self.traffic_penalty[zone_name] = \
                            self.traffic_penalty.get(zone_name, 0) + 1.5
                    else:
                        pass

    def _find_shortest_path(self, start: str, end: str) -> list[str]:
        """Find the shortest path from start to end ."""
        queue: list[tuple[float, str, list[str]]] = [(0.0, start, [start])]
        distances: dict[str, float] = {start: 0.0}

        while queue:
            current_cost, current_zone, path = heapq.heappop(queue)
            if current_zone == end:
                return path
            if current_cost > distances.get(current_zone, float('inf')):
                continue

            for neighbor_zone, connection in self.graph.get_neighbors(
                    current_zone):
                zone_type = neighbor_zone.zone_type
                base_weight = ZONE_PRIORITY.get(zone_type, 1.0)

                penalty = self.traffic_penalty.get(neighbor_zone.name, 0.0)
                # bug STR -> OBJ = CRASH, will fix it later, FIXED
                total_weight = base_weight + penalty
                new_cost = current_cost + total_weight

                if new_cost < distances.get(neighbor_zone.name, float('inf')):
                    distances[neighbor_zone.name] = new_cost
                    heapq.heappush(queue, (
                        new_cost, neighbor_zone, path + [neighbor_zone]))

        return []

    def _simulation_turn(self) -> str:
        """Simulate a single turn of the simulation."""
        moves_this_turn: list[str] = []
        self.graph.reset_link_capacities()

        return " ".join(moves_this_turn)

    def run_simulation(self) -> None:
        """Run the simulation until all drones reach the end hub."""
        turn = 1
        # Method for testing our logic
        while not all(drone.is_finished for drone in self.drones):
            turn_output = self._simulate_turn()
            if turn_output:
                print(f"T{turn}: {turn_output}")
            turn += 1
