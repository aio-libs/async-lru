SOURCES = setup.py async_lru.py tests

test: lint
	pytest tests


lint: black flake8 mypy


mypy:
	mypy --strict --show-error-codes async_lru.py tests


black:
	isort -c $(SOURCES)
	black --check $(SOURCES)

flake8:
	flake8 $(SOURCES)


fmt:
	isort $(SOURCES)
	black $(SOURCES)
