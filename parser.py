from enums import LineType
from reading import FileReader
from errors import Errors, SequnceErrors
import re


class Parser:
    def __init__(self, file_name: str):
        """Initialize the Parser with the given file name."""
        self.file_reader: FileReader = FileReader(file_name)
        self.file_name = file_name
        self.nb_drones: int = 0
        self.hubs: dict[str, LineType] = {}
        self.start_hub: str = ""
        self.end_hub: str = ""
        self.connections: dict[str, list[str]] = {}

    def __parse_nb_drones(self, line: str) -> int:
        """Parse the number of drones"""
        return int(line.split(":")[1].strip())

    def __parse_zone(self, line: str) -> str:
        """Parse a zone line and return the zone name."""
        # wait until we start the metdata

    def __parse_connection(self, line: str) -> tuple[str, str]:
        """Parse a connection line."""
        # wait until we start the metdata

    def __detect_line_type(self, line: str) -> LineType:
        """Detect the type of line based on its content."""
        if line.startswith(f"{LineType.NB_DRONES.value}:"):
            return LineType.NB_DRONES
        elif line.startswith(f"{LineType.HUB.value}:"):
            return LineType.HUB
        elif line.startswith(f"{LineType.START_HUB.value}:"):
            return LineType.START_HUB
        elif line.startswith(f"{LineType.END_HUB.value}:"):
            return LineType.END_HUB
        elif line.startswith(f"{LineType.CONNECTION.value}:"):
            return LineType.CONNECTION
        else:
            return LineType.UNKNOWN

    def parse(self) -> None:
        """Parse the file and extract infos"""
        while True:
            raw_line: str | None = self.file_reader.read_line()
            if raw_line is None:
                break
            line_type = self.__detect_line_type(raw_line)

            match line_type:
                case LineType.NB_DRONES:
                    self.__parse_nb_drones(raw_line)
                case LineType.HUB:
                    self.__parse_hub(raw_line)
                case LineType.START_HUB:
                    self.__parse_start_hub(raw_line)
                case LineType.END_HUB:
                    self.__parse_end_hub(raw_line)
                case LineType.CONNECTION:
                    self.__parse_connection(raw_line)
                case LineType.UNKNOWN:
                    Errors.log_unknown_line(raw_line)
