"""Tests for the Fly-in map parser."""

import os
import tempfile
import unittest

from errors import ParsingError
from parser import Parser


class ParserTests(unittest.TestCase):
    """Test valid and invalid map declarations."""

    def setUp(self) -> None:
        """Create a temporary directory for test maps."""
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        """Remove temporary test maps."""
        self.temp_dir.cleanup()

    def _map_path(self, content: str) -> str:
        """Create and return a temporary map path."""
        path = os.path.join(
            self.temp_dir.name,
            "test_map.txt",
        )

        with open(path, "w") as file:
            file.write(content)

        return path

    def _parse(self, content: str) -> Parser:
        """Create and run a parser for map content."""
        parser = Parser(self._map_path(content))
        parser.parse()
        return parser

    def test_valid_map(self) -> None:
        """Parse a complete valid map."""
        parser = self._parse(
            "\n".join(
                [
                    "nb_drones: 2",
                    "start_hub: start 0 0",
                    "end_hub: goal 2 0",
                    "hub: middle 1 0",
                    "connection: start-middle",
                    "connection: middle-goal",
                ]
            )
        )

        self.assertEqual(parser.nb_drones, 2)
        self.assertEqual(parser.start_hub, "start")
        self.assertEqual(parser.end_hub, "goal")
        self.assertEqual(len(parser.hubs), 3)
        self.assertEqual(
            len(parser.connection_declarations),
            2,
        )

    def test_arbitrary_color_is_accepted(self) -> None:
        """Accept any single-word color value."""
        parser = self._parse(
            "\n".join(
                [
                    "nb_drones: 1",
                    "start_hub: start 0 0",
                    "end_hub: goal 1 0 [color=turquoise]",
                    "connection: start-goal",
                ]
            )
        )

        self.assertEqual(
            parser.hubs["goal"].color,
            "turquoise",
        )

    def test_start_and_end_capacity_is_ignored(self) -> None:
        """Ignore max_drones metadata on terminal zones."""
        parser = self._parse(
            "\n".join(
                [
                    "nb_drones: 2",
                    "start_hub: start 0 0 [max_drones=invalid]",
                    "end_hub: goal 1 0 [max_drones=0]",
                    "connection: start-goal",
                ]
            )
        )

        # Start and end hubs should not keep capacity limits.
        self.assertIsNone(
            parser.hubs["start"].max_drones
        )

        self.assertIsNone(
            parser.hubs["goal"].max_drones
        )

    def test_reversed_duplicate_connection_is_rejected(
        self,
    ) -> None:
        """Treat a-b and b-a as duplicate connections."""
        content = "\n".join(
            [
                "nb_drones: 1",
                "start_hub: start 0 0",
                "end_hub: goal 1 0",
                "connection: start-goal",
                "connection: goal-start",
            ]
        )

        with self.assertRaises(ParsingError):
            self._parse(content)

    def test_trailing_metadata_content_is_rejected(
        self,
    ) -> None:
        """Reject content after a metadata block."""
        content = "\n".join(
            [
                "nb_drones: 1",
                "start_hub: start 0 0",
                "end_hub: goal 1 0 [color=red] garbage",
                "connection: start-goal",
            ]
        )

        with self.assertRaises(ParsingError):
            self._parse(content)

    def test_unknown_zone_in_connection_is_rejected(
        self,
    ) -> None:
        """Reject connections referencing unknown zones."""
        content = "\n".join(
            [
                "nb_drones: 1",
                "start_hub: start 0 0",
                "end_hub: goal 1 0",
                "connection: start-missing",
            ]
        )

        with self.assertRaises(ParsingError):
            self._parse(content)

    def test_missing_end_hub_is_rejected(self) -> None:
        """Require exactly one end hub."""
        content = "\n".join(
            [
                "nb_drones: 1",
                "start_hub: start 0 0",
            ]
        )

        with self.assertRaises(ParsingError):
            self._parse(content)

    def test_invalid_capacity_is_rejected(self) -> None:
        """Reject non-positive regular-zone capacity."""
        content = "\n".join(
            [
                "nb_drones: 1",
                "start_hub: start 0 0",
                "end_hub: goal 2 0",
                "hub: middle 1 0 [max_drones=0]",
                "connection: start-middle",
                "connection: middle-goal",
            ]
        )

        with self.assertRaises(ParsingError):
            self._parse(content)


if __name__ == "__main__":
    unittest.main()
