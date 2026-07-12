from enums import LineType


class ParsingError(Exception):
    """Base parsing exception for configuration structure and validation."""

    pass


class InvalidStructureError(ParsingError):
    """Raised when a line token arrangement fails pattern rules."""

    pass


class DeclarationError(ParsingError):
    """Raised when required components are absent from configuration."""

    pass


class MultipleKeyDefinitionError(ParsingError):
    """Raised when metadata attribute identifier is duplicated in block."""

    pass


class InvalidValueError(ParsingError):
    """Raised when content validation fails or coordinates non-integral."""

    pass


class UnknownKeyError(ParsingError):
    """Raised when an undefined metadata attribute property is processed."""

    pass


class DuplicatedConnection(ParsingError):
    """Raised when a network link sequence maps an already allocated route."""

    pass


class MultipleDefinitionError(ParsingError):
    """Raised when core variables or identical structural nodes redeclared."""

    pass


class InvalidSequnceError(ParsingError):
    """Raised when sequential constraints are violated during parsing."""

    pass


class UnknownValueError(ParsingError):
    """Raised when reference operations map to missing elements."""

    pass


class PathNotFoundError(Exception):
    """Raised when no logical routing transitions exist to destination."""

    pass


class Errors:
    """Factory handling configuration, connectivity, and syntax violations."""

    @classmethod
    def report_bad_line_type(cls, line: str, line_number: int) -> None:
        """Validates unexpected line strings against expected syntaxes."""
        error_message = f"Unknown line type at line {line_number}: '{line}'"
        raise InvalidStructureError(error_message)

    @classmethod
    def trigger_absent_required_statement(cls, line_type: LineType) -> None:
        """Ensures fundamental configuration prerequisites exist."""
        match line_type.value:
            case LineType.NB_DRONES.value:
                error_message = "Missing required declaration: nb_drones"
            case LineType.START_HUB.value:
                error_message = "Missing required declaration: start_hub"
            case LineType.END_HUB.value:
                error_message = "Missing required declaration: end_hub"
            case _:
                error_message = "Error in config file"
        raise DeclarationError(error_message)

    @classmethod
    def report_drones_clash_definition(
        cls,
        raw_line: str,
        line_number: int,
        prev_line: str,
        prev_line_number: int,
    ) -> None:
        """Fails when global scaling criteria allocated over multi-locations"""
        error_message = (
            f"Multiple definitions of nb_drones at line {line_number}: "
            f"'{raw_line}'. Previous declaration at line {prev_line_number}: "
            f"'{prev_line}'"
        )
        raise MultipleDefinitionError(error_message)

    @classmethod
    def report_start_hub_clash_definition(
        cls,
        raw_line: str,
        line_number: int,
        prev_line: str,
        prev_line_number: int,
    ) -> None:
        """Validates that a singular network layout origin reference exists."""
        error_message = (
            f"Multiple definitions of start_hub at line {line_number}: "
            f"'{raw_line}'. Previous declaration at line {prev_line_number}: "
            f"'{prev_line}'"
        )
        raise MultipleDefinitionError(error_message)

    @classmethod
    def report_end_hub_clash_definition(
        cls,
        raw_line: str,
        line_number: int,
        prev_line: str,
        prev_line_number: int,
    ) -> None:
        """Validate that a singular system routing conclusion node declared"""
        error_message = (
            f"Multiple definitions of end_hub at line {line_number}: "
            f"'{raw_line}'. Previous declaration at line {prev_line_number}: "
            f"'{prev_line}'"
        )
        raise MultipleDefinitionError(error_message)

    @classmethod
    def trigger_bad_drones_layout(
            cls, raw_line: str, line_number: int) -> None:
        """Enforces matching signatures for global system scalar definition."""
        error_message = (
            f"Invalid format for nb_drones at line {line_number}: '{raw_line}'"
        )
        raise InvalidStructureError(error_message)

    @classmethod
    def trigger_bad_start_hub_layout(
        cls, raw_line: str, line_number: int
    ) -> None:
        """Validate lexical construction schemas for processing entry points"""
        error_message = (
            f"Invalid format for start_hub at line {line_number}: '{raw_line}'"
        )
        raise InvalidStructureError(error_message)

    @classmethod
    def trigger_bad_hub_layout(cls, raw_line: str, line_number: int) -> None:
        """Enforces data compliance thresholds for network vertex rules."""
        error_message = (
            f"Invalid format for hub at line {line_number}: '{raw_line}'"
        )
        raise InvalidStructureError(error_message)

    @classmethod
    def trigger_bad_end_hub_layout(
        cls, raw_line: str, line_number: int
    ) -> None:
        """Validates configuration parameters mapped to network boundaries."""
        error_message = (
            f"Invalid format for end_hub at line {line_number}: '{raw_line}'"
        )
        raise InvalidStructureError(error_message)

    @classmethod
    def trigger_bad_connection_layout(
        cls, raw_line: str, line_number: int
    ) -> None:
        """Checks alignment structural signatures across link parsing steps."""
        error_message = (
            f"Invalid format for connection at line {line_number}: "
            f"'{raw_line}'"
        )
        raise InvalidStructureError(error_message)

    @classmethod
    def trigger_bad_zone_name_layout(
        cls, raw_line: str, zone_name: str, line_number: int
    ) -> None:
        """Rejects node tags containing non-alphanumeric formats."""
        error_message = (
            f"Invalid zone name '{zone_name}' at line {line_number}: "
            f"'{raw_line}'"
        )
        raise InvalidStructureError(error_message)

    @classmethod
    def trigger_unparseable_coordinate(
        cls,
        raw_line: str,
        coordinate: str,
        coordinate_value: str,
        line_number: int,
    ) -> None:
        """Filters non-integer assignments out of position components."""
        error_message = (
            f"Invalid coordinate value for '{coordinate}' ({coordinate_value})"
            f" at line {line_number}: '{raw_line}'"
        )
        raise InvalidValueError(error_message)

    @classmethod
    def trigger_unparseable_drones_count(
        cls, raw_line: str, nb_drones_value: str, line_number: int
    ) -> None:
        """Flags scale constraints below unity or carrying floats."""
        error_message = (
            f"Invalid number of drones ({nb_drones_value}) "
            f"at line {line_number}: '{raw_line}'"
        )
        raise InvalidValueError(error_message)

    @classmethod
    def report_recursive_connection(
        cls, raw_line: str, source_name: str, dest_name: str, line_number: int
    ) -> None:
        """Restricts cyclic network topologies targeting own interfaces."""
        error_message = (
            f"Invalid connection between same zones '{source_name}' "
            f"and '{dest_name}' at line {line_number}: '{raw_line}'"
        )
        raise DuplicatedConnection(error_message)

    @classmethod
    def report_missing_link_source(
        cls, raw_line: str, source_zone: str, line_number: int
    ) -> None:
        """Restricts link operations targeting undefined source variables."""
        error_message = (
            f"Unknown connection source zone '{source_zone}' "
            f"at line {line_number}: '{raw_line}'"
        )
        raise UnknownValueError(error_message)

    @classmethod
    def report_missing_link_destination(
        cls, raw_line: str, dest_zone: str, line_number: int
    ) -> None:
        """Restricts edge configurations terminating at missing records."""
        error_message = (
            f"Unknown connection destination zone '{dest_zone}' "
            f"at line {line_number}: '{raw_line}'"
        )
        raise UnknownValueError(error_message)

    @classmethod
    def report_hub_tag_clash(
        cls,
        raw_line: str,
        line_number: int,
        hub_name: str,
        prev_line: str,
        prev_line_number: int,
    ) -> None:
        """Ensures localized zone tracking references remain unique."""
        error_message = (
            f"Duplicate definition for hub '{hub_name}' at line {line_number}:"
            f" '{raw_line}'. Previously declared at line {prev_line_number}: "
            f"'{prev_line}'"
        )
        raise MultipleDefinitionError(error_message)

    @classmethod
    def report_start_hub_tag_clash(
        cls,
        raw_line: str,
        line_number: int,
        hub_name: str,
        previous_line: str,
        previous_line_number: int,
    ) -> None:
        """Prevents initial origin parameters from intersecting global tags."""
        error_message = (
            f"Name conflict for start_hub '{hub_name}' at line {line_number}: "
            f"'{raw_line}'. Conflict with declaration at line "
            f"{previous_line_number}: '{previous_line}'"
        )
        raise MultipleDefinitionError(error_message)

    @classmethod
    def report_end_hub_tag_clash(
        cls,
        raw_line: str,
        line_number: int,
        hub_name: str,
        previous_line: str,
        previous_line_number: int,
    ) -> None:
        """Prevents path terminal components from intersecting tracking."""
        error_message = (
            f"Name conflict for end_hub '{hub_name}' at line {line_number}: "
            f"'{raw_line}'. Conflict with declaration at line "
            f"{previous_line_number}: '{previous_line}'"
        )
        raise MultipleDefinitionError(error_message)


