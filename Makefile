SOURCES = setup.py async_lru.py tests

test: lint
	pytest tests


lint: black flake8 mypy


mypy:
	#mypy --strict --show-error-codes .


black:
	isort -c .
	black --check .

flake8:
	flake8


fmt:
	isort .
	black .
