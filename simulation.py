"""Turn-based drone simulation with 2-path routing."""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
from math import inf

from drone_graph import DroneGraph
from errors import PathNotFoundError
from utils import Color


ZONE_PRIORITY: dict[str, float] = {
    "priority": 0.8,
    "normal": 1.0,
    "restricted": 2.0,
    "blocked": inf,
}


@dataclass(slots=True)
class DroneState:
    """Runtime state for one drone."""

    name: str
    path: list[str]
    schedule: dict[int, str] = field(default_factory=dict)
    finished: bool = False


class SimulationEngine:
    """Assign 2 candidate paths to drones and replay schedules turn by turn."""

    def __init__(
        self,
        graph: DroneGraph,
        drones_count: int,
        start_hub: str,
        end_hub: str,
    ) -> None:
        """Initialize with graph and parameters."""
        self.graph: DroneGraph = graph
        self.start_hub: str = start_hub
        self.end_hub: str = end_hub
        self.drones: list[DroneState] = []
        self.current_turn: int = 0

        paths = self._build_two_paths()
        if not paths:
            raise PathNotFoundError(
                f"No path between '{start_hub}' and '{end_hub}'"
            )
        self._paths = paths
        self._assign_drones(drones_count)

    @staticmethod
    def _zone_cost(zone_type: str) -> float:
        """Get movement cost for a zone type."""
        return ZONE_PRIORITY.get(zone_type, 1.0)

    @staticmethod
    def _color_for_zone(color_name: str) -> str:
        """Return ANSI code for zone color."""
        if not color_name or color_name.lower() in {"none", "normal"}:
            return ""
        member = getattr(Color, color_name.upper(), None)
        return member.value if isinstance(member, Color) else ""

    def _path_cost(self, path: list[str]) -> float:
        """Total weighted cost of a path."""
        total = 0.0
        for zone_name in path[1:]:
            zone = self.graph.get_zone(zone_name)
            if zone is None:
                return inf
            total += self._zone_cost(zone.zone_type)
        return total

    def _shortest_path(self, start: str, end: str) -> list[str]:
        """Find shortest weighted path using Dijkstra+A*."""
        queue: list[tuple[float, str, list[str]]] = [(0.0, start, [start])]
        visited: dict[str, float] = {start: 0.0}

        while queue:
            cost, zone, path = heapq.heappop(queue)
            if zone == end:
                return path

            if cost > visited.get(zone, inf):
                continue

            for neighbor, _ in self.graph.get_neighbors(zone):
                if neighbor.zone_type == "blocked":
                    continue
                step_cost = self._zone_cost(neighbor.zone_type)
                new_cost = cost + step_cost
                if new_cost < visited.get(neighbor.name, inf):
                    visited[neighbor.name] = new_cost
                    heapq.heappush(
                        queue,
                        (new_cost, neighbor.name, path + [neighbor.name])
                    )

        return []

    def _alternative_path(
        self,
        start: str,
        end: str,
        forbidden: set[str] | None = None,
    ) -> list[str]:
        """Find a different path by avoiding some zones."""
        if forbidden is None:
            forbidden = set()

        queue: list[tuple[float, str, list[str]]] = [(0.0, start, [start])]
        visited: dict[str, float] = {start: 0.0}

        while queue:
            cost, zone, path = heapq.heappop(queue)
            if zone == end:
                return path

            if cost > visited.get(zone, inf):
                continue

            for neighbor, _ in self.graph.get_neighbors(zone):
                if (
                    neighbor.zone_type == "blocked"
                    or neighbor.name in forbidden
                ):
                    continue
                step_cost = self._zone_cost(neighbor.zone_type)
                new_cost = cost + step_cost
                if new_cost < visited.get(neighbor.name, inf):
                    visited[neighbor.name] = new_cost
                    heapq.heappush(
                        queue,
                        (
                            new_cost,
                            neighbor.name,
                            path + [neighbor.name],
                        ),
                    )

        return []

    def _build_two_paths(self) -> list[list[str]]:
        """Generate 2 candidate paths: shortest and alternative."""
        shortest = self._shortest_path(self.start_hub, self.end_hub)
        if not shortest:
            return []

        # Forbidden zones: exclude middle zones of shortest path
        forbidden = set(shortest[1:-1]) if len(shortest) > 2 else set()
        alternative = self._alternative_path(
            self.start_hub,
            self.end_hub,
            forbidden=forbidden,
        )

        if alternative and len(alternative) > 1:
            paths = sorted(
                [shortest, alternative],
                key=self._path_cost,
            )
            return paths

        return [shortest]

    def _try_reserve(
        self,
        path: list[str],
        offset: int = 0,
    ) -> dict[int, str] | None:
        """Try to reserve a path with offset. Returns schedule or None."""
        schedule: dict[int, str] = {}
        turn = offset
        current = path[0]

        for next_zone in path[1:]:
            zone_obj = self.graph.get_zone(next_zone)
            if zone_obj is None:
                return None

            cost = 2 if zone_obj.zone_type == "restricted" else 1
            arrival = turn + cost

            conn = self.graph.get_connection(current, next_zone)
            if conn is None:
                return None

            # Check capacity
            if not zone_obj.is_available_at(arrival, extra=1):
                return None

            # Check connection availability
            conn_turns = (
                [arrival - 1, arrival]
                if cost == 2
                else [arrival]
            )
            for t in conn_turns:
                if t >= 1 and not conn.is_available_at(t, extra=1):
                    return None

            # Reserve
            for t in conn_turns:
                if t >= 1:
                    conn.reserve_at(t, extra=1)
            zone_obj.reserve_at(arrival, extra=1)

            # Schedule
            if cost == 2:
                show_turn = max(1, arrival - 1)
                schedule[show_turn] = f"{current}-{next_zone}"
                schedule[arrival] = next_zone
            else:
                schedule[arrival] = next_zone

            turn = arrival
            current = next_zone

        return schedule if schedule else None

    def _assign_drones(self, count: int) -> None:
        """Assign drones to paths using sequential reservation."""
        for i in range(count):
            reserved = False
            for path in self._paths:
                max_offset = max(10, len(path) * 2 + i)
                for offset in range(0, max_offset + 1):
                    schedule = self._try_reserve(path, offset=offset)
                    if schedule:
                        drone = DroneState(
                            name=f"D{i + 1}",
                            path=path.copy(),
                            schedule=schedule,
                        )
                        self.drones.append(drone)
                        reserved = True
                        break
                if reserved:
                    break

            if not reserved:
                raise PathNotFoundError(
                    f"Failed to reserve path for D{i + 1}"
                )

    def _format_move(self, name: str, label: str) -> str:
        """Format a move with zone color if available."""
        zone_name = label.split("-", 1)[-1] if "-" in label else label
        zone = self.graph.get_zone(zone_name)
        if zone is None:
            return f"{name}-{label}"

        color = self._color_for_zone(zone.color)
        if not color:
            return f"{name}-{label}"
        return f"{name}-{color}{label}{Color.DEFAULT.value}"

    def _simulate_turn(self) -> list[str]:
        """Play one turn from all drone schedules."""
        self.current_turn += 1
        moves: list[str] = []

        for drone in self.drones:
            if drone.finished:
                continue

            action = drone.schedule.get(self.current_turn)
            if not action:
                continue

            moves.append(self._format_move(drone.name, action))

            if "-" not in action:
                if action == self.end_hub:
                    drone.finished = True

        return moves

    def run_simulation(self) -> None:
        """Run simulation until all drones finish."""
        while not all(d.finished for d in self.drones):
            events = self._simulate_turn()
            if events:
                print(" ".join(events))
