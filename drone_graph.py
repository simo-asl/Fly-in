"""Graph representation for the Fly-in network."""

from parser import Connection, Zone
from utils import normalize_pair


class DroneGraph:
    """Represent zones and their bidirectional connections."""

    def __init__(
        self,
        zones: list[Zone],
        connections: list[Connection],
    ) -> None:
        """Build graph lookup tables from parsed declarations."""
        self.zones = {zone.name: zone for zone in zones}
        self.connections = connections

        self._connections_by_pair = {
            normalize_pair(connection.source, connection.destination):
            connection
            for connection in connections
        }

        self._neighbors: dict[
            str,
            list[tuple[Zone, Connection]],
        ] = {
            zone.name: []
            for zone in zones
        }

        for connection in connections:
            source = self.zones[connection.source]
            destination = self.zones[connection.destination]

            if destination.zone_type != "blocked":
                self._neighbors[source.name].append(
                    (destination, connection)
                )

            if source.zone_type != "blocked":
                self._neighbors[destination.name].append(
                    (source, connection)
                )

    def get_neighbors(
        self,
        zone_name: str,
    ) -> list[tuple[Zone, Connection]]:
        """Return reachable neighbors of a zone."""
        return self._neighbors.get(zone_name, [])

    def get_zone(self, zone_name: str) -> Zone | None:
        """Return a zone by name."""
        return self.zones.get(zone_name)

    def get_connection(
        self,
        source: str,
        destination: str,
    ) -> Connection | None:
        """Return the connection between two zones."""
        return self._connections_by_pair.get(
            normalize_pair(source, destination)
        )
