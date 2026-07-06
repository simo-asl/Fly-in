from parser import Connection, Zone


class DroneGraph:
    def __init__(
            self, zones: list[Zone], connections: list[Connection]) -> None:
        """Initialize the DroneGraph with zones and connections."""
        self.zones: dict[str, Zone] = {zone.name: zone for zone in zones}
        self.connections: list[Connection] = connections
        self._connections_by_pair: dict[tuple[str, str], Connection] = {}
        for connection in connections:
            if connection.source < connection.destination:
                key = (connection.source, connection.destination)
            else:
                key = (connection.destination, connection.source)
            self._connections_by_pair[key] = connection

    def get_neighbors(self, zone_name: str) -> list[tuple[Zone, Connection]]:
        """Get the names of neighboring zones for a given zone."""
        neighbors: list[tuple[Zone, Connection]] = []
        zone = self.zones.get(zone_name)
        if zone is None:
            return neighbors

        for connection in self.connections:
            neighbor_name = None
            if connection.source == zone_name:
                neighbor_name = connection.destination
            elif connection.destination == zone_name:
                neighbor_name = connection.source
            if neighbor_name:
                neighbor_zone = self.zones.get(neighbor_name)
                if (
                    neighbor_zone is not None
                    and neighbor_zone.zone_type != "blocked"
                ):
                    neighbors.append((neighbor_zone, connection))

        return neighbors

    def get_zone(self, zone_name: str) -> Zone | None:
        """Return the zone instance for a given name if it exists."""
        return self.zones.get(zone_name)

    def get_connection(
        self,
        source: str,
        destination: str,
    ) -> Connection | None:
        """Return the connection between two zones if it exists."""
        if source < destination:
            key = (source, destination)
        else:
            key = (destination, source)
        return self._connections_by_pair.get(key)
