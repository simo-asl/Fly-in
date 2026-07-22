from enum import Enum


class LineType(str, Enum):
    """Enum for different types of lines in a text file."""

    HUB = "hub"
    START_HUB = "start_hub"
    END_HUB = "end_hub"
    CONNECTION = "connection"
    NB_DRONES = "nb_drones"
    UNKNOWN = "unknown"
