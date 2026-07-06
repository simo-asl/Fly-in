"""Command-line entrypoint for the Fly-in drone simulation."""

from __future__ import annotations

import sys

from drone_graph import DroneGraph
from errors import InvalidArgumentError, PathNotFoundError, ParsingError
from parser import Parser
from simulation import SimulationEngine


def _print_usage() -> None:
    """Print the expected command-line usage."""
    print("Usage: python3 main.py <map_file>")


def main() -> int:
    """Parse a map file and run the drone routing simulation."""
    if len(sys.argv) != 2:
        _print_usage()
        return 1

    map_file = sys.argv[1]

    try:
        parser = Parser(map_file)
        parser.parse()
        graph = DroneGraph(
            parser.zone_declarations,
            parser.connection_declarations,
        )
        engine = SimulationEngine(
            graph,
            parser.nb_drones,
            parser.start_hub,
            parser.end_hub,
        )
        engine.run_simulation()
    except FileNotFoundError:
        print(f"Error: file not found: {map_file}")
        return 1
    except PermissionError:
        print(f"Error: cannot open file: {map_file}")
        return 2
    except (ParsingError, PathNotFoundError, InvalidArgumentError) as error:
        print(f"Error: {error}")
        return 3
    except Exception as error:
        print(f"Unexpected error: {error}")
        return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
