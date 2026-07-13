"""Read meaningful lines from Fly-in map files."""

from typing import TextIO


class FileReader:
    """Read map lines while skipping comments and empty lines."""

    def __init__(self, file_path: str) -> None:
        """Open a map file for reading."""
        self.file_path = file_path
        self.line_number = 0
        self.file: TextIO = open(file_path, "r")

    def close(self) -> None:
        """Close the map file."""
        if not self.file.closed:
            self.file.close()

    def read_line(self) -> str | None:
        """Return the next meaningful line or None at end of file."""
        while True:
            line = self.file.readline()

            if line == "":
                return None

            self.line_number += 1
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            return line
