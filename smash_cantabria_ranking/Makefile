.PHONY: venv install lint format type test run

venv:
    python3 -m venv .venv

install:
    . .venv/bin/activate && pip install -U pip && pip install -e ".[dev]"

lint:
    . .venv/bin/activate && ruff src tests

format:
    . .venv/bin/activate && black src tests

type:
    . .venv/bin/activate && mypy src

test:
    . .venv/bin/activate && pytest -q

run:
    . .venv/bin/activate && python -m smash_ranking.ranking --help