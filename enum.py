from enum import Enum, auto


class LineType(str, Enum):
    """Enum for different types of lines in a text file."""

    COMMENT = "comment"
    HUB = "hub"
    START_HUB = "start_hub"
    END_HUB = "end_hub"
    CONNECTION = "connection"
    NB_DRONES = "nb_drones"
    UNKNOWN = "unknown"


class ZoneKeyType(str, Enum):
    """Enum for different types of zone keys."""

    NORMAL = auto()
    RESTRICTED = auto()
    BLOCKED = auto()
    PRIORITY = auto()


class ZoneType(str, Enum):
    """Zone categories for different types of zones."""

    START_HUB = "start_hub"
    END_HUB = "end_hub"
    HUB = "hub"
