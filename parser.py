"""Parse and validate Fly-in map files."""

from dataclasses import dataclass

from enums import LineType
from errors import (
    DuplicatedConnection,
    Errors,
    InvalidStructureError,
    InvalidValueError,
    MultipleKeyDefinitionError,
    UnknownKeyError,
    UnknownValueError,
)
from reading import FileReader
from utils import normalize_pair


ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}
ZONE_KEYS = {"zone", "color", "max_drones"}
CONNECTION_KEYS = {"max_link_capacity"}


@dataclass
class Zone:
    name: str
    x: int
    y: int
    zone_type: str = "normal"
    color: str = "none"
    max_drones: int | None = None


@dataclass
class Connection:
    source: str
    destination: str
    max_link_capacity: int = 1


class Parser:
    """Parse and validate a Fly-in map."""

    def __init__(self, file_name: str) -> None:
        """Initialize the parser."""
        self.file_reader = FileReader(file_name)

        self.nb_drones = 0
        self.start_hub = ""
        self.end_hub = ""

        self.hubs: dict[str, Zone] = {}

        self.zone_declarations: list[Zone] = []
        self.connection_declarations: list[Connection] = []

        self._connection_pairs: set[tuple[str, str]] = set()
        self._zone_lines: dict[str, tuple[str, int]] = {}

        self._drones_line: tuple[str, int] | None = None
        self._start_line: tuple[str, int] | None = None
        self._end_line: tuple[str, int] | None = None

    @staticmethod
    def _detect_line(raw_line: str) -> tuple[LineType, str]:
        """Return a line type and its payload."""
        prefixes = {
            "nb_drones:": LineType.NB_DRONES,
            "start_hub:": LineType.START_HUB,
            "end_hub:": LineType.END_HUB,
            "hub:": LineType.HUB,
            "connection:": LineType.CONNECTION,
        }

        for prefix, line_type in prefixes.items():
            if raw_line.startswith(prefix):
                return line_type, raw_line[len(prefix):].strip()

        return LineType.UNKNOWN, ""

    @staticmethod
    def _positive_integer(
        value: str,
        name: str,
        raw_line: str,
        line_number: int,
    ) -> int:
        """Parse a strictly positive integer."""
        if not value.isdigit() or int(value) <= 0:
            Errors.raise_at(
                InvalidValueError,
                f"Invalid {name} value '{value}'",
                raw_line,
                line_number,
            )

        return int(value)

    @staticmethod
    def _extract_metadata(
        payload: str,
        raw_line: str,
        line_number: int,
    ) -> tuple[str, dict[str, str]]:
        """Extract a declaration and its optional metadata."""
        payload = payload.split("#", 1)[0].strip()

        if "[" not in payload and "]" not in payload:
            return payload, {}

        if payload.count("[") != 1 or payload.count("]") != 1:
            Errors.invalid_metadata(raw_line, line_number)

        opening = payload.find("[")
        closing = payload.find("]")

        if opening > closing:
            Errors.invalid_metadata(raw_line, line_number)

        if payload[closing + 1:].strip():
            Errors.invalid_metadata(
                raw_line,
                line_number,
                "Unexpected content after metadata",
            )

        declaration = payload[:opening].strip()
        metadata_text = payload[opening + 1:closing].strip()

        if not declaration:
            Errors.invalid_metadata(
                raw_line,
                line_number,
                "Missing declaration before metadata",
            )

        metadata: dict[str, str] = {}

        for token in metadata_text.split():
            if token.count("=") != 1:
                Errors.invalid_metadata(raw_line, line_number)

            key, value = token.split("=", 1)

            if not key or not value:
                Errors.invalid_metadata(raw_line, line_number)

            if key in metadata:
                Errors.raise_at(
                    MultipleKeyDefinitionError,
                    f"Duplicate metadata key '{key}'",
                    raw_line,
                    line_number,
                )

            metadata[key] = value

        return declaration, metadata

    @staticmethod
    def _validate_keys(
        metadata: dict[str, str],
        allowed: set[str],
        declaration: str,
        raw_line: str,
        line_number: int,
    ) -> None:
        """Reject unsupported metadata keys."""
        unknown = metadata.keys() - allowed

        if unknown:
            key = sorted(unknown)[0]
            Errors.raise_at(
                UnknownKeyError,
                f"Unknown {declaration} metadata key '{key}'",
                raw_line,
                line_number,
            )

    def _parse_drones(
        self,
        payload: str,
        raw_line: str,
        line_number: int,
    ) -> None:
        """Parse the number of drones."""
        if self._drones_line is not None:
            previous, previous_number = self._drones_line
            Errors.duplicate(
                "nb_drones",
                raw_line,
                line_number,
                previous,
                previous_number,
            )

        value = payload.split("#", 1)[0].strip()

        self.nb_drones = self._positive_integer(
            value,
            "nb_drones",
            raw_line,
            line_number,
        )
        self._drones_line = (raw_line, line_number)

    def _check_unique_zone(
        self,
        name: str,
        raw_line: str,
        line_number: int,
    ) -> None:
        """Ensure that a zone name is unique."""
        if name not in self._zone_lines:
            return

        previous, previous_number = self._zone_lines[name]
        Errors.duplicate(
            f"zone '{name}'",
            raw_line,
            line_number,
            previous,
            previous_number,
        )

    def _check_unique_terminal(
        self,
        line_type: LineType,
        raw_line: str,
        line_number: int,
    ) -> None:
        """Ensure start and end hubs are each declared once."""
        if line_type == LineType.START_HUB:
            previous_info = self._start_line
            name = "start_hub"
        elif line_type == LineType.END_HUB:
            previous_info = self._end_line
            name = "end_hub"
        else:
            return

        if previous_info is None:
            return

        previous, previous_number = previous_info
        Errors.duplicate(
            name,
            raw_line,
            line_number,
            previous,
            previous_number,
        )

    def _parse_zone(
        self,
        line_type: LineType,
        payload: str,
        raw_line: str,
        line_number: int,
    ) -> None:
        """Parse and register a zone."""
        declaration, metadata = self._extract_metadata(
            payload,
            raw_line,
            line_number,
        )
        parts = declaration.split()

        if len(parts) != 3:
            Errors.raise_at(
                InvalidStructureError,
                "Expected a zone name and two coordinates",
                raw_line,
                line_number,
            )

        name, x_value, y_value = parts

        if "-" in name:
            Errors.raise_at(
                InvalidStructureError,
                f"Invalid zone name '{name}'",
                raw_line,
                line_number,
            )

        self._check_unique_terminal(
            line_type,
            raw_line,
            line_number,
        )
        self._check_unique_zone(name, raw_line, line_number)
        self._validate_keys(
            metadata,
            ZONE_KEYS,
            "zone",
            raw_line,
            line_number,
        )

        try:
            x = int(x_value)
            y = int(y_value)
        except ValueError:
            Errors.raise_at(
                InvalidValueError,
                "Zone coordinates must be integers",
                raw_line,
                line_number,
            )

        zone_type = metadata.get("zone", "normal")

        if zone_type not in ZONE_TYPES:
            Errors.raise_at(
                InvalidValueError,
                f"Invalid zone type '{zone_type}'",
                raw_line,
                line_number,
            )

        max_drones = None

        if line_type == LineType.HUB:
            max_drones = 1

            if "max_drones" in metadata:
                max_drones = self._positive_integer(
                    metadata["max_drones"],
                    "max_drones",
                    raw_line,
                    line_number,
                )

        zone = Zone(
            name=name,
            x=x,
            y=y,
            zone_type=zone_type,
            color=metadata.get("color", "none"),
            max_drones=max_drones,
        )

        self.hubs[name] = zone
        self.zone_declarations.append(zone)
        self._zone_lines[name] = (raw_line, line_number)

        if line_type == LineType.START_HUB:
            self.start_hub = name
            self._start_line = (raw_line, line_number)
        elif line_type == LineType.END_HUB:
            self.end_hub = name
            self._end_line = (raw_line, line_number)

    def _parse_connection(
        self,
        payload: str,
        raw_line: str,
        line_number: int,
    ) -> None:
        """Parse and register a connection."""
        declaration, metadata = self._extract_metadata(
            payload,
            raw_line,
            line_number,
        )

        if declaration.count("-") != 1:
            Errors.raise_at(
                InvalidStructureError,
                "Invalid connection format",
                raw_line,
                line_number,
            )

        source, destination = (
            value.strip()
            for value in declaration.split("-", 1)
        )

        if not source or not destination:
            Errors.raise_at(
                InvalidStructureError,
                "Invalid connection format",
                raw_line,
                line_number,
            )

        if source == destination:
            Errors.raise_at(
                DuplicatedConnection,
                f"Cannot connect zone '{source}' to itself",
                raw_line,
                line_number,
            )

        if source not in self.hubs:
            Errors.raise_at(
                UnknownValueError,
                f"Unknown connection source zone '{source}'",
                raw_line,
                line_number,
            )

        if destination not in self.hubs:
            Errors.raise_at(
                UnknownValueError,
                f"Unknown connection destination zone '{destination}'",
                raw_line,
                line_number,
            )

        self._validate_keys(
            metadata,
            CONNECTION_KEYS,
            "connection",
            raw_line,
            line_number,
        )

        capacity = 1

        if "max_link_capacity" in metadata:
            capacity = self._positive_integer(
                metadata["max_link_capacity"],
                "max_link_capacity",
                raw_line,
                line_number,
            )

        pair = normalize_pair(source, destination)

        if pair in self._connection_pairs:
            Errors.raise_at(
                DuplicatedConnection,
                f"Duplicate connection '{source}-{destination}'",
                raw_line,
                line_number,
            )

        self._connection_pairs.add(pair)

        connection = Connection(
            source,
            destination,
            max_link_capacity=capacity,
        )

        self.connection_declarations.append(connection)

    def _validate_required_fields(self) -> None:
        """Ensure all mandatory declarations exist."""
        if self._drones_line is None:
            Errors.missing(LineType.NB_DRONES)
        if self._start_line is None:
            Errors.missing(LineType.START_HUB)
        if self._end_line is None:
            Errors.missing(LineType.END_HUB)

    def parse(self) -> None:
        """Parse the complete map file."""
        first_declaration = True

        try:
            while True:
                raw_line = self.file_reader.read_line()

                if raw_line is None:
                    break

                line_number = self.file_reader.line_number
                line_type, payload = self._detect_line(raw_line)

                if first_declaration:
                    first_declaration = False

                    if line_type != LineType.NB_DRONES:
                        Errors.invalid_sequence(
                            line_type.value,
                            "nb_drones",
                            raw_line,
                            line_number,
                        )

                if line_type == LineType.UNKNOWN:
                    Errors.raise_at(
                        InvalidStructureError,
                        "Unknown declaration",
                        raw_line,
                        line_number,
                    )

                if (
                    line_type != LineType.NB_DRONES
                    and self._drones_line is None
                ):
                    Errors.invalid_sequence(
                        line_type.value,
                        "nb_drones",
                        raw_line,
                        line_number,
                    )

                if line_type == LineType.NB_DRONES:
                    self._parse_drones(
                        payload,
                        raw_line,
                        line_number,
                    )
                elif line_type == LineType.CONNECTION:
                    self._parse_connection(
                        payload,
                        raw_line,
                        line_number,
                    )
                else:
                    self._parse_zone(
                        line_type,
                        payload,
                        raw_line,
                        line_number,
                    )

            self._validate_required_fields()
        finally:
            self.file_reader.close()
