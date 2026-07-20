DEFAULT_MAP := maps/challenger/01_the_impossible_dream.txt
PYTHON := python3
MAP ?= $(if $(map),$(map),$(DEFAULT_MAP))

help:
	@echo "Usage: make [target] [map=path/to/map.txt]"
	@echo "Targets:"
	@echo "  install      Install dependencies (flake8, mypy)"
	@echo "  run          Run the program with the specified map"
	@echo "  debug        Run the program in debug mode with the specified map"
	@echo "  clean        Clean up temporary files and caches"
	@echo "  lint         Run flake8 and mypy for code quality checks"
	@echo "  lint-strict  Run flake8 and mypy with strict settings"
	@echo "  help         Show this help message"


install:
	pip install flake8 mypy

run:
	$(PYTHON) main.py $(MAP)

debug:
	$(PYTHON) -m pdb main.py $(MAP)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete


lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy main.py parser.py reading.py simulation.py drone_graph.py enums.py errors.py utils.py tests --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy main.py parser.py reading.py simulation.py drone_graph.py enums.py errors.py utils.py tests --strict


.PHONY: install run debug clean lint lint-strict help
