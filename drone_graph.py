from parser import Connection, Zone
from utils import normalize_pair


class DroneGraph:
    def __init__(
        self,
        zones: list[Zone],
        connections: list[Connection],
    ) -> None:
        """Initialize the graph with its zones and connections."""
        self.zones: dict[str, Zone] = {zone.name: zone for zone in zones}
        self.connections: list[Connection] = connections

        self._connections_by_pair: dict[tuple[str, str], Connection] = {}
        self._neighbors: dict[str, list[tuple[Zone, Connection]]] = {}

        for connection in connections:
            key = normalize_pair(
                connection.source,
                connection.destination,
            )
            self._connections_by_pair[key] = connection

            source_zone = self.zones[connection.source]
            destination_zone = self.zones[connection.destination]

            if destination_zone.zone_type != "blocked":
                self._neighbors.setdefault(connection.source, []).append(
                    (destination_zone, connection)
                )

            if source_zone.zone_type != "blocked":
                self._neighbors.setdefault(connection.destination, []).append(
                    (source_zone, connection)
                )

    def get_neighbors(self, zone_name: str) -> list[tuple[Zone, Connection]]:
        """Return all reachable neighbors of the given zone."""
        return self._neighbors.get(zone_name, [])

    def get_zone(self, zone_name: str) -> Zone | None:
        """Return the zone instance for a given name if it exists."""
        return self.zones.get(zone_name)

    def get_connection(
        self,
        source: str,
        destination: str,
    ) -> Connection | None:
        """Return the connection linking two zones, if it exists."""
        key = normalize_pair(source, destination)
        return self._connections_by_pair.get(key)
