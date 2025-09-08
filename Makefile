PYPROJECT=pyproject.toml

.PHONY: venv lint test pre-commit-install

venv:
	poetry install

lint:
	poetry run ruff check .
	poetry run black --check .
	poetry run mypy .

test:
	poetry run pytest -q

pre-commit-install:
	poetry run pre-commit install
