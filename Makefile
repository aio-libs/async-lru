# Some simple testing tasks (sorry, UNIX only).

.PHONY: init setup
init setup:
	pip install -r requirements-dev.txt
	pre-commit install

.PHONY: fmt
fmt:
	python -m pre_commit run --all-files --show-diff-on-failure

.PHONY: lint
lint: fmt
	mypy

.PHONY: test
test:
	pytest -s ./tests/
