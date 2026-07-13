"""Exceptions and error helpers for Fly-in."""

from typing import NoReturn

from enums import LineType


class ParsingError(Exception):
    """Base parsing exception."""


class InvalidStructureError(ParsingError):
    """Invalid declaration structure."""


class DeclarationError(ParsingError):
    """Missing required declaration."""


class MultipleKeyDefinitionError(ParsingError):
    """Duplicated metadata key."""


class InvalidValueError(ParsingError):
    """Invalid parsed value."""


class UnknownKeyError(ParsingError):
    """Unknown metadata key."""


class DuplicatedConnection(ParsingError):
    """Duplicated or recursive connection."""


class MultipleDefinitionError(ParsingError):
    """Duplicated declaration."""


class InvalidSequnceError(ParsingError):
    """Invalid declaration order."""


class UnknownValueError(ParsingError):
    """Reference to an unknown value."""


class PathNotFoundError(Exception):
    """No valid route exists to the destination."""


class Errors:
    """Create consistent parsing errors."""

    @staticmethod
    def raise_at(
        error: type[ParsingError],
        message: str,
        raw_line: str,
        line_number: int,
    ) -> NoReturn:
        """Raise an error containing its line and cause."""
        raise error(
            f"{message} at line {line_number}: '{raw_line}'"
        )

    @staticmethod
    def missing(line_type: LineType) -> NoReturn:
        """Raise an error for a missing required declaration."""
        raise DeclarationError(
            f"Missing required declaration: {line_type.value}"
        )

    @staticmethod
    def duplicate(
        name: str,
        raw_line: str,
        line_number: int,
        previous_line: str,
        previous_number: int,
    ) -> NoReturn:
        """Raise an error for a duplicate declaration."""
        raise MultipleDefinitionError(
            f"Multiple definitions of {name} at line {line_number}: "
            f"'{raw_line}'. Previous declaration at line "
            f"{previous_number}: '{previous_line}'"
        )

    @staticmethod
    def invalid_metadata(
        raw_line: str,
        line_number: int,
        message: str = "Invalid metadata syntax",
    ) -> NoReturn:
        """Raise an error for malformed metadata."""
        Errors.raise_at(
            InvalidValueError,
            message,
            raw_line,
            line_number,
        )

    @staticmethod
    def invalid_sequence(
        entity: str,
        required: str,
        raw_line: str,
        line_number: int,
    ) -> NoReturn:
        """Raise an error for an invalid declaration order."""
        Errors.raise_at(
            InvalidSequnceError,
            f"'{entity}' defined before {required}",
            raw_line,
            line_number,
        )
