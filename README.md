*This project has been created as part of the 42 curriculum by mel-asla.*

# Fly-in

## Description

Fly-in is a Python 3.10+ drone routing simulator. It parses a zone graph, validates the map format, builds a weighted route network, and simulates multiple drones moving from a unique start hub to a unique end hub while respecting zone capacity and connection capacity constraints.

The current implementation focuses on:
- strict input parsing and error reporting
- weighted pathfinding with support for normal, priority, and restricted zones
- turn-based simulation with simultaneous drone movement
- capacity-aware scheduling across multiple candidate paths

## Instructions

### Install

No third-party dependencies are required for the mandatory part.

### Run

Use the main entry point with a map file:

- python3 main.py maps/easy/01_linear_path.txt

### Debug

Run the program with the Python debugger:

- python3 -m pdb main.py maps/easy/01_linear_path.txt

### Lint

The project is checked with:

- flake8 .
- mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

## Algorithm choices

The solver uses three main steps:

1. Parse and validate the map file.
2. Build an undirected graph of zones and connections.
3. Compute several candidate paths, then assign drones to the best paths by balancing path cost and path capacity.

During simulation, each turn:
- drones already in restricted transit arrive first
- drones closer to the end move before drones farther back
- zone capacity and connection capacity are checked before every move
- restricted-zone movement is split across two turns

This approach is intentionally simple, deterministic, and type-safe. It is not a full multi-agent optimizer, but it is stable on the provided maps and produces valid turn-by-turn output.

## Visual representation

The current terminal output shows every turn as a space-separated list of drone movements. This gives a compact step-by-step view of the simulation and makes it easy to follow drone progress through the network.

A future graphical view or colorized terminal rendering could be added on top of the same simulation core without changing the routing logic.

## Resources

- Python documentation: https://docs.python.org/3/
- `dataclasses`: https://docs.python.org/3/library/dataclasses.html
- `heapq`: https://docs.python.org/3/library/heapq.html
- Flake8: https://flake8.pycqa.org/
- mypy: https://mypy.readthedocs.io/
- Dijkstra’s algorithm overview: https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm

### AI usage

AI was used to:
- review the project structure
- identify missing pieces in the parser, graph helper, and simulation engine
- help design the turn-based scheduling strategy
- help clean up type hints, lint issues, and CLI wiring

The implemented code was reviewed and adjusted manually to match the project rules and the provided maps.
