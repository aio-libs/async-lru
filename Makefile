SOURCES = setup.py async_lru.py tests

test: lint test-only

test-only:
	pytest tests


lint: black flake8 mypy


mypy:
	mypy


black:
	isort -c .
	black --check .

flake8:
	flake8


fmt:
	isort .
	black .
