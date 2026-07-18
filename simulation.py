from __future__ import annotations
import heapq
from dataclasses import dataclass

from drone_graph import DroneGraph
from errors import PathNotFoundError
from utils import Color


ZONE_PRIO: dict[str, int] = {
    "priority": 0,
    "normal": 1,
    "restricted": 2,
}


@dataclass(slots=True)
class Step:
    turn: int
    label: str
    zone: str | None = None
    is_link: bool = False
    src: str | None = None
    dst: str | None = None


class SimulationEngine:
    """Mananges the whole drone simulation"""
    def __init__(
        self,
        graph: DroneGraph,
        drones_count: int,
        start_hub: str,
        end_hub: str,
    ) -> None:
        """Store graph and simulation config"""
        self.graph: DroneGraph = graph
        self.start_hub: str = start_hub
        self.end_hub: str = end_hub
        self.drones_count: int = drones_count

        self.drone_paths: dict[str, list[Step]] = {}

    def _is_hub_free(self, zone: str, turn: int) -> bool:
        """Checking if the hub is free or not"""
        hub = self.graph.get_zone(zone)
        if hub is None:
            return False
        return hub.is_available_at(turn)

    def _is_link_free(self, src: str, dst: str, turn: int) -> bool:
        """Check if a connection between two hubs is availabe"""
        conn = self.graph.get_connection(src, dst)
        if conn is None:
            return False
        return conn.is_available_at(turn)

    def _can_execute_move(self, src: str, dst: str, turn: int) -> bool:
        """Deciding if a drone can move or not"""
        if not self._is_link_free(src, dst, turn + 1):
            return False

        next_zone = self.graph.get_zone(dst)
        if not next_zone:
            return False

        if next_zone.zone_type == "restricted":
            return (
                self._is_link_free(src, dst, turn + 2) and
                self._is_hub_free(dst, turn + 2)
            )
        return self._is_hub_free(dst, turn + 1)

    def _build_move_steps(
        self,
        src: str,
        dst: str,
        turn: int,
    ) -> list[Step]:
        """Create the steps required for a movement."""
        next_zone = self.graph.get_zone(dst)

        if next_zone is None:
            return []

        if next_zone.zone_type == "restricted":
            return [
                Step(
                    turn=turn + 1,
                    label=f"{src}-{dst}",
                    is_link=True,
                    src=src,
                    dst=dst,
                ),
                Step(
                    turn=turn + 2,
                    label=dst,
                    zone=dst,
                ),
            ]

        return [
            Step(
                turn=turn + 1,
                label=dst,
                zone=dst,
                src=src,
                dst=dst,
            )
        ]

    def _reserve_path(self, path: list[Step]) -> None:
        """Reserve all zones and connections used by a path."""
        for step in path:
            if step.src is not None and step.dst is not None:
                connection = self.graph.get_connection(
                    step.src,
                    step.dst,
                )

                if connection is None:
                    raise PathNotFoundError(
                        f"Missing connection: "
                        f"{step.src}-{step.dst}"
                    )

                connection.reserve_at(step.turn)

            if step.zone is not None:
                zone = self.graph.get_zone(step.zone)

                if zone is None:
                    raise PathNotFoundError(
                        f"Unknown zone: {step.zone}"
                    )

                zone.reserve_at(step.turn)

    def _find_path_for_drone(self, drone_idx: int) -> list[Step]:
        """Search for a valid path for one drone"""
        initial = Step(turn=0, label=self.start_hub, zone=self.start_hub)

        counter = 0
        heap = [(0, 0, counter, self.start_hub, [initial])]
        seen: set[tuple[str, int]] = set()

        while heap:
            turn, cost, _, zone, path = heapq.heappop(heap)

            if zone == self.end_hub:
                return path

            if (zone, turn) in seen:
                continue
            seen.add((zone, turn))

            for neighbor, _ in self.graph.get_neighbors(zone):
                dst = neighbor.name

                if dst in [s.zone for s in path if not s.is_link]:
                    continue

                if not self._can_execute_move(zone, dst, turn):
                    continue
                steps = self._build_move_steps(zone, dst, turn)
                arrival = steps[-1].turn

                prio_cost = ZONE_PRIO.get(neighbor.zone_type, 1)
                counter += 1
                heapq.heappush(heap, (
                    arrival, cost + prio_cost, counter, dst, path + steps))

            wait_turn = turn + 1
            if  self._is_hub_free(zone, wait_turn):
                counter += 1
                heapq.heappush(heap, (
                    wait_turn,
                    cost + 1,
                    counter,
                    zone,
                    path + [Step(turn=wait_turn, label=zone, zone=zone)]
                ))

        return []

    def _format_move(self, name: str, label: str) -> str:
        """Convert a movment into printable output"""
        zone_name = label.split("-", 1)[-1] if "-" in label else label
        zone = self.graph.get_zone(zone_name)
        if zone is None or zone.color.lower() in {"none", "normal"}:
            return f"{name}-{label}"
        member = getattr(Color, zone.color.upper(), None)
        color_code = member.value if isinstance(member, Color) else ""
        if not color_code:
            return f"{name}-{label}"
        return f"{name}-{color_code}{label}{Color.DEFAULT.value}"

    def run_simulation(self) -> None:
        """Replay the simulation turn by turn"""
        for i in range(1, self.drones_count + 1):
            drone_name = f"D{i}"
            path = self._find_path_for_drone(i)
            if not path:
                raise PathNotFoundError(f"No path found for {drone_name}")
            self._reserve_path(path)
            self.drone_paths[drone_name] = path

        max_turn = max(steps[-1].turn for steps in self.drone_paths.values())

        last_emitted_label = {
            f"D{i}": self.start_hub for i in range(1, self.drones_count + 1)
        }
        delivered_drones = set()

        for turn in range(1, max_turn + 1):
            turn_moves = []

            for i in range(1, self.drones_count + 1):
                drone_name = f"D{i}"
                if drone_name in delivered_drones:
                    continue

                for step in self.drone_paths[drone_name]:
                    if step.turn != turn:
                        continue
                    if step.label == last_emitted_label[drone_name]:
                        break

                    last_emitted_label[drone_name] = step.label
                    turn_moves.append(
                        self._format_move(drone_name, step.label))

                    if not step.is_link and step.zone == self.end_hub:
                        delivered_drones.add(drone_name)
                    break

            if turn_moves:
                print(" ".join(turn_moves))
