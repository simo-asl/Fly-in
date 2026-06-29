from parser import Zone, Connection


class DroneGraph:
    def __init__(
            self, zones: list[Zone], connections: list[Connection]) -> None:
        """Initialize the DroneGraph with zones and connections."""
        self.zones: dict[str, Zone] = {zone.name: zone for zone in zones}
        self.connections: list[Connection] = connections

    def get_neighbors(self, zone_name: str) -> list[str]:
        """Get the names of neighboring zones for a given zone."""
        neighbors = []
        for connection in self.connections:
            neighbor_name = None
            if connection.source == zone_name:
                neighbor_name = connection.destination
            elif connection.destination == zone_name:
                neighbor_name = connection.source
            if neighbor_name:
                neighbor_zone = self.zones.get(neighbor_name)
                if not neighbor_zone.is_blocked:
                    neighbors.append((neighbor_name, connection))

        return neighbors

    def reset_link_capacities(self) -> None:
        """Reset the current turn usage for all connections."""
        for connection in self.connections:
            connection.current_turn_usage = 0
