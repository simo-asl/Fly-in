from dataclasses import dataclass, field

from enums import LineType, ZoneType
from errors import DuplicatedConnection, Errors, MetadataErrors, SequnceErrors
from reading import FileReader


ALLOWED_COLORS: set[str] = {
    "none",
    "red",
    "green",
    "blue",
    "yellow",
    "purple",
    "magenta",
    "cyan",
    "white",
    "black",
    "brown",
    "maroon",
    "orange",
    "gold",
    "crimson",
    "violet",
    "darkred",
    "rainbow",
    "lime",
}


@dataclass
class Zone:
    """One zone declaration from the map file."""

    name: str
    x: int
    y: int
    zone_type: str = "normal"
    color: str = "none"
    max_drones: int = 1
    declaration_type: ZoneType = ZoneType.HUB
    reservations: dict[int, int] = field(default_factory=dict)

    def is_available_at(self, turn: int, extra: int = 1) -> bool:
        """Return True if the zone can accept `extra` drones at `turn`."""
        if self.declaration_type in (ZoneType.START_HUB, ZoneType.END_HUB):
            return True
        occupied = self.reservations.get(turn, 0)
        return occupied + extra <= self.max_drones

    def reserve_at(self, turn: int, extra: int = 1) -> None:
        """Reserve `extra` slots at a specific `turn`."""
        self.reservations[turn] = self.reservations.get(turn, 0) + extra


@dataclass
class Connection:
    """One bidirectional edge declaration from the map file."""

    source: str
    destination: str
    max_link_capacity: int = 1
    reservations: dict[int, int] = field(default_factory=dict)

    def is_available_at(self, turn: int, extra: int = 1) -> bool:
        """Return True if the connection has capacity at `turn`."""
        used = self.reservations.get(turn, 0)
        return used + extra <= self.max_link_capacity

    def reserve_at(self, turn: int, extra: int = 1) -> None:
        """Reserve `extra` slots on the connection at `turn`."""
        self.reservations[turn] = self.reservations.get(turn, 0) + extra


