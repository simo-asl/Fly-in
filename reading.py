from io import TextIOWrapper


class FileReader:
    """A class for reading lines from a file, skip empty lines and comments."""
    def __init__(self, file_path: str) -> None:
        """Initialize the FileReader with the given file path."""
        self.file_path: str = file_path
        self.line_number: int = 0
        self.file: TextIOWrapper
        self.__open()

    def __open(self) -> None:
        """Open the file for reading."""
        self.file = open(self.file_path, "r")

    def close(self) -> None:
        """Close the underlying file handle if it is open."""
        if not self.file.closed:
            self.file.close()

    def read_line(self) -> str | None:
        """Read a line from the file and return it."""
        while True:
            line: str | None = self.file.readline()
            if not line:
                return None

            self.line_number += 1
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            return line
