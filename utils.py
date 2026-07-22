from enum import Enum


class Color(str, Enum):
    """ANSII color codes for terminal output"""

    DEFAULT = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BROWN = "\033[38;5;94m"
    MAROON = "\033[38;5;130m"
    ORANGE = "\033[38;5;208m"
    PURPLE = "\033[38;5;93m"
    GOLD = "\033[38;5;220m"
    DARKRED = "\033[38;5;88m"
    VIOLET = "\033[38;5;99m"
    CRIMSON = "\033[38;5;197m"
    LIME = "\033[38;5;118m"


def normalize_pair(a: str, b: str) -> tuple[str, str]:
    """Return a canonical key for an undirected connection"""
    return (a, b) if a < b else (b, a)