class MetadataErrors:
    """Factory handling parameter blocks contained inside bracket wrappers."""

    @classmethod
    def trigger_bad_metadata_syntax(
        cls, raw_metadata: str, line_number: int
    ) -> None:
        """Validates that parsing variable isolated inside complete brackets"""
        error_message = (
            f"Invalid metadata syntax layout at line {line_number}: "
            f"'{raw_metadata}'"
        )
        raise InvalidValueError(error_message)

    @classmethod
    def trigger_bad_link_capacity(
        cls, raw_line: str, max_link_capacity: str, line_number: int
    ) -> None:
        """Flags edge capacity constraints thresholds below unity."""
        error_message = (
            f"Invalid max link capacity value ({max_link_capacity}) "
            f"at line {line_number}: '{raw_line}'"
        )
        raise InvalidValueError(error_message)

    @classmethod
    def trigger_unregistered_link_property(
        cls, raw_line: str, key: str, line_number: int
    ) -> None:
        """Flags unsupported processing tags attached to network path."""
        error_message = (
            f"Unknown connection metadata key '{key}' at line {line_number}: "
            f"'{raw_line}'"
        )
        raise UnknownKeyError(error_message)

    @classmethod
    def trigger_unregistered_zone_property(
        cls, raw_line: str, key: str, line_number: int
    ) -> None:
        """Filters out non-standard property indicators matched to data."""
        error_message = (
            f"Unknown zone metadata key '{key}' at line {line_number}: "
            f"'{raw_line}'"
        )
        raise UnknownKeyError(error_message)

    @classmethod
    def report_recurrent_property_tag(
        cls, raw_line: str, key: str, line_number: int
    ) -> None:
        """Flags redundant assignments to unique metadata criteria."""
        error_message = (
            f"Duplicate metadata key '{key}' found at line {line_number}: "
            f"'{raw_line}'"
        )
        raise MultipleKeyDefinitionError(error_message)

    @classmethod
    def trigger_bad_zone_type_label(
        cls, raw_line: str, zone_type: str, line_number: int
    ) -> None:
        """Restricts structural state types to supported labels."""
        error_message = (
            f"Invalid zone type '{zone_type}' specified at line {line_number}:"
            f" '{raw_line}'"
        )
        raise InvalidValueError(error_message)

    @classmethod
    def trigger_bad_color_hex(
        cls,
        raw_line: str,
        color: str,
        line_number: int,
        supported_colors: set[str],
    ) -> None:
        """Validates target aesthetic properties against verified colors."""
        allowed = ", ".join(supported_colors)
        error_message = (
            f"Invalid color '{color}' at line {line_number}: '{raw_line}'. "
            f"Supported colors: {allowed}"
        )
        raise InvalidValueError(error_message)

    @classmethod
    def trigger_bad_max_drones_bound(
        cls, raw_line: str, max_drones_value: str, line_number: int
    ) -> None:
        """Rejects volume bounds outside positive integer parameters."""
        error_message = (
            f"Invalid max drones value ({max_drones_value}) "
            f"at line {line_number}: '{raw_line}'"
        )
        raise InvalidValueError(error_message)


class SequnceErrors:
    """Factory handling lifecycle validation checkpoints for phases."""

    @classmethod
    def report_preceded_drones_definition(
        cls, raw_line: str, entity_type: str, line_number: int
    ) -> None:
        """Validates that initial scaling metrics lead the compiled flow."""
        error_message = (
            f"Ordering constraint violation: '{entity_type}' at line "
            f"{line_number} defined before nb_drones line: '{raw_line}'"
        )
        raise InvalidSequnceError(error_message)

    @classmethod
    def report_preceded_start_hub(
        cls, raw_line: str, entity_type: str, line_number: int
    ) -> None:
        """Enforces routing anchor parameters defined before milestones."""
        error_message = (
            f"Ordering constraint violation: '{entity_type}' at line "
            f"{line_number} defined before start_hub line: '{raw_line}'"
        )
        raise InvalidSequnceError(error_message)

    @classmethod
    def report_preceded_end_hub(
        cls, raw_line: str, entity_type: str, line_number: int
    ) -> None:
        """Validates structure configurations that require final criteria."""
        error_message = (
            f"Ordering constraint violation: '{entity_type}' at line "
            f"{line_number} defined before end_hub line: '{raw_line}'"
        )
        raise InvalidSequnceError(error_message)
