import heapq
from collections import Counter
from dataclasses import dataclass, field

from drone_graph import DroneGraph
from errors import PathNotFoundError
from utils import Color, normalize_pair


ZONE_PRIO: dict[str, int] = {
    "priority": 0,
    "normal": 1,
    "restricted": 2,
}


@dataclass(slots=True)
class Step:
    """Represent either a drone's current state or one completed move."""

    turn: int
    label: str
    zone: str | None = None
    is_link: bool = False
    src: str | None = None
    dst: str | None = None
    arrival_turn: int | None = None
    visited: set[str] = field(default_factory=set)


class SimulationEngine:
    """Route and move drones using live turn-by-turn capacity checks."""

    def __init__(
        self,
        graph: DroneGraph,
        drones_count: int,
        start_hub: str,
        end_hub: str,
    ) -> None:
        """Store the graph and simulation configuration."""
        self.graph = graph
        self.start_hub = start_hub
        self.end_hub = end_hub
        self.drones_count = drones_count

        self.drone_steps: dict[str, Step] = {}

    @staticmethod
    def _movement_cost(zone_type: str) -> int:
        """Return the number of turns needed to enter a zone."""
        return 2 if zone_type == "restricted" else 1

    def _is_terminal(self, zone_name: str) -> bool:
        """Return whether a zone has unlimited occupancy."""
        return zone_name in {self.start_hub, self.end_hub}

    def _path_cost(
        self,
        start: str,
        forbidden: set[str],
    ) -> tuple[int, int] | None:
        """Return the best turn and priority cost from start to end."""
        if start == self.end_hub:
            return (0, 0)

        counter = 0
        heap: list[tuple[int, int, int, str]] = [
            (0, 0, counter, start)
        ]
        best: dict[str, tuple[int, int]] = {}

        while heap:
            turns, priority, _, zone_name = heapq.heappop(heap)
            current_cost = (turns, priority)

            if zone_name in best and best[zone_name] <= current_cost:
                continue
            best[zone_name] = current_cost

            if zone_name == self.end_hub:
                return current_cost

            for neighbor, _ in self.graph.get_neighbors(zone_name):
                if (
                    neighbor.name in forbidden
                    and neighbor.name != self.end_hub
                ):
                    continue

                next_turns = turns + self._movement_cost(
                    neighbor.zone_type
                )
                next_priority = priority + ZONE_PRIO.get(
                    neighbor.zone_type,
                    1,
                )
                counter += 1
                heapq.heappush(
                    heap,
                    (
                        next_turns,
                        next_priority,
                        counter,
                        neighbor.name,
                    ),
                )

        return None

    def _candidate_destinations(
        self,
        state: Step,
        occupancy: Counter[str],
        next_arrivals: Counter[str],
    ) -> list[str]:
        """Return safe next zones ordered by route cost and congestion."""
        if state.zone is None:
            return []

        candidates: list[tuple[int, int, int, int, str]] = []

        for neighbor, _ in self.graph.get_neighbors(state.zone):
            dst = neighbor.name

            if dst in state.visited and dst != self.end_hub:
                continue

            forbidden = set(state.visited)
            forbidden.add(state.zone)
            forbidden.discard(dst)
            forbidden.discard(self.end_hub)

            remaining = self._path_cost(dst, forbidden)
            if remaining is None:
                continue

            total_turns = (
                self._movement_cost(neighbor.zone_type)
                + remaining[0]
            )
            total_priority = (
                ZONE_PRIO.get(neighbor.zone_type, 1)
                + remaining[1]
            )
            congestion = occupancy[dst] + next_arrivals[dst]

            candidates.append(
                (
                    total_turns,
                    total_priority,
                    congestion,
                    ZONE_PRIO.get(neighbor.zone_type, 1),
                    dst,
                )
            )

        candidates.sort()
        return [candidate[4] for candidate in candidates]

    def _drone_order_key(self, drone_name: str) -> tuple[int, int, int]:
        """Move drones nearest to the end before upstream drones."""
        state = self.drone_steps[drone_name]
        drone_number = int(drone_name[1:])

        if state.zone is None:
            return (10**9, 10**9, drone_number)

        forbidden = set(state.visited)
        forbidden.discard(state.zone)
        remaining = self._path_cost(state.zone, forbidden)

        if remaining is None:
            return (10**9, 10**9, drone_number)

        return (remaining[0], remaining[1], drone_number)

    def _has_zone_capacity(
        self,
        zone_name: str,
        occupancy: Counter[str],
        next_arrivals: Counter[str],
    ) -> bool:
        """Check live occupancy and already-guaranteed next arrivals."""
        if self._is_terminal(zone_name):
            return True

        zone = self.graph.get_zone(zone_name)
        if zone is None:
            return False

        return (
            occupancy[zone_name] + next_arrivals[zone_name]
            < zone.max_drones
        )

    def _has_link_capacity(
        self,
        src: str,
        dst: str,
        link_usage: Counter[tuple[str, str]],
    ) -> bool:
        """Check the connection capacity for the current turn."""
        connection = self.graph.get_connection(src, dst)
        if connection is None:
            return False

        pair = normalize_pair(src, dst)
        return link_usage[pair] < connection.max_link_capacity

    def _initialize_drones(self) -> None:
        """Place every drone at the unlimited start hub."""
        for drone_index in range(1, self.drones_count + 1):
            drone_name = f"D{drone_index}"
            self.drone_steps[drone_name] = Step(
                turn=0,
                label=self.start_hub,
                zone=self.start_hub,
                visited={self.start_hub},
            )

    def _current_occupancy(self, delivered: set[str]) -> Counter[str]:
        """Count drones currently occupying limited hubs."""
        occupancy: Counter[str] = Counter()

        for drone_name, state in self.drone_steps.items():
            if drone_name in delivered or state.zone is None:
                continue
            if not self._is_terminal(state.zone):
                occupancy[state.zone] += 1

        return occupancy

    def _process_arrivals(
        self,
        turn: int,
        delivered: set[str],
        occupancy: Counter[str],
        turn_moves: list[str],
    ) -> set[str]:
        """Complete every mandatory restricted-zone arrival."""
        arrived: set[str] = set()

        for drone_name in sorted(
            self.drone_steps,
            key=lambda name: int(name[1:]),
        ):
            state = self.drone_steps[drone_name]

            if not state.is_link or state.arrival_turn != turn:
                continue
            if state.dst is None:
                raise PathNotFoundError(
                    f"Invalid transit state for {drone_name}"
                )

            dst = state.dst
            zone = self.graph.get_zone(dst)
            if zone is None:
                raise PathNotFoundError(f"Unknown zone: {dst}")

            if (
                not self._is_terminal(dst)
                and occupancy[dst] >= zone.max_drones
            ):
                raise PathNotFoundError(
                    f"No arrival capacity for {drone_name} at {dst}"
                )

            state.turn = turn
            state.label = dst
            state.zone = dst
            state.is_link = False
            state.src = None
            state.dst = None
            state.arrival_turn = None
            state.visited.add(dst)

            if not self._is_terminal(dst):
                occupancy[dst] += 1

            turn_moves.append(self._format_move(drone_name, dst))
            arrived.add(drone_name)

            if dst == self.end_hub:
                delivered.add(drone_name)

        return arrived

    def _execute_move(
        self,
        drone_name: str,
        dst: str,
        turn: int,
        occupancy: Counter[str],
        next_arrivals: Counter[str],
        link_usage: Counter[tuple[str, str]],
        delivered: set[str],
        turn_moves: list[str],
    ) -> None:
        """Execute one already-validated normal or restricted move."""
        state = self.drone_steps[drone_name]
        src = state.zone

        if src is None:
            raise PathNotFoundError(
                f"Cannot move in-transit drone {drone_name}"
            )

        destination = self.graph.get_zone(dst)
        if destination is None:
            raise PathNotFoundError(f"Unknown zone: {dst}")

        pair = normalize_pair(src, dst)
        link_usage[pair] += 1

        if not self._is_terminal(src):
            occupancy[src] -= 1

        state.turn = turn
        state.src = src
        state.dst = dst

        if destination.zone_type == "restricted":
            label = f"{src}-{dst}"
            state.label = label
            state.zone = None
            state.is_link = True
            state.arrival_turn = turn + 1
            next_arrivals[dst] += 1

            turn_moves.append(self._format_move(drone_name, label))
            return

        state.label = dst
        state.zone = dst
        state.is_link = False
        state.arrival_turn = None
        state.visited.add(dst)

        if not self._is_terminal(dst):
            occupancy[dst] += 1

        turn_moves.append(self._format_move(drone_name, dst))

        if dst == self.end_hub:
            delivered.add(drone_name)

    def _format_move(self, name: str, label: str) -> str:
        """Convert one movement into the required printable output."""
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
        """Move all drones using live state and capacity decisions."""
        if self._path_cost(self.start_hub, set()) is None:
            raise PathNotFoundError(
                f"No path from {self.start_hub} to {self.end_hub}"
            )

        self._initialize_drones()
        delivered: set[str] = set()
        arrival_reservations: dict[int, Counter[str]] = {}
        turn = 0

        while len(delivered) < self.drones_count:
            turn += 1
            turn_moves: list[str] = []
            link_usage: Counter[tuple[str, str]] = Counter()
            occupancy = self._current_occupancy(delivered)

            arrival_reservations.pop(turn, None)
            arrived = self._process_arrivals(
                turn,
                delivered,
                occupancy,
                turn_moves,
            )
            next_arrivals = arrival_reservations.setdefault(
                turn + 1,
                Counter(),
            )

            movable = [
                drone_name
                for drone_name, state in self.drone_steps.items()
                if (
                    drone_name not in delivered
                    and drone_name not in arrived
                    and not state.is_link
                )
            ]
            movable.sort(key=self._drone_order_key)

            for drone_name in movable:
                state = self.drone_steps[drone_name]
                if state.zone is None:
                    continue

                for dst in self._candidate_destinations(
                    state,
                    occupancy,
                    next_arrivals,
                ):
                    if not self._has_link_capacity(
                        state.zone,
                        dst,
                        link_usage,
                    ):
                        continue
                    if not self._has_zone_capacity(
                        dst,
                        occupancy,
                        next_arrivals,
                    ):
                        continue

                    self._execute_move(
                        drone_name,
                        dst,
                        turn,
                        occupancy,
                        next_arrivals,
                        link_usage,
                        delivered,
                        turn_moves,
                    )
                    break

            if not turn_moves:
                raise PathNotFoundError(
                    "Simulation deadlock: no drone can move"
                )

            print(" ".join(turn_moves))
