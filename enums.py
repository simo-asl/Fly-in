from enum import Enum


class LineType(str, Enum):
    """Enum for different types of lines in a text file."""

    COMMENT = "comment"
    HUB = "hub"
    START_HUB = "start_hub"
    END_HUB = "end_hub"
    CONNECTION = "connection"
    NB_DRONES = "nb_drones"
    UNKNOWN = "unknown"


class ZoneType(str, Enum):
    """Zone categories for different types of zones."""

    START_HUB = "start_hub"
    END_HUB = "end_hub"
    HUB = "hub"
