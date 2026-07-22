from parser import Zone, Connection
from utils import normalize_pair


class DroneGraph:
    """Represent the drone network as a graph."""

    def __init__(
        self,
        zones: list[Zone],
        connections: list[Connection],
    ) -> None:
        """Initialize graph structures."""
        self.zones: dict[str, Zone] = {
            zone.name: zone
            for zone in zones
        }

        self._neighbors: dict[
            str,
            list[tuple[str, Connection]],
        ] = {}

        self._connections_by_pair: dict[
            tuple[str, str],
            Connection,
        ] = {}

        self._build_graph(connections)

    def _build_graph(
        self,
        connections: list[Connection],
    ) -> None:
        """Build adjacency and connection lookup tables."""
        for connection in connections:
            pair = normalize_pair(
                connection.source,
                connection.destination,
            )

            self._connections_by_pair[pair] = connection

            self._add_neighbor(
                connection.source,
                connection.destination,
                connection,
            )

            self._add_neighbor(
                connection.destination,
                connection.source,
                connection,
            )

    def _add_neighbor(
        self,
        source: str,
        destination: str,
        connection: Connection,
    ) -> None:
        """Add a valid neighbor to the graph."""
        zone = self.zones.get(destination)

        if zone is None:
            return

        if zone.zone_type == "blocked":
            return

        if source not in self._neighbors:
            self._neighbors[source] = []

        self._neighbors[source].append(
            (
                destination,
                connection,
            )
        )

    def get_neighbors(
        self,
        zone_name: str,
    ) -> list[tuple[str, Connection]]:
        """Return reachable neighbors of a zone."""
        return self._neighbors.get(
            zone_name,
            [],
        )

    def get_zone(
        self,
        zone_name: str,
    ) -> Zone | None:
        """Return a zone by name."""
        return self.zones.get(zone_name)

    def get_connection(
        self,
        source: str,
        destination: str,
    ) -> Connection | None:
        """Return connection between two zones."""
        pair = normalize_pair(
            source,
            destination,
        )

        return self._connections_by_pair.get(pair)
