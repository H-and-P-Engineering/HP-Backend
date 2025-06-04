.PHONY: install
install:
	uv pip install -e ".[dev]"
	pre-commit install

.PHONY: migrations
migrations:
	uv run manage.py makemigrations

.PHONY: migrate
migrate:
	uv run manage.py migrate

.PHONY: superuser
superuser:
	uv run manage.py createsuperuser

.PHONY: run
run:
	uv run manage.py runserver

.PHONY: test
test:
	pytest

.PHONY: test-coverage
test-coverage:
	pytest --cov=. --cov-report=html

.PHONY: lint
lint:
	uv tool run ruff check .
	uv tool run ruff format --check .

.PHONY: format
format:
	uv tool run ruff check --fix .
	uv tool run ruff format .

.PHONY: clean
clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	find . -name ".pytest_cache" -delete
	find . -name ".coverage" -delete
	find . -name "htmlcov" -delete

.PHONY: shell
shell:
	uv run manage.py shell_plus --ipython

.PHONY: check
check:
	uv run manage.py check
