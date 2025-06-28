.PHONY: help install install-dev test test-cov lint format clean build upload

help:
	@echo "Available commands:"
	@echo "  make install      Install project dependencies"
	@echo "  make install-dev  Install development dependencies"
	@echo "  make test         Run tests"
	@echo "  make test-cov     Run tests with coverage"
	@echo "  make lint         Run linters (flake8, mypy)"
	@echo "  make format       Format code with black and isort"
	@echo "  make clean        Remove build artifacts"
	@echo "  make build        Build distribution packages"
	@echo "  make upload       Upload to PyPI (requires credentials)"

install:
	pip install -e .

install-dev:
	pip install -r dev-requirements.txt
	pip install -e .

test:
	pytest

test-cov:
	pytest --cov=src --cov-report=term-missing --cov-report=html

lint:
	flake8 src tests
	mypy src
	ruff check src tests

format:
	black src tests
	isort src tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

upload: build
	python -m twine upload dist/*