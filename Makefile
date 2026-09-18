.PHONY: install run debug clean lint lint-strict test

install:
	uv sync

run:
	uv run python3 a_maze_ing.py config.txt


# debug with pdb for example
debug:

clean:
	rm -rf __pychache__ mypy_cache .pytest_cache # .uv .venv

lint:
	flake8 .
	mypy . --warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict





# optional commands
# run tests with pytest with coverage
test:
	uv run pytest

