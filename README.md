*This project has been created as part of the 42 curriculum by
simo-asl.*

# Fly-in

## Description

Fly-in is a Python 3.10+ drone routing simulator that moves multiple
drones through a network of connected zones while minimizing the total
number of simulation turns.

The objective is to design an efficient routing system that guides
drones from a unique start hub to a unique end hub while respecting
movement constraints, zone capacities, and connection limits.

The project focuses on:

-   Graph algorithms and pathfinding
-   Object-oriented programming
-   Input parsing and validation
-   Turn-based simulation
-   Algorithm optimization

## Features

### Map Parser

The parser reads and validates map files containing:

-   Number of drones
-   Start and end zones
-   Zones and their metadata
-   Connections between zones
-   Zone capacities
-   Connection capacities

Supported zone types:

-   normal: standard movement cost
-   restricted: requires additional movement time
-   priority: preferred during route selection
-   blocked: inaccessible zone

### Routing System

The routing system handles:

-   Multiple candidate paths
-   Weighted path selection
-   Drone distribution
-   Capacity-aware scheduling
-   Simultaneous movements

### Simulation Engine

The simulation works turn by turn and ensures:

-   Valid drone movements
-   Zone occupancy rules
-   Connection capacity limits
-   Restricted zone movement rules
-   Correct delivery tracking

## Architecture

The project is divided into several components:

### Parser

Responsible for:

-   Reading input files
-   Validating syntax
-   Extracting zone and connection data
-   Handling parsing errors

### Drone Graph

Responsible for:

-   Representing the map as a graph
-   Managing zones and connections
-   Storing routing information

### Simulation Engine

Responsible for:

-   Managing drone states
-   Scheduling movements
-   Applying constraints
-   Producing simulation output

## Algorithm Choices

The solution uses graph-based pathfinding to find efficient routes
between the start and end zones.

The algorithm process:

1.  Parse the map and build an internal graph.
2.  Evaluate possible paths while avoiding blocked zones.
3.  Consider movement costs and capacity constraints.
4.  Assign drones to suitable paths.
5.  Simulate movements turn by turn.

The implementation avoids external graph libraries and manages the graph
logic internally.

## Visual Representation

The simulation provides terminal output showing drone movements for each
turn.

Example:

``` text
D1-roof1 D2-corridorA
D1-roof2 D2-tunnelB
D1-goal D2-goal
```

This allows users to follow the progress of every drone during the
simulation.

## Instructions

### Requirements

-   Python 3.10 or later
-   flake8
-   mypy

### Run

``` bash
python3 main.py maps/easy/01_linear_path.txt
```

### Debug

``` bash
python3 -m pdb main.py maps/easy/01_linear_path.txt
```

### Lint

``` bash
flake8 .

mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```

## Example

Input:

``` text
nb_drones: 2

start_hub: hub 0 0
end_hub: goal 10 10

hub: roof1 3 4
hub: roof2 6 2

connection: hub-roof1
connection: roof1-roof2
connection: roof2-goal
```

Output:

``` text
D1-roof1 D2-roof1
D1-roof2 D2-roof2
D1-goal D2-goal
```

## Testing

The project includes tests for:

-   Parser validation
-   Graph behavior
-   Simulation rules

Tests are used to verify edge cases and ensure the simulator respects
all constraints.

## Resources

-   Python Documentation: https://docs.python.org/3/

-   Dataclasses: https://docs.python.org/3/library/dataclasses.html

-   Heap Queue: https://docs.python.org/3/library/heapq.html

-   Dijkstra Algorithm:
    https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm

## AI Usage

AI tools were used to assist with:

-   Reviewing project structure
-   Improving documentation
-   Identifying possible edge cases
-   Reviewing code organization
-   Helping with README improvements

All AI-generated suggestions were reviewed, tested, and adapted manually
to ensure correctness.

## Conclusion

Fly-in combines graph algorithms, simulation design, and software
engineering practices to create an efficient drone routing system
capable of handling complex movement constraints.