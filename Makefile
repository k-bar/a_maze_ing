MAIN_SCRIPT = a_maze_ing.py
CONFIG_FILE = config.txt
APP = app/
MAZEGEN = mazegen/
TESTS = tests/
SOURCES = $(MAIN_SCRIPT) $(MAZEGEN) $(APP)
#$(TESTS)

.PHONY: all  build install run debug clean lint lint-strict test test-cov

all: install run

build:
	uv build --wheel --out-dir .

install:
	@echo "preparing virtual environment and install mazegen as editable package..."
	uv venv
	uv pip install -e .

run:
	@echo "Running the maze project... (syncs dependencies if needed)"
	uv run python3 $(MAIN_SCRIPT) $(CONFIG_FILE)

debug:
	uv run python3 -m pdb $(MAIN_SCRIPT) $(CONFIG_FILE)

clean:
	@echo "Cleaning cache file"
	rm -rf __pycache__
	rm -rf mypy_cache .pytest_cache .uv .venv

lint:
	@echo "Running flake8 static checks..."
	uv run flake8 $(SOURCES)
	@echo "Running mypy static checks..."
	uv run mypy $(SOURCES) --warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	@echo "Running flake8 static checks..."
	uv run flake8 $(SOURCES)
	@echo "Running strict linting"
	uv run mypy $(SOURCES) --strict


test:
	uv run pytest $(TESTS)

test-cov:
	uv run pytest --cov=app --cov=mazegen $(TESTS)
