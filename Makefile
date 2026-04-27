.PHONY: install run test lint security docs clean

install:
	pip install -r requirements-dev.txt

run:
	python run.py

test:
	pytest

lint:
	black --check .
	isort --check-only .
	flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203
	mypy app/

format:
	black .
	isort .

security:
	bandit -r app/

docs:
	sphinx-build -b html docs/ docs/_build/html

docs-serve: docs
	python -m http.server 8080 --directory docs/_build/html

clean:
	rm -rf docs/_build .pytest_cache .mypy_cache htmlcov coverage.xml .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
