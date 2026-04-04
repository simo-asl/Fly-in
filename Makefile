NAME = fly-in

PYTHON = python3

SRC = main.py

.PHONY: run clean fclean re lint type test

run:
	$(PYTHON) $(SRC)

lint:
	flake8 src tests main.py

type:
	mypy src

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

fclean: clean
	rm -rf .mypy_cache .pytest_cache

re: fclean