class Parser:
    """Parse and validate drone maps according to project constraints."""

    def __init__(self, file_name: str) -> None:
        """Initialize parser state and containers."""
        self.file_reader: FileReader = FileReader(file_name)
        self.file_name: str = file_name
        self.nb_drones: int = 0

        self.hubs: dict[str, Zone] = {}
        self.start_hub: str = ""
        self.end_hub: str = ""
        self.connections: dict[str, list[str]] = {}

        self.zone_declarations: list[Zone] = []
        self.connection_declarations: list[Connection] = []
        self.connection_capacities: dict[tuple[str, str], int] = {}

        self._nb_drones_decl: tuple[str, int] | None = None
        self._start_decl: tuple[str, int] | None = None
        self._end_decl: tuple[str, int] | None = None
        self._zone_decl_info: dict[str, tuple[str, int]] = {}
        self._connection_pairs: set[tuple[str, str]] = set()
        self._saw_first_data_line: bool = False

    @staticmethod
    def __normalize_pair(source: str, destination: str) -> tuple[str, str]:
        """Return canonical tuple for undirected connection comparison."""
        if source < destination:
            return source, destination
        return destination, source

    @staticmethod
    def __is_positive_integer(raw_value: str) -> bool:
        """Check if raw value is a decimal integer strictly greater than 0."""
        if not raw_value.isdigit():
            return False
        return int(raw_value) > 0

    def __extract_payload(self, raw_line: str, line_type: LineType) -> str:
        """Return content located after '<type>:' prefix."""
        prefix = f"{line_type.value}:"
        return raw_line[len(prefix):].strip()

    def __extract_metadata(
        self,
        payload: str,
        raw_line: str,
        line_number: int,
    ) -> tuple[str, dict[str, str]]:
        """Split main payload and metadata block then parse key/value pairs."""
        open_index = payload.find("[")
        hashtag_index = payload.find("#")
        close_index = payload.find("]")
        payload = payload[:hashtag_index] if hashtag_index != -1 else payload
        if open_index == -1 and close_index == -1:
            return payload.strip(), {}

        if open_index < hashtag_index < close_index:
            MetadataErrors.trigger_bad_metadata_syntax(raw_line, line_number)

        if open_index == -1 or close_index == -1:
            MetadataErrors.trigger_bad_metadata_syntax(raw_line, line_number)

        if close_index < open_index:
            MetadataErrors.trigger_bad_metadata_syntax(raw_line, line_number)

        base = payload[:open_index].strip()
        raw_metadata = payload[open_index + 1:close_index].strip()

        if not raw_metadata:
            return base, {}

        metadata: dict[str, str] = {}
        for token in raw_metadata.split():
            if "=" not in token:
                MetadataErrors.trigger_bad_metadata_syntax(
                    raw_line,
                    line_number,
                )

            key, value = token.split("=", 1)
            if not key or not value:
                MetadataErrors.trigger_bad_metadata_syntax(
                    raw_line,
                    line_number,
                )

            if key in metadata:
                MetadataErrors.report_recurrent_property_tag(
                    raw_line,
                    key,
                    line_number,
                )
            metadata[key] = value

        return base, metadata

    def __parse_nb_drones(self, raw_line: str, line_number: int) -> None:
        """Parse and validate the nb_drones declaration."""
        if self._nb_drones_decl is not None:
            prev_line, prev_line_number = self._nb_drones_decl
            Errors.report_drones_clash_definition(
                raw_line,
                line_number,
                prev_line,
                prev_line_number,
            )

        payload = self.__extract_payload(raw_line, LineType.NB_DRONES)
        if not payload:
            Errors.trigger_bad_drones_layout(raw_line, line_number)
        index = payload.find("#")
        if index != -1:
            payload = payload[:index].strip()
        if " " in payload or "\t" in payload:
            Errors.trigger_bad_drones_layout(raw_line, line_number)

        if not self.__is_positive_integer(payload):
            Errors.trigger_unparseable_drones_count(
                raw_line,
                payload,
                line_number,
            )

        self.nb_drones = int(payload)
        self._nb_drones_decl = (raw_line, line_number)

    def __parse_zone_line(
        self,
        raw_line: str,
        line_number: int,
        line_type: LineType,
    ) -> Zone:
        """Parse and validate one zone declaration."""
        payload = self.__extract_payload(raw_line, line_type)
        base, metadata = self.__extract_metadata(
            payload,
            raw_line,
            line_number,
        )
        tokens = base.split()

        if len(tokens) != 3:
            self.__raise_bad_zone_layout(line_type, raw_line, line_number)

        name, x_value, y_value = tokens
        self.__validate_zone_name(raw_line, line_number, name)

        x = self.__parse_coordinate(
            raw_line,
            line_number,
            "x",
            x_value,
        )
        y = self.__parse_coordinate(
            raw_line,
            line_number,
            "y",
            y_value,
        )

        zone_kind = "normal"
        color = "none"
        max_drones = 1

        for key, value in metadata.items():
            if key.lower() == "zone":
                allowed = {"normal", "blocked", "restricted", "priority"}
                if value not in allowed:
                    MetadataErrors.trigger_bad_zone_type_label(
                        raw_line,
                        value,
                        line_number,
                    )
                zone_kind = value
            elif key.lower() == "color":
                if value.lower() not in ALLOWED_COLORS:
                    MetadataErrors.trigger_bad_color_hex(
                        raw_line,
                        value,
                        line_number,
                        ALLOWED_COLORS,
                    )
                color = value
            elif key.lower() == "max_drones":
                if not self.__is_positive_integer(value):
                    MetadataErrors.trigger_bad_max_drones_bound(
                        raw_line,
                        value,
                        line_number,
                    )
                max_drones = int(value)
            else:
                MetadataErrors.trigger_unregistered_zone_property(
                    raw_line,
                    key,
                    line_number,
                )

        declaration_type = ZoneType.HUB
        if line_type == LineType.START_HUB:
            declaration_type = ZoneType.START_HUB
        elif line_type == LineType.END_HUB:
            declaration_type = ZoneType.END_HUB

        return Zone(
            name=name,
            x=x,
            y=y,
            zone_type=zone_kind,
            color=color,
            max_drones=max_drones,
            declaration_type=declaration_type,
        )

    def __validate_zone_name(
        self,
        raw_line: str,
        line_number: int,
        zone_name: str,
    ) -> None:
        """Enforce zone name format: no whitespace and no dash."""
        if "-" in zone_name:
            Errors.trigger_bad_zone_name_layout(
                raw_line,
                zone_name,
                line_number,
            )

    def __parse_coordinate(
        self,
        raw_line: str,
        line_number: int,
        coordinate_name: str,
        coordinate_value: str,
    ) -> int:
        """Parse one coordinate and raise a detailed validation error."""
        try:
            return int(coordinate_value)
        except ValueError:
            Errors.trigger_unparseable_coordinate(
                raw_line,
                coordinate_name,
                coordinate_value,
                line_number,
            )
        return 0

    def __raise_bad_zone_layout(
        self,
        line_type: LineType,
        raw_line: str,
        line_number: int,
    ) -> None:
        """Raise line-type specific malformed-zone error."""
        if line_type == LineType.START_HUB:
            Errors.trigger_bad_start_hub_layout(raw_line, line_number)
        elif line_type == LineType.END_HUB:
            Errors.trigger_bad_end_hub_layout(raw_line, line_number)
        else:
            Errors.trigger_bad_hub_layout(raw_line, line_number)

    def __register_zone(
        self,
        raw_line: str,
        line_number: int,
        line_type: LineType,
        zone: Zone,
    ) -> None:
        """Register a zone and validate uniqueness constraints."""
        if line_type == LineType.START_HUB:
            if self._start_decl is not None:
                prev_line, prev_line_number = self._start_decl
                Errors.report_start_hub_clash_definition(
                    raw_line,
                    line_number,
                    prev_line,
                    prev_line_number,
                )
        elif line_type == LineType.END_HUB:
            if self._end_decl is not None:
                prev_line, prev_line_number = self._end_decl
                Errors.report_end_hub_clash_definition(
                    raw_line,
                    line_number,
                    prev_line,
                    prev_line_number,
                )

        if zone.name in self._zone_decl_info:
            prev_line, prev_line_number = self._zone_decl_info[zone.name]
            if line_type == LineType.START_HUB:
                Errors.report_start_hub_tag_clash(
                    raw_line,
                    line_number,
                    zone.name,
                    prev_line,
                    prev_line_number,
                )
            elif line_type == LineType.END_HUB:
                Errors.report_end_hub_tag_clash(
                    raw_line,
                    line_number,
                    zone.name,
                    prev_line,
                    prev_line_number,
                )
            else:
                Errors.report_hub_tag_clash(
                    raw_line,
                    line_number,
                    zone.name,
                    prev_line,
                    prev_line_number,
                )

        self.hubs[zone.name] = zone
        self.zone_declarations.append(zone)
        self._zone_decl_info[zone.name] = (raw_line, line_number)

        if line_type == LineType.START_HUB:
            self.start_hub = zone.name
            self._start_decl = (raw_line, line_number)
        elif line_type == LineType.END_HUB:
            self.end_hub = zone.name
            self._end_decl = (raw_line, line_number)

    def __parse_connection(
        self,
        raw_line: str,
        line_number: int,
    ) -> None:
        """Parse and validate one connection declaration."""
        payload = self.__extract_payload(raw_line, LineType.CONNECTION)
        base, metadata = self.__extract_metadata(
            payload,
            raw_line,
            line_number,
        )

        edge = base.strip()
        if edge.count("-") != 1:
            Errors.trigger_bad_connection_layout(raw_line, line_number)

        source, destination = edge.split("-", 1)
        source = source.strip()
        destination = destination.strip()
        index = destination.find("#")
        if index != -1:
            destination = destination[:index].strip()
        if not source or not destination:
            Errors.trigger_bad_connection_layout(raw_line, line_number)

        if source == destination:
            Errors.report_recursive_connection(
                raw_line,
                source,
                destination,
                line_number,
            )

        if source not in self.hubs:
            Errors.report_missing_link_source(raw_line, source, line_number)
        if destination not in self.hubs:
            Errors.report_missing_link_destination(
                raw_line,
                destination,
                line_number,
            )

        max_link_capacity = 1
        for key, value in metadata.items():
            if key != "max_link_capacity":
                MetadataErrors.trigger_unregistered_link_property(
                    raw_line,
                    key,
                    line_number,
                )

            if not self.__is_positive_integer(value):
                MetadataErrors.trigger_bad_link_capacity(
                    raw_line,
                    value,
                    line_number,
                )
            max_link_capacity = int(value)

        pair = self.__normalize_pair(source, destination)
        if pair in self._connection_pairs:
            raise DuplicatedConnection(
                "Duplicate connection found at line "
                f"{line_number}: '{raw_line}'"
            )

        self._connection_pairs.add(pair)
        self.connection_capacities[pair] = max_link_capacity
        self.connection_declarations.append(
            Connection(source, destination, max_link_capacity)
        )

    def __detect_line_type(self, line: str) -> LineType:
        """Detect line type based on known prefixes."""
        if line.lower().startswith(f"{LineType.NB_DRONES.value}:"):
            return LineType.NB_DRONES
        if line.lower().startswith(f"{LineType.HUB.value}:"):
            return LineType.HUB
        if line.lower().startswith(f"{LineType.START_HUB.value}:"):
            return LineType.START_HUB
        if line.lower().startswith(f"{LineType.END_HUB.value}:"):
            return LineType.END_HUB
        if line.lower().startswith(f"{LineType.CONNECTION.value}:"):
            return LineType.CONNECTION
        return LineType.UNKNOWN

    def __validate_required_fields(self) -> None:
        """Ensure mandatory declarations exist exactly once."""
        if self.nb_drones <= 0:
            Errors.trigger_absent_required_statement(LineType.NB_DRONES)
        if not self.start_hub:
            Errors.trigger_absent_required_statement(LineType.START_HUB)
        if not self.end_hub:
            Errors.trigger_absent_required_statement(LineType.END_HUB)

    def __build_graph(self) -> None:
        """Build adjacency list from validated connection declarations."""
        self.connections = {name: [] for name in self.hubs}
        for connection in self.connection_declarations:
            self.connections[connection.source].append(connection.destination)
            self.connections[connection.destination].append(connection.source)

    def __ensure_nb_drones_first(
        self,
        raw_line: str,
        line_number: int,
        line_type: LineType,
    ) -> None:
        """Enforce first non-comment line to be nb_drones declaration."""
        if self._saw_first_data_line:
            return
        self._saw_first_data_line = True
        if line_type != LineType.NB_DRONES:
            SequnceErrors.report_preceded_drones_definition(
                raw_line,
                line_type.value,
                line_number,
            )

    def parse(self) -> None:
        """Parse the full map file and populate parser attributes."""
        try:
            while True:
                raw_line = self.file_reader.read_line()
                if raw_line is None:
                    break

                line_number = self.file_reader.line_number
                line_type = self.__detect_line_type(raw_line)
                self.__ensure_nb_drones_first(raw_line, line_number, line_type)

                if line_type == LineType.UNKNOWN:
                    Errors.report_bad_line_type(raw_line, line_number)

                if (
                    line_type != LineType.NB_DRONES
                    and self._nb_drones_decl is None
                ):
                    SequnceErrors.report_preceded_drones_definition(
                        raw_line,
                        line_type.value,
                        line_number,
                    )

                if line_type == LineType.NB_DRONES:
                    self.__parse_nb_drones(raw_line, line_number)
                    continue

                if line_type in (
                    LineType.HUB,
                    LineType.START_HUB,
                    LineType.END_HUB,
                ):
                    zone = self.__parse_zone_line(
                        raw_line,
                        line_number,
                        line_type,
                    )
                    self.__register_zone(
                        raw_line,
                        line_number,
                        line_type,
                        zone,
                    )
                    continue

                if line_type == LineType.CONNECTION:
                    self.__parse_connection(raw_line, line_number)

            self.__validate_required_fields()
            self.__build_graph()
        finally:
            self.file_reader.close()
